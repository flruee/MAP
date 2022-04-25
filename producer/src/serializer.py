



import logging
import json
from xml.etree.ElementInclude import include


class Serializer:
    def __init__(self, kafka_producer, substrate, producer_config, node_config, kafka_config):
        self.producer = kafka_producer
        self.substrate =substrate
        self.producer_config = producer_config
        self.node_config = node_config
        self.kafka_config = kafka_config

    def string_replacer(self,data):
        return data.replace("'",'"').replace("(","[").replace(")","]").replace("None","null").replace("True", "true").replace("False", "false")


    def handle_block_data(self,block_dict, kafka=True):
        key = bytes(str(block_dict["number"]),"utf-8")
        print(block_dict)
        if kafka:
            self.producer.send(self.kafka_config["topic"],value=block_dict, key=key)

        if self.producer_config["logLevel"] <= 10:
            with open("block.json", "w+") as f:
                f.write(json.dumps(block_dict, indent=4))


    def jsonize_header(self,obj):
        """
        The header is encoded in rust like syntax, and there seems to be no serialization method.
        Each log is wrapped with '<scale_info::13(value={RELEVANT_DATA}>', which python and JSON can't handle.
        Furthermore the data is wrapped in normal brackets instead of square brackets which violates JSON.
        """
        logs = obj["header"]["digest"]["logs"]
        print(len(logs))
        for i in range(len(logs)):
            print(i)
            mod_log = str(logs[i])
            mod_log = self.string_replacer(mod_log)
            
            obj["header"]["digest"]["logs"][i] = json.loads(mod_log)
        return obj

    def jsonize_extrinsic(self,block_hash):
        """
        The extrinsic part is implemented via classes and not dicts
        Fortunately a serialization method is available.
        """

        block = self.substrate.get_block(block_hash)
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

    def jsonize_events(self,block_hash):
        events = self.substrate.get_events(block_hash)
        events_jsonized = []
        count = 0
        for event in events:
            event_jsonized = str(event)
            event_jsonized = self.string_replacer(event_jsonized)
            
            try:
                old_string = event_jsonized#json.dumps(event_jsonized, indent=4)
                while True:
                    new_string = self.backslash_escaper(old_string)
                    if new_string == old_string:
                        break
                    else:
                        old_string = new_string
                
                json.dumps(new_string, indent=4)
                print(new_string)
                events_jsonized.append(json.loads(new_string))
            except Exception as e2:
                print(e2)
                logging.error(f"Error {e} in block {block_hash}. JSON serialization failed for event #{count}")
                logging.debug(f"Event content:\n{event_jsonized}")
            count+=1

        return events_jsonized
            

    def subscription_handler(self,obj, update_nr, subscription_id):

        logging.info(f"New block #{obj['header']['number']} produced by {obj['author']}")
        self.handle_one_block(obj)
        if self.producer_config["one_block"]:
            return {'message': 'Subscription will cancel when a value is returned', 'updates_processed': update_nr}

    def handle_one_block(self,obj):
        block_number = obj["header"]["number"]
        block_hash = self.substrate.get_block_hash(block_number)
        header = self.jsonize_header(obj)
        extrinsics = self.jsonize_extrinsic(block_hash)
        events = self.jsonize_events(block_hash)
        #setup json dict
        block_dict = {
            "number": block_number,
            "hash": block_hash,
            "header": header,
            "extrinsics": extrinsics,
            "events": events
        }

        self.handle_block_data(block_dict)



    def direct_block_handler(self,from_block, to_block):
        for block_number in range(from_block, to_block+1):
            print(block_number)
            header = self.substrate.get_block_header(block_number=block_number, include_author=True)
            self.handle_one_block(header)


    def backslash_escaper(self,string):
        """
        bad python encoding strikes again.
        Some hex values are interpreted as string and then contain \x00, which will throw if jsonized.
        This function transforms the bad string back to valid hex
        """
        backslash_index = None
        for i in range(len(string)):
            if string[i] == "\\":
                backslash_index = i
        if backslash_index is None:
            return string
        string_start = None
        string_end = None
        for i in range(backslash_index,0,-1):
            if string[i] == '"':
                string_start = i
                break
        for i in range(backslash_index, len(string)):
            if string[i] == '"':
                string_end = i
                break
        
        bad_string = string[string_start+1:string_end]
        print(bad_string)
        bad_count = bad_string.count("\\x00")
        string_without_null_char = bad_string.replace("\\x00", "")
        cleaned_hex = string_without_null_char.encode("utf-8").hex()
        print(cleaned_hex)
        print(bad_string)
        for i in range(bad_count):
            cleaned_hex+="00"
        cleaned_string = string.replace(bad_string, cleaned_hex)
        print(cleaned_string)
        return cleaned_string