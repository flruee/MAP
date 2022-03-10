import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer
import ssl
import sys
import os

def handle_blocks(from_block: int, to_block:int):

    for block_number in range(from_block, to_block+1):
        block = substrate.get_block_header(block_number=block_number, include_author=True)
        handle_block(block)
        print(f"saved block #{block['header']['number']}")

def handle_block(block):
    #handle genesis block
    if block["header"]["number"] == 0:
        block["author"] = None
        
    #logging.info(f"New block #{block['header']['number']} produced by {block['author']}")
    
    block_number = block["header"]["number"]
    block_hash = substrate.get_block_hash(block_number)
    header = jsonize_header(block)
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

def string_replacer(data):
    return data.replace("'",'"').replace("(","[").replace(")","]").replace("None","null")

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w+')

def handle_block_data(block_dict, kafka=True):
    with safe_open_w(f"blocks/{block_dict['number']}.json") as f:
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
        



if __name__ == "__main__":
    from_block = int(sys.argv[1])
    to_block = int(sys.argv[2])

    with open("config.json","r") as f:
        config = json.loads(f.read())

    polkadot_config = config["node"]
    kafka_config = config["kafka"]
    producer_config = config["producer"]

    logging.basicConfig(filename='block_data.log', level=producer_config["logLevel"])
    #logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    #needed for self signed certificate
    sslopt = {
        "sslopt": {
            "cert_reqs": ssl.CERT_NONE
            }
    }

    substrate = SubstrateInterface(
        url=polkadot_config["url"],
        ss58_format=polkadot_config["ss58_format"],
        type_registry_preset=polkadot_config["type_registry_preset"],
        
        ws_options=sslopt
    )


    handle_blocks(from_block, to_block)
