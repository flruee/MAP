from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
from src.driver_singleton import Driver
from typing import Dict
from substrateinterface.utils import ss58
from py2neo import Subgraph, Node, Relationship
import time
import logging

Base = declarative_base()
"""
Block
"""

treasury_address = "13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB"


def decorator_factory(decorator):
    """
    Meta decorator
    Is used to decorate other decorators such that they can have passed an argument
    e.g. 
    @decorator(argument)
    would not work if decorator isn't decorated with this decorator
    It is used mostly for the event_error_handling such that we can decorate a function with an exception and
    log it if something bad happened
    """

    def layer(error, *args, **kwargs):
        def repl(f, *args, **kwargs):
            return decorator(f, error, *args, **kwargs)

        return repl

    return layer


@decorator_factory
def profiler(function, cls_name, *args, **kwargs):
    def wrapper(*args, **kwargs):
        logging.debug("Transaction started")
        start = time.perf_counter()
        result = function(*args, **kwargs)
        logging.debug(f"Transaction finished {cls_name} {function.__name__} took {time.perf_counter() - start} s")
        return result

    return wrapper


class RawData(Base):
    __tablename__ = "raw_data"
    block_number = Column(Integer, primary_key=True)
    data = Column(JSON)

    def __repr__(self):
        return f"Block {self.block_number}"


class Utils:
    schema = dict()
    @staticmethod
    def convert_public_key_to_polkadot_address(address):
        try:
            if address[0] == '1':
                return address
            return ss58.ss58_encode(ss58_format=0, address=address)
        except ValueError:
            address = address.replace("0x", "")
            if address[0] == '1':
                return address

    @staticmethod
    def extract_event_attributes(event, treasury):
        if treasury:
            try:
                if event['event_id'] == 'Transfer':
                    return 0
                result = event['attributes']
                if isinstance(result, int):
                    return result
                else:
                    result1 = result[0]['value']
                    if isinstance(result1, int):
                        return result1
                    else:
                        return result[1]['value']
            except KeyError:
                return 0
        else:
            result = event['attributes'][1]
            if isinstance(result, Dict):
                return result['value']
            else:
                return result

    @staticmethod
    def merge_subgraph(subgraph, *other):
        for element in other:
            subgraph = subgraph | element
        return subgraph

    @staticmethod
    def merge(res_list):
        new_list = []
        for i in range(int(len(res_list))):
            if len(res_list) == 1:
                new_list.append(res_list[0])
                return new_list
            elif len(res_list) == 0:
                return new_list
            else:
                try:
                    x = res_list.pop()
                except IndexError:
                    x = Subgraph()
                try:
                    y = res_list.pop()
                except IndexError:
                    y = Subgraph()
            new_list.append(Utils.merge_subgraph(x, y))
        return new_list

    def set_schema(self, schema):
        self.schema = schema

    def restructure_block(self, data, schema):
        self.set_schema(schema)

        return


class Block(GraphObject):
    __primarykey__ = "block_number"

    block_number = Property("block_number")
    hash = Property("hash")
    timestamp = Property("timestamp")

    has_author = RelatedTo("Validator")
    has_transaction = RelatedTo("Transaction")
    previous_block = RelatedTo("Block")
    has_aggregator = RelatedTo("Aggregator")

    @staticmethod
    def create(data, timestamp):
        block = Node("Block",
                     block_number=data["number"],
                     hash=data["hash"],
                     timestamp=timestamp
                     )
        return block

    @staticmethod
    def save(block: "Block"):
        Driver().get_driver().save(block)


