from dotenv import load_dotenv, find_dotenv
from py2neo.ogm import Repository
from src.inserter import Neo4jBlockHandler
from src.models import RawData, Utils
from src.driver_singleton import Driver
import time
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import os
import ast
import logging


from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler("graph.log", maxBytes=1024 ** 3, backupCount=2)

logging.basicConfig(level=logging.DEBUG, handlers=[handler],
                        format='%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

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
transaction_list = range(1000000,11328745)
#transaction_list = [5499975] # free floating balance node
#transaction_list = [5499979]
#transaction_list = [7499977]


"""CREATE INDEX IF NOT EXISTS
FOR (n:Account)
ON (n.address)"""

"""Match (n:Account {address: '14bARWgpfEiURUS7sGGb54V6mvteRhYWDovcjnFMsLfxRxVV'}) return n;"""

#transaction_list = [330907]
# create first validatorpool for testing
with Session(pg_driver) as session:
    start = time.time()
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    account = Driver().get_driver().graph.run(
        "Match (n:Account {address: '" + '14bARWgpfEiURUS7sGGb54V6mvteRhYWDovcjnFMsLfxRxVV' + "'}) return n").evaluate()
    end = time.time()
    print(end-start)
    stmt = select(RawData).where(RawData.block_number == 328745)
    db_data = session.execute(stmt).fetchone()[0]
    subgraph = block_handler.handle_full_block(db_data.data)
    tx = Driver().get_driver().graph.begin()
    tx.create(subgraph)
    Driver().get_driver().graph.commit(tx)

counter = 0
average_time = 0

with Session(pg_driver) as session:
    subgraphs = []
    for i in transaction_list:
        start = time.time()
        print(i)
        if counter == 10000:
            counter = 0
            average_time = average_time / 1
            print(average_time)
            average_time = 0
            print(len(subgraphs))
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
        end = time.time()
        average_time += end - start
    print(end - start)


