from dotenv import load_dotenv, find_dotenv

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import Neo4jError
from py2neo.ogm import Repository
#from py2neo import Graph
from src.inserter import Neo4jBlockHandler
from src.models import RawData
from src.driver_singleton import Driver
import time
import json
import logging
#from kafka import KafkaConsumer
#from sqlalchemy import create_engine, select
#from sqlalchemy.orm import Session
#from src import RawData
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import logging
import os
import ast


load_dotenv(find_dotenv())

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


DATABASE_USERNAME = env('DATABASE_USERNAME')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
DATABASE_URL = env('DATABASE_URL')


driver = Repository(DATABASE_URL, auth=(DATABASE_USERNAME, str(DATABASE_PASSWORD)))
#driver.graph.schema.create_index("Account", "address")
#driver.graph.schema.drop_index("Account", "address")
#driver.graph.schema.drop_uniqueness_constraint("Account", "address")
#driver.graph.schema.create_uniqueness_constraint("Account", "address")
driver_singleton = Driver()
driver_singleton.add_driver(driver)
pg_driver = create_engine('postgresql://postgres:polkamap@172.23.149.214/raw_data')
block_handler = Neo4jBlockHandler(driver)
transaction_list = range(5000000,10000000)
#transaction_list = [5000000]
counter = 0
average_time = 0

with Session(pg_driver) as session:
    for i in transaction_list:
        print(i)
        stmt = select(RawData).where(RawData.block_number == i)
        db_data = session.execute(stmt).fetchone()[0]
        block_handler.handle_full_block(db_data.data)

"""while True:
    counter += 1
    if counter == 5:
        counter = 0
        average_time = average_time/1000
        print(average_time)
        average_time = 0
    start = time.time()

    end = time.time()
    average_time += end - start"""