class Transaction(GraphObject):
    extrinsic_hash = Property()
    amount_transferred = Property()
    is_successful = Property()

    has_extrinsic_function = RelatedTo("ExtrinsicFunction")
    has_event_function = RelatedTo("EventFunction")
    reward_validator = RelatedTo("Balance")
    reward_treasury = RelatedTo("Balance")
    sender_account = RelatedTo("Account")
    is_proxy = RelatedTo("Transaction")
    is_batch = RelatedTo("Transaction")

    @staticmethod
    def finish_transaction(block, transaction):
        block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
        return block_transaction_relationship

    @staticmethod
    def save(transaction: "Transaction"):
        Driver().get_driver().save(transaction)

    @staticmethod
    def create(block,
               transaction_data,
               event_data,
               proxy_transaction=None,
               batch_from_account=None,
               batch_transaction=None,
               subgraph=None
               ):

        call_function = transaction_data["call"]["call_function"]
        call_module = transaction_data["call"]["call_module"]
        print(call_module, call_function)
        transaction = Node("Transaction",
                           extrinsic_hash=transaction_data["extrinsic_hash"])
        subgraph = Utils.merge_subgraph(subgraph, transaction)

        extrinsic_function = ExtrinsicFunction.get(call_function, subgraph)
        if extrinsic_function is None:
            extrinsic_function = ExtrinsicFunction.create(call_function)
        extrinsic_module = ExtrinsicModule.get(call_module, subgraph)
        if extrinsic_module is None:
            extrinsic_module = ExtrinsicModule.create(call_module)
        subgraph = Utils.merge_subgraph(subgraph, extrinsic_function, extrinsic_module)
        extrinsicfunction_extrinsicmodule_relationship = Relationship(extrinsic_function,
                                                                      "PART_OF_MODULE",
                                                                      extrinsic_module)
        transaction_extrinsicfunction_relationship = Relationship(transaction,
                                                                  "HAS_EXTRINSICFUNCTION",
                                                                  extrinsic_function)
        subgraph = Utils.merge_subgraph(subgraph, extrinsicfunction_extrinsicmodule_relationship,
                                        transaction_extrinsicfunction_relationship)

        #Transaction.handle_extrinsics_without_sender(call_module, call_function, subgraph, block, transaction)
        if call_module in ['FinalityTracker', 'Parachains', 'ParaInherent', 'ImOnline',
                           'ElectionProviderMultiPhase', 'Timestamp', 'Council', 'Claims', 'Babe']:
            """
            Simply return transaction since no balance shift takes place in these modules.
            """
            block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
            return Utils.merge_subgraph(subgraph, block_transaction_relationship)

        if call_module in ["Staking"] and call_function in ['submit_election_solution_unsigned']:
            block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
            return Utils.merge_subgraph(subgraph, block_transaction_relationship)

        if call_module in ["Grandpa"] and call_function in ['report_equivocation_unsigned']:
            block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
            return Utils.merge_subgraph(subgraph, block_transaction_relationship)
        """
        For batch calls we handle the individual extrinsics as seperate transactions. The fee paid is split up evenly
        between the individual calls.
        """
        if call_module == 'Utility' and call_function in ['batch', 'as_derivative', 'batch_all', 'force_batch']:
            from_account_address = transaction_data['address']
            from_account = Account.get(subgraph, from_account_address)
            if from_account is None:
                from_account = Account.create(from_account_address)

            event_start = 0
            event_end = len(event_data)
            if call_function == 'as_derivative':
                transaction_structure = dict()
                transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
                transaction_structure['address'] = transaction_data['address']
                transaction_structure['call'] = transaction_data['call']['call_args'][1]['value']
                return Transaction.create(block=block,
                                          transaction_data=transaction_structure,
                                          event_data=event_data,
                                          batch_from_account=from_account,
                                          batch_transaction=transaction,
                                          subgraph=subgraph)

            transaction_data_list = transaction_data['call']['call_args'][0]['value']
            for j in range(len(transaction_data_list)):
                sub_extrinsic_data = transaction_data_list[j]

                """
                We can't assign events to extrinsics (only after spec 9050 that introduced the 'ItemCompleted' event).
                This is most of the time not a great problem since we get our information from the extrinsic data.
                There is however the case of Staking(PayoutStakers). In this extrinsic the events carry the information
                of who got how much. Fortunately we know that the validator gets payed out first. We can therefore check if 
                the next extrinsic is also a payout extrinsic, then iterate through the events until we find the payout event
                for the validator in the next extrinsic and use all events until that one to create the rewards with the right era.
                """
                payout_staker_flag = False
                if (
                        j + 1 < len(transaction_data_list) and
                        transaction_data_list[j]["call_module"] == "Staking" and
                        transaction_data_list[j]["call_function"] == "payout_stakers" and
                        transaction_data_list[j + 1]["call_module"] == "Staking" and
                        transaction_data_list[j + 1]["call_function"] == "payout_stakers"
                ):
                    next_validator = transaction_data_list[j + 1]["call_args"][0]["value"]
                    payout_staker_flag = True

                for i in range(event_start, event_end):
                    if event_data[i]['module_id'] == "Utility":
                        if event_data[i]['event_id'] == "ItemCompleted":
                            was_successful = True
                            break
                        elif event_data[i]['event_id'] == "ItemFailed":
                            was_successful = False
                            break
                        elif event_data[i]['event_id'] == "BatchInterrupted":
                            was_successful = False
                            break
                        elif event_data[i]['event_id'] == "BatchCompleted":
                            was_successful = True
                            break
                    elif event_data[i]['event_id'] == "ProxyExecuted" and event_data[i]['module_id'] == 'Proxy':
                        was_successful = True
                        break
                        # True Horror, an encapsulation of type Sudo->Batch gives no indication as to which events
                        # belong to which item of the batch. we have to handle those by hand.
                    elif block['block_number'] in [240853, 240984, 372203, 500796]:
                        was_successful = True
                        i = i + 2  # take 3 events
                        break
                    elif payout_staker_flag and event_data[i]['module_id'] == "Staking" and\
                            event_data[i]['event_id'] == "Reward":
                        reward_account = Utils.convert_public_key_to_polkadot_address(
                            event_data[i]['attributes'][0]['value'])
                        if next_validator == reward_account and i != event_start:
                            i = i - 1
                            was_successful = True
                            break

                sub_events = event_data[event_start:i + 1]
                event_start = i + 1
                transaction_structure = dict()
                transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
                transaction_structure['address'] = transaction_data['address']
                transaction_structure['call'] = sub_extrinsic_data
                subgraph = Transaction.create(block=block,
                                              transaction_data=transaction_structure,
                                              event_data=sub_events,
                                              batch_from_account=from_account,
                                              batch_transaction=transaction,
                                              subgraph=subgraph)
        """
        Get account which triggered the transaction and set initial values of variables required for further processing
        """
        from_account_address = Utils.convert_public_key_to_polkadot_address(transaction_data['address'])
        if batch_from_account is None:
            from_account = Account.get(subgraph, from_account_address)
            if from_account is None:
                from_account = Account.create(from_account_address)
        else:
            from_account = batch_from_account
            transaction_batch_relationship = Relationship(transaction, "IS_BATCH", batch_transaction)
            subgraph = Utils.merge_subgraph(subgraph, transaction_batch_relationship)
        subgraph = Utils.merge_subgraph(subgraph, from_account)

        transaction_senderaccount_relationship = Relationship(transaction, "FROM_ACCOUNT", from_account)
        subgraph = Utils.merge_subgraph(subgraph, transaction_senderaccount_relationship)

        """
        Handle Extrinsics which failed. They are required to pay fees regardless of outcome.
        """
        if len(event_data):
            if event_data[-1]["event_id"] == "ExtrinsicFailed":
                transaction['is_succesful'] = False
                block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
                subgraph = Utils.merge_subgraph(subgraph, transaction)
                return Utils.merge_subgraph(subgraph, block_transaction_relationship)
        transaction.is_successful = True
        """
        Lastly we make a separate batch node which we connect to the individual call
        """
        if call_module == 'Utility' and call_function in ['batch', 'as_derivative', 'batch_all', 'force_batch']:
            block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
            subgraph = Utils.merge_subgraph(subgraph, block_transaction_relationship)

        """
        Similarly to the batch calls we treat the individual proxy calls as separate transactions and connect them
        to the proxy function node
        """
        if call_module == 'Proxy' and call_function == 'proxy':  # todo: handle proxy extrinsics
            transaction_structure = dict()
            transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
            transaction_structure['address'] = transaction_data['address']
            transaction_structure['call'] = transaction_data['call']['call_args'][2]['value']
            subgraph = Transaction.create(block=block,
                                          transaction_data=transaction_structure,
                                          event_data=event_data,
                                          proxy_transaction=transaction,
                                          subgraph=subgraph)
            # todo: connect with proxy call

        if proxy_transaction is not None:
            transaction_proxy_relationship = Relationship(transaction, "IS_PROXY", proxy_transaction)
            block_transaction_relationship = Relationship(block, "HAS_TRANSACTION", transaction)
            subgraph = Utils.merge_subgraph(subgraph, transaction_proxy_relationship, block_transaction_relationship)

        """
        Here we handle the different function calls that shift balance between accounts.
        """
        if extrinsic_function['name'] in ["transfer", "transfer_all", "transfer_keep_alive"]:

            return Transaction.handle_transfer(transaction_data=transaction_data,
                                               event_data=event_data,
                                               block=block,
                                               transaction=transaction,
                                               from_account=from_account,
                                               subgraph=subgraph)

        elif extrinsic_function['name'] in ["bond", "bond_extra"]:
            return Transaction.handle_bond(transaction_data=transaction_data,
                                           event_data=event_data,
                                           block=block,
                                           transaction=transaction,
                                           extrinsic_function=extrinsic_function,
                                           from_account=from_account,
                                           subgraph=subgraph)

        elif extrinsic_function['name'] == "set_controller":
            return Transaction.handle_set_controller(transaction_data=transaction_data,
                                                     event_data=event_data,
                                                     block=block,
                                                     transaction=transaction,
                                                     from_account=from_account,
                                                     subgraph=subgraph)

        elif extrinsic_function['name'] == "set_payee":
            return Transaction.handle_set_payee(transaction_data=transaction_data,
                                                event_data=event_data,
                                                block=block,
                                                transaction=transaction,
                                                from_account=from_account,
                                                subgraph=subgraph)

        elif extrinsic_function['name'] == "payout_stakers":
            return Transaction.handle_payout_stakers(transaction_data=transaction_data,  # todo: improve this sucks ass
                                                     event_data=event_data,
                                                     block=block,
                                                     transaction=transaction,
                                                     subgraph=subgraph,
                                                     batch_transaction=batch_transaction)
        return subgraph

    @staticmethod
    def handle_extrinsics_without_sender(call_module, call_function, subgraph, block, transaction):
        return

    @staticmethod
    def handle_transfer(transaction_data,
                        event_data,
                        block,
                        transaction,
                        from_account,
                        subgraph):

        to_account_address = Utils.convert_public_key_to_polkadot_address(
            transaction_data["call"]["call_args"][0]["value"])
        to_account = Account.get(subgraph, to_account_address)
        if not to_account:
            to_account = Account.create(to_account_address)

        amount_transferred = transaction_data['call']['call_args'][1]['value']

        transaction["amount_transferred"] = str(amount_transferred)
        fromaccount_transferto_relationship = Relationship(from_account, "TRANSFER_TO", to_account)
        # fromaccount_transferto_relationship.properties['block_number'] = block['block_number'] # todo: add property
        subgraph = Utils.merge_subgraph(subgraph, fromaccount_transferto_relationship, from_account, to_account,
                                        Transaction.finish_transaction(block, transaction))
        return subgraph

    @staticmethod
    def handle_set_controller(transaction_data,
                              event_data,
                              block,
                              transaction,
                              from_account,
                              subgraph):

        controller_address = Utils.convert_public_key_to_polkadot_address(
            transaction_data["call"]["call_args"][0]["value"])
        controller_account = Account.get(subgraph, controller_address)
        if not controller_account:
            controller_account = Account.create(controller_address)
        controller_account_relationship = Relationship(controller_account, "CONTROLS", from_account)

        amount_transferred = 0
        transaction["amount_transferred"] = str(amount_transferred)

        return Utils.merge_subgraph(subgraph, from_account, controller_account,
                                    Transaction.finish_transaction(block, transaction), controller_account_relationship)

    @staticmethod
    def handle_bond(transaction_data,
                    event_data,
                    block,
                    transaction,
                    extrinsic_function,
                    from_account,
                    subgraph):

        if extrinsic_function['name'] == "bond":
            amount_transferred = str(transaction_data["call"]["call_args"][1]["value"])

            controller_address = Utils.convert_public_key_to_polkadot_address(
                transaction_data["call"]["call_args"][0]["value"])
            reward_destination = transaction_data["call"]["call_args"][2]["value"]
            if "Account" in reward_destination:
                reward_destination = reward_destination["Account"]
            if controller_address != Utils.convert_public_key_to_polkadot_address(transaction_data["address"]):
                controller_account = Account.get(subgraph, controller_address)
            else:
                controller_account = from_account
            if not controller_account:
                controller_account = Account.create(controller_address)
            controlleraccount_fromaccount_relationship = Relationship(controller_account, "CONTROLS", from_account)
            subgraph = Utils.merge_subgraph(subgraph, controlleraccount_fromaccount_relationship)
            controller_account["reward_destination"] = reward_destination

        elif extrinsic_function['name'] == "bond_extra":
            amount_transferred = str(transaction_data["call"]["call_args"][0]["value"])
            controller_account = None
        else:
            raise NotImplementedError(extrinsic_function.name)

        transaction["amount_transferred"] = amount_transferred

        Account.save(from_account)
        if controller_account is not None:
            subgraph = Utils.merge_subgraph(subgraph, controller_account)
        # controller is the same as from account, else everything updated gets overwritten in update balance.

        return Utils.merge_subgraph(subgraph, from_account, Transaction.finish_transaction(block, transaction))

    @staticmethod
    def pay_fees(event_data,
                 block,
                 transaction,
                 from_account,
                 to_account,
                 amount_transferred,
                 extrinsic_function_name,
                 length_transaction,
                 author_account,
                 transfer,
                 treasury_account):
        """
        This function handles the settlement of transaction fees (validator and treasury).
        There exist some blocks where there are no fees. (i.e. first blocks of era)
        """

        validator_fee = int(Utils.extract_event_attributes(event_data[-2], False) / length_transaction)
        try:
            treasury_fee = int(Utils.extract_event_attributes(event_data[-3], True) / length_transaction)
        except IndexError:
            treasury_fee = 0
        treasury_account.update_balance(transferable=treasury_fee)
        transaction.reward_treasury.add(treasury_account.get_current_balance())
        author_account.update_balance(transferable=validator_fee)
        if validator_fee + treasury_fee:
            transaction.reward_validator.add(author_account.get_current_balance())
        total_fee = int((validator_fee + treasury_fee) / length_transaction)
        if extrinsic_function_name in ['bond', 'bond_extra']:
            from_account.update_balance(transferable=-(amount_transferred + total_fee),
                                        bonded=amount_transferred)
        else:
            if from_account != to_account and to_account is not None and transfer:
                to_account.update_balance(transferable=+amount_transferred)
                from_account.update_balance(block.block_number, to_account,
                                            transferable=-(amount_transferred + total_fee))
            else:
                from_account.update_balance(transferable=-(amount_transferred + total_fee))
        if extrinsic_function_name in ["transfer", "transfer_all", "transfer_keep_alive"] and transaction.is_successful:
            transaction.from_balance.add(from_account.get_current_balance())
            transaction.to_balance.add(to_account.get_current_balance())
        return transaction, author_account, treasury_account, from_account, to_account

    @staticmethod
    def handle_set_payee(transaction_data,
                         event_data,
                         block,
                         transaction,
                         from_account,
                         subgraph):
        reward_destination = transaction_data['call']['call_args'][0]['value']
        if isinstance(reward_destination, Dict):
            reward_destination = reward_destination['Account']
        from_account["reward_destination"] = reward_destination

        Account.save(from_account)
        return Utils.merge_subgraph(subgraph, from_account, Transaction.finish_transaction(block, transaction))

    @staticmethod
    def handle_payout_stakers(transaction_data,
                              event_data,
                              block,
                              transaction,
                              subgraph,
                              batch_transaction):
        """
        handles Staking(Reward) event by creating a nominator node, checking their payout preferences
        (reward_destination) adjusting their transferable/bonded balance respectively.
        We check whether the nominator receiving the reward is the same address as the validator in order to avoid
        creating a nominator node for a validator.
        """
        validator_stash = transaction_data['call']['call_args'][0]['value']
        author_account = Account.get(subgraph, validator_stash)
        if author_account is None:
            author_account = Account.create(validator_stash)
        validator = Validator.get_from_account(author_account)
        if validator is None:
            validator, account_validator_relationship = Validator.create(amount_staked=0, self_staked=0,
                                                                         nominator_staked=0,
                                                                         account=author_account)
            subgraph = Utils.merge_subgraph(subgraph, validator, account_validator_relationship)

        for event in event_data:
            if event['event_id'] == 'Reward':
                nominator_reward = event['attributes'][1]['value']
                nominator_address = event['attributes'][0]['value']
                nominator_account = Account.get(subgraph, nominator_address)
                if nominator_account is None:
                    nominator_account = Account.create(nominator_address)
                nominator = Nominator.get_from_account(nominator_account)
                if nominator is None:
                    nominator, account_nominator_relationship = Nominator.create(total_staked=0, reward=0,
                                                                                 account=nominator_account)
                    subgraph = Utils.merge_subgraph(subgraph, nominator, account_nominator_relationship)
                nominator['reward'] = nominator_reward
                validator_nominator_relationship = Relationship(validator, "HAS_NOMINATOR", nominator)
                subgraph = Utils.merge_subgraph(subgraph, nominator, validator,
                                                validator_nominator_relationship, nominator_account)

        return Utils.merge_subgraph(subgraph, Transaction.finish_transaction(block, transaction))

    @staticmethod
    def handle_tip(transaction_data, event_data, block, transaction):
        from_address = Utils.convert_public_key_to_polkadot_address(transaction_data["address"])
        from_account = Account.get(from_address)
        if from_account is None:
            from_account = Account.create(from_address)
        to_address = Utils.convert_public_key_to_polkadot_address(transaction_data["call"]["call_args"][0]["value"])
        to_account = Account.get(to_address)
        if not to_account:
            to_account = Account.create(to_address)
        amount_transferred = transaction_data['call']['call_args'][1]['value']
        transaction.amount_transferred = str(amount_transferred)
        return transaction, from_account, to_account, amount_transferred

    @staticmethod
    def handle_move_to_reserved(transaction_data, event_data, block, transaction):
        from_address = Utils.convert_public_key_to_polkadot_address(transaction_data['address'])
        from_account = Account.get(from_address)
        if from_account is None:
            from_account = Account.create(from_address)
        amount_moved_to_reserved = transaction_data['call']['call_args'][0]['value']

        from_account.update_balance(transferable=-amount_moved_to_reserved, reserved=amount_moved_to_reserved)
        amount_transferred = 0
        return transaction, from_account, from_account, amount_transferred

    @staticmethod
    def handle_claim(transaction_data, event_data):
        polkadot_address = transaction_data['call']['call_args'][0]['value']
        polkadot_address_clean = Utils.convert_public_key_to_polkadot_address(polkadot_address)
        polkadot_account = Account.get(polkadot_address_clean)
        if polkadot_account is None:
            polkadot_account = Account.create(polkadot_address_clean)
        amount_claimed = event_data[-2]['attributes'][2]['value']
        polkadot_account.update_balance(transferable=amount_claimed)
        return polkadot_account


