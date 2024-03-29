import json
import logging
import ssl
import time
from typing import List
import datetime
from src.models import Block, Transaction, Account, Transaction, Validator, ValidatorPool, Nominator, Utils
from src.driver_singleton import Driver
from py2neo.ogm import Repository
from py2neo import Subgraph, Relationship
from substrateinterface import SubstrateInterface
from websocket._exceptions import WebSocketConnectionClosedException
import copy


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
        else:
            block = Block.create(data, timestamp)
        author_address = data["header"]["author"]
        subgraph = Subgraph()
        author_account = Account.get(subgraph, author_address)
        if not author_account:
            author_account = Account.create(author_address)
        validator = Validator.get_from_account(author_account)
        if not validator:
            validator, account_validator_relationship = Validator.create(validator_account=author_account)
            subgraph = Utils.merge_subgraph(subgraph, account_validator_relationship, validator)

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

        for event in events_data:
            if event['module_id'] == "Staking" and event['event_id'] in ['EraPayout', 'EraPaid']:
                validatorpool = self.handle_validatorpool(event, subgraph, block)
                subgraph = Utils.merge_subgraph(subgraph, validatorpool)

        if len(data['extrinsics']) == 1 and len(data["events"]) > 2:  # Todo: handle differently,
            """
            This was done because some blocks contain 0 extrinsics, 
            however they contain events that require handling
            """
            start = 0
            logging.warning(f"strange block {data['number']}")
        else:
            start = 1
        if start and len(data['extrinsics']) == 1:
            # block nr 1603427
            subgraphs.append(subgraph)
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
    def __create_substrate_connection():
        with open("config.json","r") as f:
            node_config=json.loads(f.read())["node"]
        sslopt = {
        "sslopt": {
            "cert_reqs": ssl.CERT_NONE
            }
        }
        substrate = SubstrateInterface(
            url=node_config["url"],
            ss58_format=node_config["ss58_format"],
            type_registry_preset=node_config["type_registry_preset"],

            ws_options=sslopt
        )
        return substrate

    def __retry_query(self, substrate, module, storage_function, params, block_hash, n=5):
        """
        Sometimes a websocket connection closes, possibly due to overload.
        This function tries the query, if a websocket connection occurs it tries to reconnect n times and
        repeat the query, if all else fails it throws
        """
        for i in range(n):
            try:
                # The query function modifies params in place
                # If we repeat the query the params list will be modified
                # and the function will fail -> deepcopy the params
                params2 = copy.deepcopy(params)
                print(f"{substrate}: {type(substrate)}")
                print(f"{module}: {type(module)}")
                print(f"{storage_function}: {type(storage_function)}")
                for p in params2:
                    print(f"{p}: {type(p)}")
                print(f"{block_hash}: {type(block_hash)}")
                return substrate.query(
                    module=module,
                    storage_function=storage_function,
                    params=params2,
                    block_hash=block_hash
                ).value
            except WebSocketConnectionClosedException:
                print("ERROR: WEBSOCKETCONNECTION CLOSED. Retrying...")
                time.sleep(5)
                substrate = self.__create_substrate_connection()

        raise WebSocketConnectionClosedException()


    def handle_validatorpool(self, event, subgraph, block):

        base_subgraph = subgraph

        current_validatorpool = ValidatorPool.create(
                                                    event=event,
                                                    block=block)
        previous_validatorpool_node = ValidatorPool.get(event['attributes'][0]['value']-1)
        if previous_validatorpool_node is not None:
            current_previous_relationship = Relationship(current_validatorpool,
                                                         "PREVIOUS_POOL",
                                                         previous_validatorpool_node)
            subgraph = Utils.merge_subgraph(subgraph, current_previous_relationship)
        substrate = Neo4jBlockHandler.__create_substrate_connection()
        # Get all validators of era
        validator_reward_points = self.__retry_query(
            substrate=substrate,
            module='Staking',
            storage_function='ErasRewardPoints',
            params=[current_validatorpool['era']],
            block_hash=block['hash']
        )
        counter = 0
        staking_sum = 0
        for validator_address, reward_points in validator_reward_points["individual"]:

            validator_account = Account.get(subgraph, validator_address)
            if validator_account is None:
                validator_account = Account.create(validator_address)
            subgraph = Utils.merge_subgraph(subgraph, validator_account)
            validator_staking = substrate.query(
                module='Staking',
                storage_function='ErasStakers',
                params=[current_validatorpool['era'], validator_address],
                block_hash=block['hash']
            ).value
            commission = substrate.query(
                module='Staking',
                storage_function='ErasValidatorPrefs',
                params=[current_validatorpool['era'], validator_address],
                block_hash=block['hash']
            ).value
            validator, account_validator_relationship = Validator.create(validator_account, current_validatorpool, reward_points,
                                         validator_staking, commission)
            validatorpool_validator_relationship = Relationship(current_validatorpool, "HAS_VALIDATOR", validator)
            subgraph = Utils.merge_subgraph(subgraph, validator, account_validator_relationship, validatorpool_validator_relationship)
            staking_sum += validator['total_stake']

            for element in validator_staking["others"]:
                counter +=1
                print(counter)
                nominator_address = element["who"]
                nominator_stake = element["value"]
                nominator_account = Account.get(subgraph, nominator_address)
                if nominator_account is None:
                    nominator_account = Account.create(nominator_address)

                nominator, nominator_account_relationship = Nominator.create(nominator_account, nominator_stake)
                validator_nominator_relationship = Relationship(validator, 'HAS_NOMINATOR', nominator)
                subgraph = Utils.merge_subgraph(subgraph, nominator, nominator_account, validator_nominator_relationship, nominator_account_relationship)

            tx = Driver().get_driver().graph.begin()
            tx.create(subgraph)
            Driver().get_driver().graph.commit(tx)

            subgraph = Subgraph()
            subgraph = Utils.merge_subgraph(subgraph, base_subgraph)
        current_validatorpool['total_stake'] = staking_sum
        return Utils.merge_subgraph(subgraph, current_validatorpool)


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
