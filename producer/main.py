import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer

def handle_block_data(block_dict):
    producer.send(kafka_config["topic"],value=block_dict)


def subscription_handler(obj, update_nr, subscription_id):

    logging.info(f"New block #{obj['header']['number']} produced by {obj['author']}")

    block_number = obj["header"]["number"]
    block_hash = substrate.get_block_hash(block_number)
    block = substrate.get_block(block_hash)
    
    #setup json dict
    block_dict = {
        "number": block_number,
        "hash": block_hash,
        "extrinsics": []
    }

    count = 0
    #iterate through extrinsics and serialize them
    for extrinsic in block["extrinsics"]:
        
        try:
            #Check if json serialization works
            json.dumps(extrinsic.value_serialized, indent=4)
            block_dict["extrinsics"].append(extrinsic.value_serialized) 
            logging.info("all good?")
        except Exception as e:
            count+=1
            logging.error(f"Error {e} in block {block_number}. JSON serialization failed for extrinsic #{count}")
            logging.debug(f"Extrinsic content:\n{extrinsic.value_serialized}")

    #do something with the json
    #try:
    handle_block_data(block_dict)
    #    logging.info(f"Block #{block_number} successfully handled")
    #except Exception as e:
    #    logging.error(f"Error {e} in block {block_number}. JSON serialization failed")



    #cancel subscription    
    return {'message': 'Subscription will cancel when a value is returned', 'updates_processed': update_nr}


if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    polkadot_config = config["node"]
    kafka_config = config["kafka"]
    producer_config = config["producer"]

    logging.basicConfig(filename='producer.log', level=producer_config["logLevel"])
    
    substrate = SubstrateInterface(
        url=polkadot_config["url"],
        ss58_format=polkadot_config["ss58_format"],
        type_registry_preset=polkadot_config["type_registry_preset"]
    )

    producer = KafkaProducer(bootstrap_servers=kafka_config["bootstrap_servers"],
                         value_serializer=lambda x: 
                            json.dumps(x).encode('utf-8'))

    result = substrate.subscribe_block_headers(subscription_handler, include_author=True, finalized_only=True)