class ExtrinsicFunction(GraphObject):
    __primarykey__ = "name"
    name = Property()
    has_module = RelatedTo("ExtrinsicModule")

    @staticmethod
    @profiler("ExtrinsicFunction")
    def get(function_name, subgraph):
        for node in subgraph.nodes:
            if node.has_label('ExtrinsicFunction'):
                if node['name'] == function_name:
                    return node
        extrinsic_function = Driver().get_driver().graph.run(
            "Match (n:ExtrinsicFunction {name: '" + str(function_name) + "'}) return n").evaluate()
        return extrinsic_function

    @staticmethod
    def create(function_name: str):
        extrinsic_function = Node("ExtrinsicFunction",
                                  name=function_name
                                  )
        return extrinsic_function

    @staticmethod
    def save(extrinsic_function: "ExtrinsicFunction"):
        Driver().get_driver().save(extrinsic_function)


class ExtrinsicModule(GraphObject):
    __primarykey__ = "name"

    name = Property()
    has_function = RelatedTo("ExtrinsicFunction")

    @staticmethod
    @profiler("ExtrinsicModule")
    def get(name, subgraph):
        for node in subgraph.nodes:
            if node.has_label('ExtrinsicModule'):
                if node['name'] == name:
                    return node
        extrinsic_module = Driver().get_driver().graph.run(
            "Match (n:ExtrinsicModule {name: '" + str(name) + "'}) return n").evaluate()
        return extrinsic_module

    @staticmethod
    def create(module_name: str) -> Node:
        extrinsic_module = Node("ExtrinsicModule",
                                name=module_name,
                                )
        return extrinsic_module

    @staticmethod
    def save(extrinsic_module: "ExtrinsicModule"):
        Driver().get_driver().save(extrinsic_module)


