import time
import json
import logging
from kafka import KafkaConsumer
from mongoengine import connect
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models.models import Account
DB = "postgres"
MODE = "kafka"
if DB == "postgres":
	from src.insertions_pg import PGBlockHandler
else:
	from src.insertions import handle_blocks
from src.queries.schema import schema
import logging




if __name__ == "__main__":
    #TODO: crrrreate logging object
    logging.basicConfig(filename='db.log', level=logging.INFO,format='%(asctime)s,%(levelname)s :%(message)s')

    if DB == "postgres":
        engine = create_engine('postgresql://mapUser:mapmap@localhost/map')
        with Session(engine) as session:
            logging.info("hi")
            block_handler = PGBlockHandler(session)
            start = time.time()
            if MODE == "json":
                block_handler.handle_blocks(0, 10000)
            elif MODE == "node": 
                block_handler.handle_node_connection_blocks(4710599,4710599+100)
            elif MODE == "kafka":
                logging.info("2")
                with open("config.json","r") as f:
                    config = json.loads(f.read())

                kafka_config = config["kafka"]
                preprocessor_config = config["preprocessor"]

                logging.basicConfig(filename='preprocessor.log', level=preprocessor_config["logLevel"])
                print("before kafka")
                # To consume latest messages and auto-commit offsets
                consumer = KafkaConsumer(
                        kafka_config["topic"],
                        auto_offset_reset="earliest",
                        bootstrap_servers=kafka_config["bootstrap_servers"]
                )
                print("waiting")
                for message in consumer:
                    # message value and key are raw bytes -- decode if necessary!
                    # e.g., for unicode: `message.value.decode('utf-8')`
                    print(message)
                    block_number = message.key.decode("utf-8").replace("b","")
                    print(f"received block {message.key.decode('utf-8')}")
                    data = json.loads(message.value)
                    #with open(f"block_data/{data['number']}.json", "w+") as f:
                    #    f.write(json.dumps(data,indent=4))
                    block_handler.handle_full_block(data)


                


    else:
        print("noooooo")
        db_connection = connect("example", host="mongodb://127.0.0.1:27017/map", alias="default")
        start = time.time()
        #handle_blocks(3182856, 3182857)
        handle_blocks(4710599, 4721600)
        end = time.time()
        #handle_blocks(4714883,4714884)
        print(end-start)
        query = """
            {
            transfer{
            value,
            toAddress,
            type
            }
            }
        """
        result = schema.execute(query)
        print(result)
        #result = Account.objects.get(address="12vT2aGAtnqBHopieTcj7ETpsLm9YkXkcK41BAjFcfwxabHJ")
    

