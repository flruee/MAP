from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom, RelatedObjects
from src.driver_singleton import Driver
from typing import Dict
from substrateinterface.utils import ss58
Base = declarative_base()
"""
Block
"""

treasury_address = "13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB"


class RawData(Base):
    __tablename__ = "raw_data"
    block_number = Column(Integer, primary_key=True)
    data = Column(JSON)

    def __repr__(self):
        return f"Block {self.block_number}"

class Utils:
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
        block = Block(
            block_number=data["number"],
            hash=data["hash"],
            timestamp=timestamp,
        )
        return block


class Transaction(GraphObject):
    extrinsic_hash = Property()
    amount_transferred = Property()
    is_successful = Property()

    has_extrinsic_function = RelatedTo("ExtrinsicFunction")
    has_event_function = RelatedTo("EventFunction")
    from_balance = RelatedTo("Balance")
    to_balance = RelatedTo("Balance")
    reward_validator = RelatedTo("Balance")
    reward_treasury = RelatedTo("Balance")
    sender_account = RelatedTo("Account")
    is_proxy = RelatedTo("Transaction")
    is_batch = RelatedTo("Transaction")

    @staticmethod
    def create(block,
               transaction_data,
               event_data,
               author_account,
               validator,
               treasury_account,
               length_transaction=1,
               proxy_transaction=None,
               batch_transaction=None,
               batch_from_account=None):

        tx = Driver().get_driver().graph.begin()
        call_function           = transaction_data["call"]["call_function"]
        call_module             = transaction_data["call"]["call_module"]
        #print(call_module, call_function)
        transaction             = Transaction(extrinsic_hash=transaction_data["extrinsic_hash"])
        extrinsic_function      = ExtrinsicFunction.get(call_function)

        if not extrinsic_function:
            extrinsic_function = ExtrinsicFunction.create(call_function, call_module)

        transaction.has_extrinsic_function.add(extrinsic_function)


        if call_module in ['FinalityTracker', 'Parachains', 'ParaInherent', 'ImOnline',
                            'ElectionProviderMultiPhase', 'Timestamp', 'Council']:
            """
            Simply return transaction since no balance shift takes place in these modules.
            """
            block.has_transaction.add(transaction)
            from_account = None
            to_account = None
            nodes = [transaction, block, extrinsic_function,  validator, treasury_account, from_account, to_account]
            no_none_nodes = [node for node in nodes if node is not None]
            for node in no_none_nodes:
                print(node)
                tx.create(node)
            tx.commit()


        if call_module == 'Claims':
            return
            sender_account = Transaction.handle_claim(transaction_data, event_data)
            transaction.sender_account.add(sender_account)
            block.has_transaction.add(transaction)
            #tx.create(block)
            #tx.create(transaction)
            nodes = [transaction, block, extrinsic_function,  validator, treasury_account, from_account, to_account]
            no_none_nodes = [node for node in nodes if node is not None]
            for node in no_none_nodes:
                tx.create(node)
            tx.commit()
        """
        For batch calls we handle the individual extrinsics as seperate transactions. The fee paid is split up evenly
        between the individual calls.
        """
        if call_module == 'Utility' and call_function in ['batch', 'as_derivative', 'batch_all', 'force_batch']:
            from_account_address = transaction_data['address']
            from_account = Account.get(from_account_address)
            if from_account is None:
                from_account = Account.create(from_account_address)
            for transaction_batch in transaction_data['call']['call_args'][0]['value']:
                transaction_structure = dict()
                transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
                transaction_structure['address'] = transaction_data['address']
                transaction_structure['call'] = transaction_batch

                Transaction.create(block=block,
                                   transaction_data=transaction_structure,
                                   event_data=event_data,
                                   author_account=author_account,
                                   validator=validator,
                                   treasury_account=treasury_account,
                                   length_transaction=len(transaction_data['call']['call_args'][0]['value']),
                                   batch_transaction=transaction,
                                   batch_from_account=from_account)
        """
        Get account which triggered the transaction and set initial values of variables required for further processing
        """
        from_account_address = Utils.convert_public_key_to_polkadot_address(transaction_data['address'])
        if batch_from_account is None:
            #print(f'batch is None so this is adddress: {from_account_address}')
            from_account = Account.get(from_account_address)
            if from_account is None:
                from_account = Account.create(from_account_address)
        else:
            from_account = batch_from_account
        transaction.sender_account.add(from_account)
        to_account = None
        amount_transferred = 0


        """
        Handle Extrinsics which failed. They are required to pay fees regardless of outcome.
        """
        if event_data[-1]["event_id"] != "ExtrinsicSuccess":
            transaction.is_successful = False
            transfer = False
            transaction, validator_account, treasury_account, from_account, to_account = \
                Transaction.pay_fees(event_data=event_data,
                                     block=block,
                                     transaction=transaction,
                                     from_account=from_account,
                                     to_account=to_account,
                                     amount_transferred=amount_transferred,
                                     extrinsic_function_name=extrinsic_function.name,
                                     length_transaction=length_transaction,
                                     author_account=author_account,
                                     transfer=transfer,
                                     treasury_account=treasury_account)

            block.has_transaction.add(transaction)
            nodes = [transaction, block, extrinsic_function,  validator, treasury_account, from_account, to_account]
            no_none_nodes = [node for node in nodes if node is not None]
            for node in no_none_nodes:
                tx.create(node)
            tx.commit()
        transaction.is_successful = True


        if batch_transaction is not None:
            transaction.is_batch.add(batch_transaction)
        """
        Lastly we make a separate batch node which we connect to the individual call
        """
        if call_module == 'Utility' and call_function in ['batch', 'as_derivative', 'batch_all', 'force_batch']:
            block.has_transaction.add(transaction)
            return transaction, block, extrinsic_function,  validator, treasury_account, from_account, to_account

        """
        Similarly to the batch calls we treat the individual proxy calls as separate transactions and connect them
        to the proxy function node
        """
        if call_module == 'Proxy' and call_function == 'proxy': # todo: handle proxy extrinsics
            transaction_structure = dict()
            transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
            transaction_structure['address'] = transaction_data['address']
            transaction_structure['call'] = transaction_data['call']['call_args'][2]['value']
            Transaction.create(block=block,
                               transaction_data=transaction_structure,
                               event_data=event_data,
                               author_account=author_account,
                               validator=validator,
                               proxy_transaction=transaction)
            # todo: connect with proxy call
            nodes = [transaction, block, extrinsic_function,  validator, treasury_account, from_account, to_account]
            no_none_nodes = [node for node in nodes if node is not None]
            for node in no_none_nodes:
                tx.create(node)
            tx.commit()

        if proxy_transaction is not None:
            transaction.is_proxy.add(proxy_transaction)
            block.has_transaction.add(transaction)


        """
        Here we handle the different function calls that shift balance between accounts.
        """
        transfer = False
        if extrinsic_function.name in ["transfer", "transfer_all", "transfer_keep_alive"]:
            transaction, from_account, to_account, amount_transferred, transfer = \
                Transaction.handle_transfer(transaction_data=transaction_data,
                                            event_data=event_data,
                                            block=block,
                                            transaction=transaction,
                                            from_account=from_account)

        elif extrinsic_function.name in ["bond", "bond_extra"]:
            transaction, from_account, controller_account, amount_transferred, transfer= \
                Transaction.handle_bond(transaction_data=transaction_data,
                                        event_data=event_data,
                                        block=block,
                                        transaction=transaction,
                                        extrinsic_function=extrinsic_function,
                                        from_account=from_account)

        elif extrinsic_function.name == "set_controller":
            transaction, from_account, controller_account, amount_transferred, transfer = \
                Transaction.handle_set_controller(transaction_data=transaction_data,
                                                  event_data=event_data,
                                                  block=block,
                                                  transaction=transaction,
                                                  from_account=from_account)

        elif extrinsic_function.name == "set_payee":
            transaction, from_account, to_account, amount_transferred, transfer = \
                Transaction.handle_set_payee(transaction_data=transaction_data,
                                             event_data=event_data,
                                             block=block,
                                             transaction=transaction,
                                             from_account=from_account)

        elif extrinsic_function.name == "payout_stakers":
            transaction, from_account, to_account, amount_transferred, transfer = \
                Transaction.handle_payout_stakers(transaction_data=transaction_data,
                                                  event_data=event_data,
                                                  block=block,
                                                  transaction=transaction)

        elif extrinsic_function.name == "propose_spend": # todo: handle treasury extrinsics
            return transaction, block, extrinsic_function

        """
        pay fees
        """
        transaction, validator_account, treasury_account, from_account, to_account = \
            Transaction.pay_fees(event_data=event_data,
                                 block=block,
                                 transaction=transaction,
                                 from_account=from_account,
                                 to_account=to_account,
                                 amount_transferred=amount_transferred,
                                 extrinsic_function_name=extrinsic_function.name,
                                 length_transaction=length_transaction,
                                 author_account=author_account,
                                 transfer=transfer,
                                 treasury_account=treasury_account)
        block.has_transaction.add(transaction)
        nodes = [transaction, block, extrinsic_function, validator, treasury_account, from_account, to_account]
        no_none_nodes = [node for node in nodes if node is not None]
        for node in no_none_nodes:
            tx.create(node)
        tx.commit()


    @staticmethod
    def handle_transfer(transaction_data,
                        event_data,
                        block,
                        transaction,
                        from_account):

        to_account_address = Utils.convert_public_key_to_polkadot_address(transaction_data["call"]["call_args"][0]["value"])
        to_account = Account.get(to_account_address)
        if not to_account:
            to_account = Account.create(to_account_address)

        amount_transferred = transaction_data['call']['call_args'][1]['value']

        transaction.amount_transferred = amount_transferred
        transfer = True
        return transaction, from_account, to_account, amount_transferred, transfer

    @staticmethod
    def handle_set_controller(transaction_data,
                              event_data,
                              block,
                              transaction,
                              from_account):

        controller_address = Utils.convert_public_key_to_polkadot_address(
                                transaction_data["call"]["call_args"][0]["value"])
        controller_account = Account.get(controller_address)
        if not controller_account:
            controller_account = Account.create(controller_address)
        controller_account.controls.add(from_account)
        #tx.create(controller_account)

        amount_transferred = 0
        transaction.amount_transferred = amount_transferred
        transfer = False
        return transaction, from_account, controller_account, amount_transferred, transfer

    @staticmethod
    def handle_bond(transaction_data,
                    event_data,
                    block,
                    transaction,
                    extrinsic_function,
                    from_account):

        if extrinsic_function.name == "bond":
            amount_transferred = transaction_data["call"]["call_args"][1]["value"]

            controller_address = Utils.convert_public_key_to_polkadot_address(
                transaction_data["call"]["call_args"][0]["value"])
            reward_destination = transaction_data["call"]["call_args"][2]["value"]
            if "Account" in reward_destination:
                reward_destination = reward_destination["Account"]
            if controller_address != Utils.convert_public_key_to_polkadot_address(transaction_data["address"]):
                controller_account = Account.get(controller_address)
            else:
                controller_account = from_account
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            controller_account.reward_destination = reward_destination
            #tx.create(controller_account)
            from_account = controller_account
        elif extrinsic_function.name == "bond_extra":
            amount_transferred = transaction_data["call"]["call_args"][0]["value"]
            controller_account = None
        else:
            raise NotImplementedError(extrinsic_function.name)

        transaction.amount_transferred = amount_transferred
        transfer = False
        # controller is the same as from account, else everything updated gets overwritten in update balance.
        return transaction, from_account, controller_account, amount_transferred, transfer


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
        if validator_fee+treasury_fee:
            transaction.reward_validator.add(author_account.get_current_balance())
        total_fee = int((validator_fee+treasury_fee) / length_transaction)
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
                         from_account):
        reward_destination = transaction_data['call']['call_args'][0]['value']
        if isinstance(reward_destination, Dict):
            reward_destination = reward_destination['Account']
        from_account.reward_destination = reward_destination
        #tx.create(from_account)
        amount_transferred = 0
        transfer = False
        return transaction, from_account, from_account, amount_transferred, transfer

    @staticmethod
    def handle_payout_stakers(transaction_data,
                              event_data,
                              block,
                              transaction):
        # todo: involve tx
        """
        handles Staking(Reward) event by creating a nominator node, checking their payout preferences (reward_destination)
        adjusting their transferable/bonded balance respectively.
        We check whether or not the nominator receiving the reward is the same address as the validator in order to avoid
        creating a nominator node for a validator.
        """
        validator_stash = transaction_data['call']['call_args'][0]['value']
        author_account = Account.get(validator_stash)
        if not author_account:
            author_account = Account.create(validator_stash)
        validator = Validator.get_from_account(author_account)
        if not validator:
            validator = Validator.create(author_account)
        for event in event_data:
            if event['event_id'] == 'Reward':
                nominator_reward = event['attributes'][1]['value']
                nominator_address = event['attributes'][0]['value']
                if nominator_address == validator_stash:
                    if author_account.reward_destination in [None, 'Stash', 'Controller', 'Account']:
                        author_account.update_balance(transferable=nominator_reward)
                    elif author_account.reward_destination in ['Staked']:
                        author_account.update_balance(bonded=nominator_reward)
                    continue
                nominator_account = Account.get(nominator_address)
                if nominator_account is None:
                    nominator_account = Account.create(nominator_address)
                if nominator_account.reward_destination in [None, 'Stash', 'Controller', 'Account']:
                    nominator_account.update_balance(transferable=nominator_reward)
                elif nominator_account.reward_destination in ['Staked']:
                    nominator_account.update_balance(bonded=nominator_account)
                nominator = Nominator.get_from_account(nominator_account)
                nominator_account.is_nominator.add(nominator)
                repository = Driver().get_driver()
                #repository.merge(nominator_account)
                nominator.reward = nominator_reward
                #repository.merge(nominator)
                validator.has_nominator.add(nominator)
                #repository.merge(validator)

        amount_transferred = 0
        from_account_address = transaction_data['address']
        from_account = Account.get(from_account_address)
        if from_account is None:
            from_account = Account.create(from_account_address)
        transfer = False
        return transaction, from_account, from_account, amount_transferred, transfer

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
        transaction.amount_transferred = amount_transferred
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
    def get(name):
        return ExtrinsicFunction.match(Driver().get_driver(), name).first()

    @staticmethod
    def create(function_name: str, module_name) -> "ExtrinsicFunction":
        extrinsic_function = ExtrinsicFunction(
                name=function_name
                )
        extrinsic_module = ExtrinsicModule.get(module_name)
        if not extrinsic_module:
            extrinsic_module = ExtrinsicModule.create(module_name)
        extrinsic_function.has_module.add(extrinsic_module)
        #Driver().get_driver().merge(extrinsic_function)
        return extrinsic_function