class EventFunction(GraphObject):
    __primarykey__ = "name"

    name = Property()


class EventModule(GraphObject):
    __primarykey__ = "name"

    name = Property()
    has_function = RelatedTo("EventFunction")


class TransferDenomination(GraphObject):
    __primarykey__ = "name"

    name = Property()


#### Accounts and Balances
class Account(GraphObject):
    __primarykey__ = "address"

    address = Property()
    account_index = Property()
    nonce = Property()
    reward_destination = Property()

    transfer_to = RelatedTo("Account")
    controls = RelatedTo("Account")
    is_validator = RelatedTo("Validator")
    is_nominator = RelatedTo("Nominator")

    @staticmethod
    def create(address: str):
        account = Node("Account",
                       address=address
                       )
        return account

    @staticmethod
    @profiler("Account")
    def get(subgraph, address: str):
        for node in subgraph.nodes:
            if node.has_label('Account'):
                if node['address'] == address:
                    return node
        account = Driver().get_driver().graph.run(
            "Match (n:Account {address: '" + str(address) + "'}) return n").evaluate()

        return account

    @staticmethod
    def save(account: "Account"):
        Driver().get_driver().save(account)

    @staticmethod
    @profiler("Account")
    def get_treasury():
        treasury = Driver().get_driver().graph.run(
            "Match (n:Account {address: " + str(treasury_address) + "}) return n").evaluate()
        if not treasury:
            treasury = Account.create(treasury_address)
        return treasury


