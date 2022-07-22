import logging
from typing import List
import datetime
import json
from src.pg_models.balance import Balance
from src.event_handlers.utils import event_error_handling
#from src.pg_models import Block as b,Extrinsic as e,Event as v
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic
from src.pg_models.event import Event
from src.pg_models.account import Account
from src.pg_models.transfer import Transfer
from src.pg_models.controller import Controller
#from src.event_handlers_pg import SystemEventHandler, BalancesEventHandler, StakingEventHandler, ClaimsEventHandler
from sqlalchemy.exc import IntegrityError
from src.node_connection import handle_one_block
class PGBlockHandler:
    def __init__(self, session):
        self.session = session


    def handle_blocks(self,start, end):
        for i in range(start, end+1):
            with open(f"small_block_dataset/{i}.json", "r") as f:
                data = json.loads(f.read())  
            self.handle_full_block(data)
            print(data["number"])
            #self.session.commit()

    def handle_node_connection_blocks(self,start,end):
        for i in range(start, end+1):
            block = handle_one_block(i)
            self.handle_full_block(block)
            print(block["number"])

    def handle_full_block(self,data):
        block = self.insert_block(data)
        extrinsics= self.handle_extrinsics_and_events(block,data)
        

    def insert_block(self,data):
        return Block.create(data)

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
            current_events_data = self.handle_events(events_data, i)
            #last event denotes if ectrinsic was successfull
            #was_successful = current_events[-1].event_name == "ExtrinsicSuccess"
            extrinsic = Extrinsic.create(block, extrinsic_data,current_events_data)
            events = [Event.create(event_data,extrinsic.id,block.block_number) for event_data in current_events_data]

            self.handle_special_extrinsics(block, extrinsic, events)
            """


            # if no era create an empty list
            if not "era" in extrinsic_data.keys():
                extrinsic_data["era"] = [None]
            # change immortal transactions "00" to -1
            if extrinsic_data["era"] == "00":
                extrinsic_data["era"] = [-1]

            for key in ["address", "signature", "nonce", "tip"]:
                if not key in extrinsic_data.keys():
                    extrinsic_data[key] = None
     
            try:
                extrinsic = Extrinsic(
                    extrinsic_hash = extrinsic_data["extrinsic_hash"],
                    block_number = data["number"],
                    extrinsic_length = extrinsic_data["extrinsic_length"],
                    address = extrinsic_data["address"],
                    signature = extrinsic_data["signature"],
                    era = extrinsic_data["era"],
                    nonce = extrinsic_data["nonce"],
                    tip = extrinsic_data["tip"],
                    module_name = extrinsic_data["call"]["call_module"],
                    function_name = extrinsic_data["call"]["call_function"],
                    call_args = extrinsic_data["call"]["call_args"],
                    was_successful = True,
                    fee = 0
                
                )
                self.session.add(extrinsic)
                try:
                    self.session.commit()
                except IntegrityError:
                    pass
                    
                for event in current_events:
                    event.extrinsic = extrinsic.id
                    event.block_number = data["number"]
                    self.session.add(event)
                try:
                    self.session.commit()
                except IntegrityError:
                    pass
            except IntegrityError:
                pass
            """
            
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
                current_events.append(event_data)


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
            attributes = event_data["attributes"],
            topics = event_data["topics"]
    
        )

        return event


    def handle_special_extrinsics(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        """
        Each event has some implications on the overall data model. This function here differentiates between
        the different modules and then uses a event handler class to handle the specific event.
        e.g. the event "NewAccount" of the "Systems" module means that we have to create a new Account entry.

        Since not all data relevant for us is contained in the event data (sometimes we additionally need to know the blocknumber or time)
        we use the whole block.
        """
        print(extrinsic.module_name)
        if(extrinsic.module_name == "Balances" and extrinsic.function_name in ["transfer", "transfer_keep_alive,transfer_all"]):
            self.__handle_transfer(block, extrinsic, events)
        
        elif(extrinsic.module_name == "Staking" and extrinsic.function_name in ["bond", "bond_extra"]):
            self.__handle_bond(block, extrinsic, events)




    def __handle_transfer(self, block: Block, extrinsic: Extrinsic, events: List[Event]):
        from_account = Account.get(extrinsic.account)
        to_address = extrinsic.call_args[0]["value"]
        to_account = Account.get_from_address(to_address)
        if not to_account:
            to_account = Account.create(to_address)
        
        # Get amount transferred from 'Transfer' event

        for event in events:
            if event.event_name == 'Transfer':
                print(event.attributes)
                amount_transferred = event.attributes[2]['value']

        # Create new balances
        from_balance = Balance.create(from_account, block.block_number, transferable=-(amount_transferred+extrinsic.fee))
        to_balance = Balance.create(from_account, block.block_number,transferable=amount_transferred)

        transfer = Transfer.create(
            block_number=block.block_number,
            from_account=from_account,
            to_account=to_account,
            from_balance=from_balance,
            to_balance=to_balance,
            value=amount_transferred,
            extrinsic=extrinsic,
            type=extrinsic.function_name
        )
    
    def __handle_bond(self,block: Block, extrinsic: Extrinsic, events: List[Event]):
        from_account = Account.get(extrinsic.account)
        print(extrinsic.call_args)
        
        if extrinsic.function_name == "bond":
            amount_transferred = extrinsic.call_args[1]["value"]
            controller_address = extrinsic.call_args[0]["value"]
            controller_account = Account.get_from_address(controller_address)
            if not controller_account:
                controller_account = Account.create(controller_address)
            Controller.create(controller_account, from_account)
        elif extrinsic.function_name == "bond_extra":
            amount_transferred = extrinsic.call_args[0]["value"]
        else:
            raise NotImplementedError()
        
        old_balance = Balance.get_last_balance(from_account)
        new_balance = Balance.create(from_account, extrinsic,transferable=-(extrinsic.fee+amount_transferred) ,bonded=amount_transferred)
        
        Transfer.create(
            block_number=block.block_number,
            from_account=from_account,
            to_account=from_account,
            from_balance=old_balance,
            to_balance=new_balance,
            value=amount_transferred,
            extrinsic=extrinsic,
            type=extrinsic.function_name
        )
