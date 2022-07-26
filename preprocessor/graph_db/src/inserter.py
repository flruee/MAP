import logging
from typing import Dict, List
import datetime
import json
from src.models import Block,Transaction, Account, Balance, Transaction, Validator, ValidatorPool, Nominator
from src.driver_singleton import Driver
from py2neo.ogm import Repository


class Neo4jBlockHandler:
    def __init__(self, driver: Repository):
        self.driver = driver
        self.handled_call_modules = ['Balances',
                                     'Staking',
                                     'Treasury'
                                     ]
        self.current_era = None
        self.block_author = None

    def handle_full_block(self, data):
        
        block = self.__handle_block_data(data)
        transactions = self.__handle_transaction_data(data, block)
        events = self.__handle_event_data(data, transactions, block)
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

        author_account = Account.get(data["header"]["author"])
        if not author_account:
            author_account = Account.create(data["header"]["author"])

        validator = Validator.get_from_account(author_account)
        if not validator:
            validator = Validator.create(author_account)

        block.has_author.add(validator)



        # Only a problem for the first block
        try:
            block.previous_block.add(last_block)
        except TypeError:
            pass
        
        Block.save(block) #todo: save block
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
        if transaction_data["call"]["call_function"] in \
                ["transfer", "transfer_all", "transfer_keep_alive", "bond","bond_extra","set_controller", "set_payee"]:
            transaction = Transaction.create(block,transaction_data, event_data)
            #Transaction.handle_transfer(transaction, transaction_data, block)
            
        else:
            return None

    def __handle_event_data(self, data, transactions, block):

        for extrinsic in data['extrinsics']:
            if extrinsic['call']['call_function'] == 'payout_stakers' and extrinsic['call']['call_module'] == 'Staking':
                payout_era = extrinsic['call']['call_args'][1]['value']
                payout_validator = extrinsic['call']['call_args'][0]['value']
        for event in data['events']:
            if event['event_id'] == 'EraPayout' and event['module_id'] == 'Staking':
                self.current_era = event['attributes'][0]['value']
            elif event['event_id'] == 'NewAuthorities' and event['module_id'] == 'Grandpa':
                validator_pool = ValidatorPool.create(self.current_era, block)
                previous_validator_pool = ValidatorPool.get(self.current_era - 1)
                if previous_validator_pool is None:
                    pass
                else:
                    validator_pool.previous_validator_pool.add(previous_validator_pool)
                    previous_validator_pool.to_block.add(list(block.previous_block.triples())[0][2])
            elif event['event_id'] == 'Reward' and event['module_id'] == 'Staking':
                nominator_reward = event['attributes'][1]['value']
                nominator_address = event['attributes'][0]['value']
                nominator_account = Account.get(nominator_address)
                if nominator_account is None:
                    nominator_account = Account.create(nominator_address)
                if nominator_account.reward_destination in [None, 'Stash', 'Controller', 'Account']:
                    nominator_account.update_balance(transferable=nominator_reward)
                elif nominator_account.reward_destination in ['Staked']:
                    nominator_account.update_balance(bonded=nominator_account)
                nominator = Nominator.get_from_account(nominator_account)
                nominator_account.is_nominator.add(nominator)
                Account.save(nominator_account)
                nominator.reward = nominator_reward
                author_account = Account.get(payout_validator)
                if not author_account:
                    author_account = Account.create(payout_validator)

                validator = Validator.get_from_account(author_account)
                if not validator:
                    validator = Validator.create(author_account)
                Nominator.save(nominator)
                validator.has_nominator.add(nominator)
                Validator.save(validator)

        if self.current_era is not None:
            validator_pool = ValidatorPool.get(self.current_era)
            if validator_pool is None:
                validator_pool = ValidatorPool.create(self.current_era, block)
            validator_pool = self.__add_validator_to_validatorpool(validator_pool, block)
            ValidatorPool.save(validator_pool)
        return

    def __add_validator_to_validatorpool(self, validator_pool, block):
        validators = list(validator_pool.hasValidators.triples())
        if not len(validators):
            validator_pool.hasValidators.add(list(block.has_author.triples())[0][2])
        else:
            for validator in validators:
                if list(block.has_author.triples())[0][2] != validator[2]:
                    validator_pool.hasValidators.add(list(block.has_author.triples())[0][2])
        return validator_pool


    def __add_fees_to_author(self, address, block, events: List):
        
        author = Account.match(self.driver, address).first()
        if author is None:
            author = Account.create_account(address)

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
