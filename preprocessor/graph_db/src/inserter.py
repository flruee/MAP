import logging
from typing import Dict, List
import datetime
import json

from sqlalchemy import JSON
#from src.event_handlers.utils import event_error_handling
from src.models import Block,Transaction, Account, Balance, Transaction
from src.driver_singleton import Driver
#from src.event_handlers_pg import SystemEventHandler, BalancesEventHandler, StakingEventHandler, ClaimsEventHandler
from sqlalchemy.exc import IntegrityError
#from src.node_connection import handle_one_block
from py2neo.ogm import Repository


class Neo4jBlockHandler:
    def __init__(self, driver: Repository):
        self.driver = driver
        self.handled_call_modules = ['Balances',
                                'Staking',
                                'Treasury',

                                ]
    def handle_full_block(self,data):
        
        block = self.__handle_block_data(data)
        transactions= self.__handle_transaction_data(data, block)
        #events = self.__insert_events(data, extrinsics)
        #author = self.__add_fees_to_author(data["header"]["author"],block, events)
        #self.__commit_all(block, extrinsics, events, author)
        

    def __handle_block_data(self,data):
        """
        Creates new block node and connects it to previous block node
        """
        
        timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]
        timestamp = datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=timestamp)

        last_block = Block.match(Driver().get_driver(), data["number"]-1).first()

        block = Block(
            block_number=data["number"],
            hash=data["hash"],
            timestamp=timestamp,
        )

        author = Account.get(data["header"]["author"])
        if not author:
            author = Account.create(data["header"]["author"])
        block.has_author.add(author)


        #Only a problem for the first block
        try:
            block.previous_block.add(last_block)
        except TypeError:
            pass
        
        #Block.save(block)
        return block



    def __handle_transaction_data(self, data, block: Block):

        transactions = []
        events_data = data["events"]

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

            #TODO make a parainherent check here
            extrinsic_data = data["extrinsics"][i]
            current_events = self.handle_events(events_data, i)

            # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
            # timestamp is already handled above
            transaction = self.__handle_transaction(block,extrinsic_data, current_events)
            if not transaction:
                continue
            block.has_transaction.add(transaction)

            transactions.append(transaction)
        return transactions

    def __handle_transaction(self, block: Block,transaction_data: Dict,event_data: Dict):
        """
        creates a transaction node, 
        """

        if not transaction_data["call"]["call_module"] in self.handled_call_modules:
            return None
        
        if transaction_data["call"]["call_function"] in ["transfer", "transfer_all"]:
            transaction = Transaction.create(block,transaction_data, event_data)
            #Transaction.handle_transfer(transaction, transaction_data, block)
            
        else:
            return None
        


    
    

    def __add_fees_to_author(self, address, block, events: List):
        
        author = Account.match(self.driver, address).first()
        if author is None:
            author, author_balance = self.__create_account(address )
        else:
            author_balance =  list(author.has_balances.triples())[-1][-1]
                
        fees = 0
        for event in events:
            if event.module_name == "Balances" and event.event_name == "Deposit":
                attributes = json.loads(event.attributes)
                if not attributes[0]["value"] == author.address:
                    raise Exception("author and event address not the same")
                fees += attributes[1]["value"]
        if fees != 0:
            new_balance = Balance(
                transferable = author_balance.transferable + fees,
                reserved = author_balance.reserved,
                bonded = author_balance.bonded,
                unbonding = author_balance.unbonding
            )

            author.has_balances.add(new_balance)
            block.has_balances.add(new_balance)
            self.driver.save(new_balance)

        block.has_author.add(author)

        return author
        


    def __create_account(self, address:str):
        account = Account(
            address = address
        )
        balance = Balance(
            transferable = 0,
            reserved = 0,
            bonded = 0,
            unbonding = 0
        )

        account.has_balances.add(balance)

        self.driver.save(account)
        self.driver.save(balance)

        return account, balance
        

    def __commit_all(self, block, extrinsics, events, author):
        self.driver.save(author)

        for event in events:
            self.driver.save(event)
        for extrinsic in extrinsics:
            self.driver.save(extrinsic)
        self.driver.save(block)


    


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
            

    def handle_events(self,events, extrinsic_idx) -> List:
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
