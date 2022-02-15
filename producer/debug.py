from substrateinterface import SubstrateInterface
import json
import logging

def jsonize_events(block_hash):
    events = substrate.get_events(block_hash)
    events_jsonized = []
    count = 0
    for event in events:
        print(event)
        event_jsonized = str(event)
        event_jsonized = event_jsonized.replace("'",'"').replace("(","[").replace(")","]").replace("None","null")
        print(event_jsonized[140:160])
        
        try:
            events_jsonized.append(json.loads(event_jsonized))
        except TypeError or json.decoder.JSONDecoder:
            logging.error(f"Error {e} in block {block_hash}. JSON serialization failed for event #{count}")
            logging.debug(f"Event content:\n{event_jsonized}")

        count+=1

    return events_jsonized



if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    polkadot_config = config["node"]
    producer_config = config["producer"]

    
    substrate = SubstrateInterface(
        url=polkadot_config["url"],
        ss58_format=polkadot_config["ss58_format"],
        type_registry_preset=polkadot_config["type_registry_preset"]
    )

    block_number = 9038808
    block_hash = substrate.get_block_hash(block_number)

    jsonize_events(block_hash)