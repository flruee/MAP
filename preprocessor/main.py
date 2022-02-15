from asyncore import write
import json
import logging
from kafka import KafkaConsumer, ConsumerRebalanceListener


#class Listener(ConsumerRebalanceListener)
def handle_event(data,*args, **kwargs):
    print(data)
    print()
    print(args)
    print()
    print(kwargs)
    print()
    exit()
if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    kafka_config = config["kafka"]
    preprocessor_config = config["preprocessor"]

    logging.basicConfig(filename='preprocessor.log', level=preprocessor_config["logLevel"])
    
    consumer = KafkaConsumer(
        bootstrap_servers=kafka_config["bootstrap_servers"],
    )

    # To consume latest messages and auto-commit offsets
    consumer = KafkaConsumer(kafka_config["topic"],
                            bootstrap_servers=kafka_config["bootstrap_servers"])
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print("topic")
        print(message.topic)
        print()
        print("partition")
        print(message.partition)
        print()
        print("offset")
        print(message.offset)
        print()
        print("kex")
        print(message.key)
        print()
        print("value")
        data = json.loads(message.value)
        print(data)
        with open(f"block_data/{data['number']}.json", "w+") as f:
            f.write(json.dumps(data,indent=4))
        #print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                    message.offset, message.key,
        #                                    message.value))

