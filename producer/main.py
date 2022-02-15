import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer

def string_replacer(data):
    return data.replace("'",'"').replace("(","[").replace(")","]").replace("None","null")


def handle_block_data(block_dict, kafka=True):
    if kafka:
        producer.send(kafka_config["topic"],value=block_dict)

    if producer_config["logLevel"] <= 10:
        with open("block.json", "w+") as f:
            f.write(json.dumps(block_dict, indent=4))


def jsonize_header(obj):
    """
    The header is encoded in rust like syntax, and there seems to be no serialization method.
    Each log is wrapped with '<scale_info::13(value={RELEVANT_DATA}>', which python and JSON can't handle.
    Furthermore the data is wrapped in normal brackets instead of square brackets which violates JSON.
    """
    logs = obj["header"]["digest"]["logs"]
    for i in range(len(logs)):
        mod_log = str(logs[i])
        mod_log = string_replacer(mod_log)
        
        obj["header"]["digest"]["logs"][i] = json.loads(mod_log)
    return obj

def jsonize_extrinsic(block_hash):
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

def jsonize_events(block_hash):
    events = substrate.get_events(block_hash)
    events_jsonized = []
    count = 0
    for event in events:
        event_jsonized = str(event)
        event_jsonized = string_replacer(event_jsonized)
        
        try:
            json.dumps(event_jsonized, indent=4)
            events_jsonized.append(json.loads(event_jsonized))
        except TypeError or json.decoder.JSONDecoder:
            logging.error(f"Error {e} in block {block_hash}. JSON serialization failed for event #{count}")
            logging.debug(f"Event content:\n{event_jsonized}")

        count+=1

    return events_jsonized
        

def subscription_handler(obj, update_nr, subscription_id):

    logging.info(f"New block #{obj['header']['number']} produced by {obj['author']}")

    block_number = obj["header"]["number"]
    block_hash = substrate.get_block_hash(block_number)
    header = jsonize_header(obj)
    extrinsics = jsonize_extrinsic(block_hash)
    events = jsonize_events(block_hash)
    #setup json dict
    block_dict = {
        "number": block_number,
        "hash": block_hash,
        "header": header,
        "extrinsics": extrinsics,
        "events": events
    }

    handle_block_data(block_dict)
    if producer_config["one_block"]:
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

    producer = KafkaProducer(
        bootstrap_servers=kafka_config["bootstrap_servers"],
        max_request_size=317344026,
        value_serializer=lambda x: 
            json.dumps(x).encode('utf-8')
    )

    result = substrate.subscribe_block_headers(subscription_handler, include_author=True, finalized_only=True)
