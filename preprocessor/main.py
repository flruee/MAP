import json
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from kafka import KafkaConsumer
import datetime


def filer(self):
    now = datetime.datetime.now()
    return self + now.strftime("%Y-%m-%d_%H:%M:%S")



if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    kafka_config = config["kafka"]
    preprocessor_config = config["preprocessor"]

    logging_filename = 'preprocessor.log'
    logger = logging.getLogger('preprocessor')
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    logging.basicConfig(filename=logging_filename, level=preprocessor_config["logLevel"])
    handler = RotatingFileHandler(logging_filename, maxBytes=1024**3, backupCount=2)
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)

    consumer = KafkaConsumer(
        bootstrap_servers=kafka_config["bootstrap_servers"],
    )

    # To consume latest messages and auto-commit offsets
    consumer = KafkaConsumer(kafka_config["topic"],
                            bootstrap_servers=kafka_config["bootstrap_servers"])
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print(message)
        exit()
        x = message.key.decode("utf-8").replace("b","")
        print(f"received block {message.key.decode('utf-8')}")
        data = json.loads(message.value)
        with open(f"block_data/{data['number']}.json", "w+") as f:
            f.write(json.dumps(data,indent=4))
        #print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                    message.offset, message.key,
        #                                    message.value))

