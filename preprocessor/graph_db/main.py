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
transaction_list = range(328745,1328745)
#transaction_list = [5499975] # free floating balance node
#transaction_list = [5499979]
#transaction_list = [7499977]
#transaction_list = [330907]
counter = 0
average_time = 0

with Session(pg_driver) as session:
    subgraphs = []
    start = time.time()
    for i in transaction_list:
        print(i)
        if counter == 100000:
            counter = 0
            average_time = average_time / 100000
            print(average_time)
            average_time = 0
            subgraph = subgraphs[0]
            for sub in subgraphs[1:]:
                subgraph = Utils.merge_subgraph(subgraph, sub)
            tx = Driver().get_driver().graph.begin()
            tx.create(subgraph)
            Driver().get_driver().graph.commit(tx)
            exit()
            subgraphs = []
        counter += 1
        stmt = select(RawData).where(RawData.block_number == i)
        db_data = session.execute(stmt).fetchone()[0]
        subgraph = block_handler.handle_full_block(db_data.data)
        subgraphs.append(subgraph)
        end = time.time()
        average_time += end - start
    print(end - start)


