import logging
from typing import Dict, List
import datetime
import json
from src.models import Block, Transaction, Account, Transaction, Validator, ValidatorPool, Nominator, Utils
from src.driver_singleton import Driver
from py2neo.ogm import Repository
from py2neo import Subgraph, Node, Relationship


class Neo4jBlockHandler:
    def __init__(self, driver: Repository):
        self.driver = driver
        self.current_era = None
        self.block_author = None

    def handle_full_block(self, data):
        block, subgraph = self.__handle_block_data(data)
        subgraphs = self.__handle_transaction_data(data, block, subgraph)
        if not len(subgraphs):
            return
        if not len(subgraphs) == 1:
            subgraph = subgraphs[0]
            for sub in subgraphs[1:]:
                subgraph = Utils.merge_subgraph(subgraph, sub)
        else:
            subgraph = subgraphs[0]
        return subgraph
        """        tx = Driver().get_driver().graph.begin()
        tx.create(subgraph)
        tx.commit()"""

    def __handle_block_data(self, data):
        """
        Creates new block node and connects it to previous block node
        """
        timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]
        timestamp = datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=timestamp)
        last_block = Block.match(Driver().get_driver(), data["number"] - 1).first()
        if last_block is not None:
            last_block = last_block.__node__
        block = Block.match(Driver().get_driver(), data["number"]).first()
        if block is not None:
            block = block.__node__
        if block is None:
            block = Block.create(data, timestamp)
        author_address = data["header"]["author"]
        subgraph = Subgraph()
        author_account = Account.get(subgraph, author_address)
        if not author_account:
            author_account = Account.create(author_address)
        validator = Validator.get_from_account(author_account)
        if not validator:
            validator = Validator.create(amount_staked=0, self_staked=0, nominator_staked=0,
                                         account=author_account)

        if last_block is not None:
            block_lastblock_relationship = Relationship(block, "PREVIOUS_BLOCK", last_block)
            subgraph = Utils.merge_subgraph(subgraph, block_lastblock_relationship)

        block_validator_relationship = Relationship(block, "HAS_AUTHOR", validator)
        account_validator_relationship = Relationship(author_account, "IS_VALIDATOR", validator)

        subgraph = Utils.merge_subgraph(subgraph, block, author_account, validator, block_validator_relationship,
                             account_validator_relationship)
        return block, subgraph

    def __handle_transaction_data(self, data, block, subgraph):
        events_data = data["events"]
        subgraphs = []
        last_event_module = events_data[-1]['module_id']
        last_event_function = events_data[-1]['event_id']
        if last_event_function == 'NewAuthorities' and last_event_module == 'Grandpa':
            subgraph = self.handle_validatorpool(events_data[-1], subgraph, block)
            subgraphs.append(subgraph)
        if len(data['extrinsics']) == 1 and len(data["events"]) > 2:  # Todo: handle differently,
            """
            This was done because some blocks contain 0 extrinsics, 
            however they contain events that require handling
            """
            start = 0
            logging.warning(f"strange block {data['number']}")
        else:
            start = 1
        for i in range(start, len(data["extrinsics"])):
            # TODO make a parainherent check here
            extrinsic_data = data["extrinsics"][i]
            current_events = self.handle_events(events_data, i)

            # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
            # timestamp is already handled above

            subgraph = Transaction.create(block=block,
                               transaction_data=extrinsic_data,
                               event_data=current_events,
                               proxy_transaction=None,
                               batch_from_account=None,
                               batch_transaction=None,
                               subgraph=subgraph
                               )
            subgraphs.append(subgraph)
        return subgraphs


    def __handle_transaction(self,
                             block,
                             transaction_data,
                             event_data,
                             author_account,
                             validator,
                             treasury_account):
        """
        creates a transaction node,
        """
        return

    @staticmethod
    def handle_validatorpool(event, subgraph, block):
        #validatorpool.from_block.add(block)
        last_validator_pool_node = None
        if block['block_number'] == 328745:
            era = 0
        else:
            last_validator_pool = ValidatorPool.get()
            last_validator_pool_node = last_validator_pool.__node__
            era = last_validator_pool.era + 1
        current_validatorpool = ValidatorPool.create(era=era,
                             total_staked=0,
                             total_reward=0)
        if last_validator_pool_node is not None:
            current_previous_relationship = Relationship(current_validatorpool, "PREVIOUS_POOL", last_validator_pool_node)
            subgraph = Utils.merge_subgraph(subgraph, current_previous_relationship)
        currentpool_block_relationship = Relationship(current_validatorpool, "FROM_BLOCK", block)
        for validator in event['attributes'][0]['value']:
            validator_address = Utils.convert_public_key_to_polkadot_address(validator['authority_id'])
            validator_account = Account.get(subgraph, validator_address)
            if validator_account is None:
                validator_account = Account.create(validator_address)
            validator_node = Validator.get_from_account(validator_account)
            account_validator_relationship = Relationship(validator_account, "IS_VALIDATOR", validator_node)
            validatorpool_validatornode_relationship = Relationship(current_validatorpool, "HAS_VALIDATOR", validator_node)
            subgraph = Utils.merge_subgraph(subgraph, validator_node, validator_account,
                                            validatorpool_validatornode_relationship, account_validator_relationship)
        return Utils.merge_subgraph(subgraph, current_validatorpool, currentpool_block_relationship)


    def __handle_event_data(self, data, transactions, block):
        """
        Here we handle events that contain crucial information not tied to any extrinsics.
        In the case of ['EraPayout', 'EraPaid'] we extract the previous era (and add one to get the current era)
        In the case of 'NewAuthorities' we extract the new set of active validators for the current era.
            We further extract the previous validatorpool via era-index in order to establish the relation
            "previous_validator_pool" with the current validator_pool.
        """
        try:
            if data['events'][1]['event_id'] not in ['EraPayout', 'EraPaid']:
                return
        except IndexError:
            return
        for event in data['events']:
            if event['event_id'] in ['EraPayout', 'EraPaid'] and event['module_id'] == 'Staking':
                current_era = event['attributes'][0]['value'] + 1
            elif event['event_id'] == 'NewAuthorities' and event['module_id'] == 'Grandpa':
                validator_pool = ValidatorPool.create(current_era, block)
                previous_validator_pool = ValidatorPool.get(current_era - 1)
                if previous_validator_pool is None:
                    pass
                else:
                    validator_pool.previous_validator_pool.add(previous_validator_pool)
                    previous_validator_pool.to_block.add(list(block.previous_block.triples())[0][2])

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

        author_balance = list(author.has_balances.triples())[-1][-1]

        fees = 0
        for event in events:
            if event.module_name == "Balances" and event.event_name == "Deposit":
                attributes = json.loads(event.attributes)
                if not attributes[0]["value"] == author.address:
                    raise Exception("author and event address not the same")
                fees += attributes[1]["value"]
        if fees != 0:
            new_balance = Balance(
                transferable=author_balance.transferable + fees,
                reserved=author_balance.reserved,
                bonded=author_balance.bonded,
                unbonding=author_balance.unbonding
            )

            author.has_balances.add(new_balance)
            block.has_balances.add(new_balance)
            self.driver.save(new_balance)

        block.has_author.add(author)

        return author

    def handle_events(self, events, extrinsic_idx) -> List:
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