class ExtrinsicModule(GraphObject):
    __primarykey__ = "name"

    name = Property()


    @staticmethod
    def get(name):
        return ExtrinsicModule.match(Driver().get_driver(), name).first()

    @staticmethod
    def create(module_name: str) -> "ExtrinsicModule":
        extrinsic_module = ExtrinsicModule(
                name=module_name,
                )
        #Driver().get_driver().merge(extrinsic_module)
        return extrinsic_module



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

    has_balances = RelatedTo("Balance")
    current_balance = RelatedTo("Balance")
    transfer_to = RelatedTo("Account")
    controls = RelatedTo("Account")
    is_validator = RelatedTo("Validator")
    is_nominator = RelatedTo("Nominator")


    def get_current_balance(self):
        triples = list(self.current_balance.triples())
        balance = triples[0][-1]
        return balance


    @staticmethod
    def create(address: str):
        account = Account(
            address=address
        )
        null_balance = Balance.create(0,0,0,0)
        account.has_balances.add(null_balance)
        account.current_balance.add(null_balance)
        return account

    @staticmethod
    def get(address: str):
        result = Account.match(Driver().get_driver(), primary_value=address).first()
        print(f'this is what i found: {result} for this address: {address}')
        return Account.match(Driver().get_driver(), primary_value=address).first()

    
    @staticmethod
    def get_treasury():
        treasury = Account.match(Driver().get_driver(), treasury_address).first()
        if not treasury:
            treasury = Account.create(treasury_address)
        return treasury


    def update_balance(self,
                       block_number=None,
                       other_account: "Account"=None,
                       transferable=0,
                       reserved=0,
                       bonded=0,
                       unbonding=0):

        current_balance= self.get_current_balance()
        current_balance.transferable += transferable
        current_balance.reserved += reserved
        current_balance.bonded += bonded
        current_balance.unbonding += unbonding

        from_balance = Balance.createFromObject(current_balance, current_balance)
        self.has_balances.add(from_balance)
        self.current_balance.remove(current_balance)
        self.current_balance.add(from_balance)

        if other_account is not None and block_number is not None:
            self.transfer_to.add(other_account, {"block_number": block_number})
        tx = Driver().get_driver().graph.begin()
        tx.create(self)
        tx.commit()
        #tx.create(self)

