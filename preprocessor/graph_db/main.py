import os
import ast
import json
from dotenv import load_dotenv, find_dotenv
from py2neo.ogm import Repository
from src.inserter import Neo4jBlockHandler
from src.models import RawData, Utils
from src.driver_singleton import Driver
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from os import listdir
from os.path import isfile, join


"""logging"""
"""
import logging
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler("graph.log", maxBytes=1024 ** 3, backupCount=2)

logging.basicConfig(level=logging.DEBUG, handlers=[handler],
                        format='%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
"""


def env(key, default=None, required=True):
    """
    Retrieves environment variables and returns Python natives. The (optional)
    default will be returned if the environment variable does not exist.
    """
    try:
        value = os.environ[key]
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value
    except KeyError:
        if default or not required:
            return default
        raise RuntimeError("Missing required environment variable '%s'" % key)



"""
Set config
"""
load_dotenv(find_dotenv())
DATABASE_USERNAME = env('DATABASE_USERNAME')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
DATABASE_URL = env('DATABASE_URL')
driver = Repository(DATABASE_URL, auth=(DATABASE_USERNAME, str(DATABASE_PASSWORD)))
driver_singleton = Driver()
driver_singleton.add_driver(driver)
pg_driver = create_engine('postgresql://postgres:polkamap@172.23.149.214/raw_data')
block_handler = Neo4jBlockHandler(driver)


"""
Set the block range you wish to handle.
"""
transaction_list = range(1750391,11328745)


with Session(pg_driver) as session:
    subgraphs = []
    counter = 0
    for i in transaction_list:
        print(i)
        if i == 0:
            print("We do not handle Genesis block")
            continue

        """
        Set counter to the batch_size you would like to handle. Experiment with various values to find your
        optimum.
        """
        if counter == 1:
            counter = 0
            subgraph = subgraphs[0]
            merge_counter = 0
            while len(subgraphs) and not len(subgraphs) == 1:
                subgraphs = Utils.merge(subgraphs)
                print(len(subgraphs))
            print('merge_done')
            tx = Driver().get_driver().graph.begin()
            tx.create(subgraphs[0])
            Driver().get_driver().graph.commit(tx)
            print("push done")
            subgraphs = []
        counter += 1
        stmt = select(RawData).where(RawData.block_number == i)
        db_data = session.execute(stmt).fetchone()[0]
        subgraph = block_handler.handle_full_block(db_data.data)
        subgraphs.append(subgraph)