class ValidatorPool(GraphObject):
    __primarykey__ = "era"

    era = Property()
    validator_payout = Property()
    treasury_payout = Property()
    total_staked = Property()

    block_number = RelatedTo("Block")
    previous_validator_pool = RelatedTo("ValidatorPool")
    hasValidators = RelatedTo("Validator")


    @staticmethod
    @profiler("ValidatorPool")
    def get(era):
        query = "Match (v:ValidatorPool{era:x}) return v"
        query = query.replace("x", str(era))
        result = Driver().get_driver().graph.run(query).evaluate()
        return result

    @staticmethod
    def create(event,block:"Block"):
        try:
            validator_pool =\
                                Node("ValidatorPool",
                                era=event['attributes'][0]["value"],
                                validator_payout=event['attributes'][1]["value"],
                                treasury_payout=event['attributes'][2]["value"],
                                block_number=block['block_number']
                                )
        except (IndexError, TypeError):
            validator_pool = ValidatorPool(
                era = event['attributes'][0],
                validator_payout = event['attributes'][1],
                treasury_payout = event['attributes'][2],
                block_number = block['block_number']
            )
        return validator_pool


class Validator(GraphObject):
    __primarykey__ = "era"


    account = RelatedFrom("Account", "IS_VALIDATOR")
    era = Property()
    reward_points = Property()
    total_stake = Property()
    own_stake = Property()
    commission = Property()

    has_nominator = RelatedTo("Nominator")


    @staticmethod
    @profiler("Validator")
    def get_account_from_validator(validator):
        print(validator.account.triples())

    @staticmethod
    @profiler("Validator")
    def get_from_account(account: "Account") -> "Validator":
        return Driver().get_driver().graph.run(
            "Match (v:Validator)<-[:IS_VALIDATOR]-(a:Account {address: '" + str(
                account['address']) + "'}) return v").evaluate()


    @staticmethod
    def create(validator_account, current_validatorpool=None, reward_points=None,
                                         validator_staking=None,  commission=None):

        if current_validatorpool is None:
            validator = Node("Validator",
                        )
            return validator

        validator = Node("Validator",
                         era=current_validatorpool['era'],
                         total_stake=validator_staking["total"],
                         own_stake=validator_staking["own"],
                         commission=commission["commission"],
                         reward_points=reward_points
                         )
        account_validator_relationship = Relationship(validator_account, "IS_VALIDATOR", validator)
        return validator, account_validator_relationship


class Nominator(GraphObject):
    total_staked = Property()
    reward = Property()

    @staticmethod
    @profiler("Nominator")
    def get_from_account(account: "Account") -> "Nominator":
        return Driver().get_driver().graph.run(
            "Match (n:Nominator)<-[:IS_NOMINATOR]-(a:Account {address: '" + str(
                account['address']) + "'}) return n").evaluate()

    @staticmethod
    def create(nominator_account, nominator_stake):
        nominator = Node("Nominator",
                         total_staked=nominator_stake
                         )
        account_nominator_relationship = Relationship(nominator_account, "IS_NOMINATOR", nominator)
        return nominator, account_nominator_relationship