class Balance(GraphObject):
    __tablename__ = "balance"

    transferable = Property()
    reserved = Property()
    bonded = Property()
    unbonding = Property()

    previous_balance = RelatedTo("Balance")

    @staticmethod
    def create(transferable:int, reserved:int, bonded:int, unbonding:int, previous_balance:"Balance"=None) -> "Balance":
        balance = Balance(
            transferable=transferable,
            reserved=reserved,
            bonded=bonded,
            unbonding=unbonding
        )
        if previous_balance:
            balance.previous_balance.add(previous_balance)

        return balance

    @staticmethod
    def createFromObject(balance: "Balance", previous_balance) -> "Balance":
        
        return Balance.create(balance.transferable, balance.reserved, balance.bonded, balance.unbonding, previous_balance)


class ValidatorPool(GraphObject):
    __primarykey__ = "era"

    era = Property()
    total_staked = Property()
    total_reward = Property()

    hasValidators = RelatedTo("Validator")
    from_block = RelatedTo("Block")
    to_block = RelatedTo("Block")
    previous_validator_pool = RelatedTo("ValidatorPool")

    @staticmethod
    def get(era):
        return ValidatorPool.match(Driver().get_driver(), era).first()

    @staticmethod
    def create(era, block, total_staked=0, total_reward=0):
        validatorpool = ValidatorPool(
            era=era,
            total_staked=total_staked,
            total_reward=total_reward
        )
        validatorpool.from_block.add(block)
        Driver().ge#t_driver().merge(validatorpool)
        return validatorpool


