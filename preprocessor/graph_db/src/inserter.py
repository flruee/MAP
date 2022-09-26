import logging
from typing import List
import datetime
from src.models import Block, Transaction, Account, Transaction, Validator, ValidatorPool, Nominator, Utils
from src.driver_singleton import Driver
from py2neo.ogm import Repository
from py2neo import Subgraph, Relationship


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

    @staticmethod
    def __handle_block_data(data):
        """
        Creates new block node and connects it to previous block node
        """
        timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]
        timestamp = datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=timestamp)

        last_block = Driver().get_driver().graph.run(
            "Match (n:Block{block_number:" + str(data['number'] - 1) + "}) return n").evaluate()

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
            validator, account_validator_relationship = Validator.create(amount_staked=0, self_staked=0, nominator_staked=0,
                                         account=author_account)
            subgraph = Utils.merge_subgraph(subgraph, account_validator_relationship)

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
        if start and len(data['extrinsics']) == 1:  # block nr 1603427
            subgraphs.append(Subgraph())
        else:
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

    @staticmethod
    def handle_validatorpool(event, subgraph, block):
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
            current_previous_relationship = Relationship(current_validatorpool,
                                                         "PREVIOUS_POOL",
                                                         last_validator_pool_node)
            subgraph = Utils.merge_subgraph(subgraph, current_previous_relationship)
        currentpool_block_relationship = Relationship(current_validatorpool, "FROM_BLOCK", block)
        for validator in event['attributes'][0]['value']:
            validator_address = Utils.convert_public_key_to_polkadot_address(validator['authority_id'])
            validator_account = Account.get(subgraph, validator_address)
            if validator_account is None:
                validator_account = Account.create(validator_address)
            validator_node = Validator.get_from_account(validator_account)
            account_validator_relationship = Relationship(validator_account, "IS_VALIDATOR", validator_node)
            validatorpool_validatornode_relationship = Relationship(current_validatorpool,
                                                                    "HAS_VALIDATOR",
                                                                    validator_node)
            subgraph = Utils.merge_subgraph(subgraph, validator_node, validator_account,
                                            validatorpool_validatornode_relationship, account_validator_relationship)
        return Utils.merge_subgraph(subgraph, current_validatorpool, currentpool_block_relationship)

    @staticmethod
    def handle_events(events, extrinsic_idx) -> List:
        """
                Iterates through events, selects those that have the same extrinsic_idx as the given one
                stores them in the db and returns all found events

                The events correspond to the transactions based on the order the transactions were executed
                The last event of a transaction indicates if the transaction was executed successfully
                i.e. the first transaction (timestamp) with index 0 has one event (with extrinsic_id 0) that indicates
                if it was successful. An extrinsic (lets say it was extrinsic n) that sends DOT to another account has
                multiple events (all with the same extrinsic_id = n-1)

            """
        current_events = []
        for event_data in events:
            if extrinsic_idx == 0:
                extrinsic_idx = None
            if event_data["extrinsic_idx"] == extrinsic_idx:
                current_events.append(event_data)

        return current_events
