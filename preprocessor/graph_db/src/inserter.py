import logging
from typing import List
import datetime
import json

from sqlalchemy import JSON
#from src.event_handlers.utils import event_error_handling
from src.models import Block,Extrinsic,Event
#from src.event_handlers_pg import SystemEventHandler, BalancesEventHandler, StakingEventHandler, ClaimsEventHandler
from sqlalchemy.exc import IntegrityError
#from src.node_connection import handle_one_block
from py2neo.ogm import Repository
class Neo4jBlockHandler:
    def __init__(self, driver: Repository):
        self.driver = driver

    def handle_full_block(self,data):
        
        block = self.__insert_block(data)
        extrinsics= self.__insert_extrinsics(data, block)
        events = self.__insert_events(data, extrinsics)
        self.__commit_all(block, extrinsics, events)
        

    def __insert_block(self,data):
        header = self.insert_header(data["header"])
        try:
            timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]

        except IndexError:
            timestamp = 1590507378000 - 6

        timestamp = datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=timestamp)
        
        last_block = Block.match(self.driver, data["number"]-1).first()

        block = Block(
            block_number=data["number"],
            hash=data["hash"],
            extrinsics_root = header["header"]["extrinsicsRoot"],
            parent_hash = header["header"]["parentHash"],
            state_root = header["header"]["stateRoot"],
            author = header["author"],
            timestamp=timestamp,
        )

        #Only a problem for the first block
        try:
            block.last_block.add(last_block)
        except TypeError:
            pass

        return block

    def insert_header(self,header_data):
        """
        Removes unnecessary fields from header data, then creates a Header object, stores it and returns it 
        """
        header_data["header"].pop("number")
        header_data["header"].pop("hash")

        return header_data

    def __insert_extrinsics(self, data, block: Block):

        extrinsics = []
        if len(data['extrinsics']) == 1 and len(data["events"]) > 2: # Todo: handle differently,
            """
            This was done because some blocks contain 0 extrinsics, 
            however they contain events that require handling
            """
            start = 0
            logging.warning(f"strange block {data['number']}")
        else:
            start = 1
        for i in range(start, len(data["extrinsics"])):
            """
            #index 0 is reserved for the timestamp transaction in extrinsics.
            
            if i in 0:
                timestamp = extrinsic_data["call"]["call_args"][0]["value"]
                print(timestamp)
                continue
            
            #index 1 is for paraInherents which probably have to be handled differently
            if i == 1:
                continue
            """
            #TODO make a parainherent check here
            extrinsic_data = data["extrinsics"][i]
            # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
            # timestamp is already handled above


            # if no era create an empty list
            if not "era" in extrinsic_data.keys():
                extrinsic_data["era"] = [-2]
            # change immortal transactions "00" to -1
            if extrinsic_data["era"] == "00":
                extrinsic_data["era"] = [-1]

            for key in ["address", "signature", "nonce", "tip"]:
                if not key in extrinsic_data.keys():
                    extrinsic_data[key] = None
            extrinsic = Extrinsic(
                extrinsic_hash = extrinsic_data["extrinsic_hash"],
                extrinsic_length = extrinsic_data["extrinsic_length"],
                signature = extrinsic_data["signature"],
                era = extrinsic_data["era"],
                nonce = extrinsic_data["nonce"],
                module_name = extrinsic_data["call"]["call_module"],
                function_name = extrinsic_data["call"]["call_function"],

            
            )

            block.has_extrinsics.add(extrinsic)

            extrinsics.append(extrinsic)
        return extrinsics

    def __insert_events(self, data,extrinsics:List[Extrinsic]):
        events = []
        for extrinsic_idx in range(len(extrinsics)):
            current_events = []
            order_id = 0
            extrinsic = extrinsics[extrinsic_idx]
            for event_data in data["events"]:
                if extrinsic_idx == 0:
                    extrinsic_idx = None
                if event_data["extrinsic_idx"] == extrinsic_idx:
                    event_data.pop("event")
        
                    event_data.pop("event_index")

                    event = Event(
                        phase = event_data["phase"],
                        module_name =  event_data["module_id"],
                        event_name =  event_data["event_id"],
                        attributes = json.dumps(event_data["attributes"]),
                        topics = event_data["topics"]
                
                    )
                    extrinsic.has_events.add(event)
                    if order_id > 0:
                        event.event_before.add(current_events[-1])
                    current_events.append(event)

                    order_id += 1
            
            events+=current_events
                    


        return current_events
    def __commit_all(self, block, extrinsics, events):
        #self.driver.save(extrinsics)
        for event in events:
            self.driver.save(event)
        for extrinsic in extrinsics:
            self.driver.save(extrinsic)
        self.driver.save(block)
    def handle_extrinsics_and_events(self,block,data) -> List[Extrinsic]:
        events_data = data["events"]

        extrinsics = []


        if len(data['extrinsics']) == 1 and len(events_data) > 2: # Todo: handle differently,
            """
            This was done because some blocks contain 0 extrinsics, 
            however they contain events that require handling
            """
            start = 0
            logging.warning(f"strange block {data['number']}")
        else:
            start = 1
        for i in range(start, len(data["extrinsics"])):
            """
            #index 0 is reserved for the timestamp transaction in extrinsics.
            
            if i in 0:
                timestamp = extrinsic_data["call"]["call_args"][0]["value"]
                print(timestamp)
                continue
            
            #index 1 is for paraInherents which probably have to be handled differently
            if i == 1:
                continue
            """
            #TODO make a parainherent check here
            extrinsic_data = data["extrinsics"][i]
            # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
            # timestamp is already handled above


            # if no era create an empty list
            if not "era" in extrinsic_data.keys():
                extrinsic_data["era"] = [None]
            # change immortal transactions "00" to -1
            if extrinsic_data["era"] == "00":
                extrinsic_data["era"] = [-1]

            for key in ["address", "signature", "nonce", "tip"]:
                if not key in extrinsic_data.keys():
                    extrinsic_data[key] = None
            extrinsic = Extrinsic(
                extrinsic_hash = extrinsic_data["extrinsic_hash"],
                extrinsic_length = extrinsic_data["extrinsic_length"],
                signature = extrinsic_data["signature"],
                #era = extrinsic_data["era"],
                nonce = extrinsic_data["nonce"],
                module_name = extrinsic_data["call"]["call_module"],
                function_name = extrinsic_data["call"]["call_function"],
                #call_args = extrinsic_data["call"]["call_args"],
                #tip = extrinsic_data["tip"],

                
                #has_callee = extrinsic_data["address"],
                #has_events = events
            
            )
            current_events = self.handle_events(events_data, i)
            last_event = json.loads(current_events[-1].attributes)
            print(last_event)
            #print(current_events[-1].attributes)
            print(json.loads(current_events[-1].attributes)[0])
            exit()
            extrinsic.has_block.add(block)
            
            #last event denotes if ectrinsic was successfull
            was_successful = current_events[-1].event_name == "ExtrinsicSuccess"


            for event in current_events:
                extrinsic.has_events.add(event)
                event.has_extrinsic.add(extrinsic)
                event.has_block.add(block)
                self.driver.save(event)
            self.driver.save(extrinsic)
            #self.special_event(block, extrinsic, current_events)

            extrinsics.append(extrinsic)
            


        #if len(extrinsics)> 0:
        #    return extrinsics[0]
        return extrinsics


    def handle_events(self,events, extrinsic_idx) -> List[Event]:
        """
            Iterates through events, selects those that have the same extrinsic_idx as the given one
            stores them in the db and returns all found events


            The events correspond to the transactions based on the order the transactions were executed
            The last event of a transaction indicates if the transaction was executed successfully
            i.e. the first transaction (timestamp) with index 0 has one event (with extrinsic_id 0) that indicates if it was successfull.
            an extrinsic (lets say it was extrinsic n) that sends DOT to an other account has multiple events (all with the same extrinic_id = n-1)

        """
        current_events = []
        for event_data in events:
            if extrinsic_idx == 0:
                extrinsic_idx = None
            if event_data["extrinsic_idx"] == extrinsic_idx:
                current_events.append(self.insert_event(event_data))


        return current_events


    def insert_event(self,event_data):
        """
        Stores event data in db
        """

        event_data.pop("event")
        
        event_data.pop("event_index")

        event = Event(
            event_order_id = event_data["extrinsic_idx"], #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
            phase = event_data["phase"],
            module_name =  event_data["module_id"],
            event_name =  event_data["event_id"],
            attributes = json.dumps(event_data["attributes"]),
            topics = event_data["topics"]
    
        )

        return event


    def special_event(self,block, extrinsic, events):
        """
        Each event has some implications on the overall data model. This function here differentiates between
        the different modules and then uses a event handler class to handle the specific event.
        e.g. the event "NewAccount" of the "Systems" module means that we have to create a new Account entry.

        Since not all data relevant for us is contained in the event data (sometimes we additionally need to know the blocknumber or time)
        we use the whole block.
        """
        for event in events:
                print(f"{event.module_name}: {event.event_name}")
                if event.module_name == "System":
                    handler= SystemEventHandler(self.session)
                    handler.handle_event(block, extrinsic, event)

              
                elif event.module_name == "Balances":
                    handler = BalancesEventHandler(self.session)
                    handler.handle_event(block, extrinsic, event)

                
                elif event.module_name == "Staking":
                    handler = StakingEventHandler(self.session)
                    handler.handle_event(block, extrinsic, event)
                
                elif event.module_name == "Claims":
                    handler = ClaimsEventHandler(self.session)
                    handler.handle_event(block, extrinsic, event)
                
                
                #handler.handle_event(block, extrinsic, event)
            


