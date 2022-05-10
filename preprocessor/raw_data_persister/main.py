import time
import json
import logging
from kafka import KafkaConsumer
from mongoengine import connect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src import RawData

import logging




if __name__ == "__main__":
    #TODO: crrrreate logging object
    logging.basicConfig(filename='rawDataPersister.log', level=logging.INFO,format='%(asctime)s,%(levelname)s :%(message)s')

    engine = create_engine('postgresql://mapUser:mapmap@localhost/raw_data')
    with Session(engine) as session:

        logging.info("2")
        with open("config.json","r") as f:
            config = json.loads(f.read())

        kafka_config = config["kafka"]
        preprocessor_config = config["preprocessor"]

        print("before kafka")
        # To consume latest messages and auto-commit offsets
        consumer = KafkaConsumer(
                kafka_config["topic"],
                auto_offset_reset="earliest",
                bootstrap_servers=kafka_config["bootstrap_servers"],
                group_id="rawDataPersister"
        )
        print("waiting")
        for message in consumer:
            # message value and key are raw bytes -- decode if necessary!
            # e.g., for unicode: `message.value.decode('utf-8')`
            print(message)
            block_number = message.key.decode("utf-8").replace("b","")
            print(f"received block {message.key.decode('utf-8')}")
            data = json.loads(message.value)
            
            #check if already in db
            stmt = select(RawData).where(RawData.block_number==data["number"])
            db_data = session.execute(stmt).fetchone()

            if db_data is None:
                raw_data = RawData(
                    block_number=data["number"],
                    data=data
                )
                session.add(raw_data)
                session.commit()


                