class Validator(GraphObject):
    amount_staked = Property()
    self_staked = Property()
    nominator_staked = Property()

    has_nominator = RelatedTo("Nominator")
    account = RelatedFrom("Account", "IS_VALIDATOR")

    @staticmethod
    def get_account_from_validator(validator):
        #res1 =  Driver().get_driver().run("Match (v:Validator)<-[:IS_VALIDATOR]-(a:Account {address: '"+str(account.address)+"'}) return a")
        print(validator.account.triples())

    @staticmethod
    def get_from_account(account: "Account") -> "Validator":

        validator_list = list(account.is_validator.triples())
        
        if not len(validator_list):
            validator = Validator.create(account=account)
        else:
            validator = validator_list[0][-1]
        return validator
        
    @staticmethod
    def create(amount_staked=0, self_staked=0, nominator_staked=0, account:"Account"=None):
        validator = Validator(
            amount_staked=amount_staked,
            self_staked=self_staked,
            nominator_staked=nominator_staked
        )
        account.is_validator.add(validator)
        #tx.create(validator)
        return validator
        

class Nominator(GraphObject):
    total_staked = Property()
    reward = Property()

    @staticmethod
    def get_from_account(account: "Account") -> "Nominator":
        nominator_list = list(account.is_nominator.triples())
        if not len(nominator_list):
            nominator = Nominator.create(account=account)
        else:
            nominator = nominator_list[0][-1]
        return nominator

    @staticmethod
    def create(total_staked=0, reward=0, account:"Account"=None):
        nominator = Nominator(
            total_staked=total_staked,
            reward=reward
        )
        repository = Driver().get_driver()
        #repository.merge(nominator)
        account.is_nominator.add(nominator)
        #repository.merge(account)
        return nominator

