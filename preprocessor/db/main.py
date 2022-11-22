from dotenv import load_dotenv, find_dotenv
import os
import ast
import time
import json
import logging
from kafka import KafkaConsumer
from mongoengine import connect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.insertions_pg import PGBlockHandler

from src.queries.schema import schema
import logging
import traceback
from src.pg_models.raw_data import RawData

load_dotenv(find_dotenv())


from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging
from logging.handlers import RotatingFileHandler

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    context._query_start_time = time.time()
    logger.debug("Start Query:\n%s" % statement)
    # Modification for StackOverflow answer:
    # Show parameters, which might be too verbose, depending on usage..
    logger.debug("Parameters:\n%r" % (parameters,))


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    total = time.time() - context._query_start_time
    logger.debug("Query Complete!")

    # Modification for StackOverflow: times in milliseconds
    logger.debug("Total Time: %.02fms" % (total*1000))

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
DATABASE_NAME = env("DATABASE_NAME")
RAW_DATA_DATABASE_NAME = env("RAW_DATA_DATABASE_NAME")
MODE = env("MODE")

if __name__ == "__main__":
    # Logging
    handler = RotatingFileHandler("db.log", maxBytes=1024 ** 3, backupCount=2)

    logging.basicConfig(level=logging.DEBUG, handlers=[handler],
                            format='%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logger = logging.getLogger("sqlalchemy.engine")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Get db connections
    engine = create_engine(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}')
    raw_data_engine = create_engine(f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{RAW_DATA_DATABASE_NAME}")
    

    with Session(engine) as session:
        driver = Driver()
        driver.add_driver(session)
        
        # Store session in a Singleton class for easy access elsewhere
        block_handler = PGBlockHandler(session)

        # Get data directly from node, useful for debugging
        if MODE == "node": 
            start = time.perf_counter()
            blocks = [9556966]
            block_handler.handle_node_connection_blocks(blocks) #1411
            print(f"Took {time.perf_counter() - start}")

        # Get data from raw_data database
        elif MODE == "db":
            with Session(raw_data_engine) as raw_data_session:
                for i in range(6955431,11000000):
                    data =raw_data_session.query(RawData.data).filter(RawData.block_number==i).first()[0]
                    block_handler.handle_full_block(data)
                    session.commit()

        # Get data from kafka
        elif MODE == "kafka":
            with open("config.json","r") as f:
                config = json.loads(f.read())

            kafka_config = config["kafka"]
            preprocessor_config = config["preprocessor"]

            # To consume latest messages and auto-commit offsets
            consumer = KafkaConsumer(
                    kafka_config["topic"],
                    auto_offset_reset="earliest",
                    bootstrap_servers=kafka_config["bootstrap_servers"],
                    group_id="grp3",
                    max_poll_records=1
            )
            for message in consumer:
                # message value and key are raw bytes -- decode if necessary!
                # e.g., for unicode: `message.value.decode('utf-8')`
                block_number = message.key.decode("utf-8").replace("b","")
                print(f"received block {message.key.decode('utf-8')}")
                data = json.loads(message.value)
  
                # Check if block was already handled
                stmt = select(Block).where(Block.block_number==data["number"])
                db_data = session.execute(stmt).fetchone()

                if db_data is None:
                    try:
                        with session.begin():
                            block_handler.handle_full_block(data)
                    except Exception:
                        print(data["number"])
                        traceback.print_exc()
                        exit()

                

