import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer

def handle_block_data(block_dict, kafka=True):
    if kafka:
        producer.send(kafka_config["topic"],value=block_dict,key=bytes(block_dict["number"]))

    if producer_config["logLevel"] <= 10:
        with open("block.json", "w+") as f:
            f.write(json.dumps(block_dict, indent=4))


def get_header(obj):
    """
    The header is encoded in rust like syntax, and there seems to be no serialization method.
    Each log is wrapped with '<scale_info::13(value={RELEVANT_DATA}>', which python and JSON can't handle.
    Furthermore the data is wrapped in normal brackets instead of square brackets which violates JSON.
    """
    logs = obj["header"]["digest"]["logs"]
    for i in range(len(logs)):
        mod_log = str(logs[i])
        mod_log = mod_log.replace("'",'"').replace("(","[").replace(")","]")
        
        obj["header"]["digest"]["logs"][i] = json.loads(mod_log)
    return obj

def get_extrinsic(block_hash):
    """
    The extrinsic part is implemented via classes and not dicts
    Fortunately a serialization method is available.
    """

    block = substrate.get_block(block_hash)
    count = 0
    #iterate through extrinsics and serialize them
    extrinsics = []
    for extrinsic in block["extrinsics"]:
        
        try:
            #Check if json serialization works
            json.dumps(extrinsic.value_serialized, indent=4)
            extrinsics.append(extrinsic.value_serialized) 
        except Exception as e:
            count+=1
            logging.error(f"Error {e} in block {block_hash}. JSON serialization failed for extrinsic #{count}")
            logging.debug(f"Extrinsic content:\n{extrinsic.value_serialized}")

    return extrinsics

def subscription_handler(obj, update_nr, subscription_id):

    logging.info(f"New block #{obj['header']['number']} produced by {obj['author']}")

    block_number = obj["header"]["number"]
    block_hash = substrate.get_block_hash(block_number)
    header = get_header(obj)
    extrinsics = get_extrinsic(block_hash)
    #setup json dict
    block_dict = {
        "number": block_number,
        "hash": block_hash,
        "header": header,
        "extrinsics": extrinsics
    }

    handle_block_data(block_dict)
 
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
