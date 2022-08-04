from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
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
        if address[0] == '1':
            return address
        return ss58.ss58_encode(ss58_format=0, address=address)


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

    @staticmethod
    def save(block: "Block"):
        Driver().get_driver().save(block)


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
    def create(block: Block, transaction_data, event_data, length_transaction=1,
               proxy_transaction=None, batch_transaction=None) -> "Transaction":
        transaction = Transaction(
            extrinsic_hash=transaction_data["extrinsic_hash"]
        )
        extrinsic_function = ExtrinsicFunction.get(transaction_data["call"]["call_function"])
        if not extrinsic_function:
            extrinsic_function = ExtrinsicFunction.create(transaction_data["call"]["call_function"],
                                                          transaction_data["call"]["call_module"])

        transaction.has_extrinsic_function.add(extrinsic_function)
        from_account_address = transaction_data['address']
        from_account = Account.get(from_account_address)
        if from_account is None:
            from_account = Account.create(from_account_address)
        transaction.sender_account.add(from_account)
        to_account = None
        amount_transferred = 0
        if event_data[-1]["event_id"] != "ExtrinsicSuccess":
            transaction.is_successful = False
            Transaction.pay_fees(event_data, block, transaction, from_account, to_account, amount_transferred,
                                 extrinsic_function.name, length_transaction)
            Transaction.save(transaction)
            block.has_transaction.add(transaction)
            Block.save(block)
            return transaction
        transaction.is_successful = True
        if transaction_data['call']['call_module'] in ['FinalityTracker', 'Parachains']:
            return transaction
        if transaction_data['call']['call_module'] == 'Utility' and transaction_data['call']['call_function'] == 'batch':
            for transaction_batch in transaction_data['call']['call_args'][0]['value']:
                transaction_structure = dict()
                transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
                transaction_structure['address'] = transaction_data['address']
                transaction_structure['call'] = transaction_batch
                Transaction.create(block, transaction_structure, event_data,
                                   len(transaction_data['call']['call_args'][0]['value']), batch_transaction=transaction)

        if batch_transaction is not None:
            transaction.is_batch.add(batch_transaction)
        if transaction_data['call']['call_module'] == 'Utility' and transaction_data['call']['call_function'] == 'batch':
            Transaction.save(transaction)
            block.has_transaction.add(transaction)
            Block.save(block)
            return transaction

        if transaction_data['call']['call_module'] == 'Proxy' and transaction_data['call']['call_function'] == 'proxy':
            transaction_structure = dict()
            transaction_structure['extrinsic_hash'] = transaction_data['extrinsic_hash']
            transaction_structure['address'] = transaction_data['address']
            transaction_structure['call'] = transaction_data['call']['call_args'][2]['value']
            Transaction.create(block, transaction_structure, event_data, proxy_transaction=transaction)
            # todo: connect with proxy call
            return transaction

        if proxy_transaction is not None:
            transaction.is_proxy.add(proxy_transaction)

        if extrinsic_function.name in ["transfer", "transfer_all", "transfer_keep_alive"]:
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_transfer(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name in ["bond", "bond_extra"]:
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_bond(transaction_data, event_data, block, transaction, extrinsic_function)

        elif extrinsic_function.name == "set_controller":
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_set_controller(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name == "set_payee":
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_set_payee(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name == "payout_stakers":
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_payout_stakers(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name == "tip":
            transaction, from_account, to_account, amount_transferred = \
                Transaction.handle_tip(transaction_data, event_data, block, transaction)

        Transaction.pay_fees(event_data, block, transaction, from_account, to_account, amount_transferred,
                             extrinsic_function.name, length_transaction)
        Transaction.save(transaction)
        block.has_transaction.add(transaction)
        Block.save(block)
        return transaction

    @staticmethod
    def save(transaction: "Transaction"):
        Driver().get_driver().save(transaction)

    @staticmethod
    def handle_transfer(transaction_data: Dict, event_data: Dict, block: Block, transaction: "Transaction"):
        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))
        to_account = Account.get(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))

        if not to_account:
            to_account = Account.create(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))

        amount_transferred = transaction_data['call']['call_args'][1]['value']

        transaction.amount_transferred = amount_transferred
        return transaction, from_account, to_account, amount_transferred

    @staticmethod
    def handle_set_controller(transaction_data, event_data, block, transaction):
        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))
        controller_address = transaction_data["call"]["call_args"][0]["value"].replace("0x", "")
        controller_account = Account.get(controller_address)
        if not controller_account:
            controller_account = Account.create(controller_address)
        controller_account.controls.add(from_account)
        Account.save(controller_account)

        amount_transferred = 0
        transaction.amount_transferred = amount_transferred
        return transaction, from_account, from_account, amount_transferred

    @staticmethod
    def handle_bond(transaction_data: Dict, event_data: Dict, block: Block, transaction: "Transaction", extrinsic_function: "ExtrinsicFunction"):
        from_account_address = Utils.convert_public_key_to_polkadot_address(transaction_data["address"])
        from_account = Account.get(from_account_address)
        if not from_account:
            from_account = Account.create(from_account_address)

        if extrinsic_function.name == "bond":
            amount_transferred = transaction_data["call"]["call_args"][1]["value"]

            controller_address = Utils.convert_public_key_to_polkadot_address(
                transaction_data["call"]["call_args"][0]["value"])
            reward_destination = transaction_data["call"]["call_args"][2]["value"]
            if controller_address != Utils.convert_public_key_to_polkadot_address(transaction_data["address"]):
                controller_account = Account.get(controller_address)
            else:
                controller_account = from_account
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            controller_account.reward_destination = reward_destination
            Account.save(controller_account)
            from_account = controller_account
        elif extrinsic_function.name == "bond_extra":
            amount_transferred = transaction_data["call"]["call_args"][0]["value"]
        else:
            raise NotImplementedError(extrinsic_function.name)

        transaction.amount_transferred = amount_transferred
        # controller is the same as from account, else everything updated gets overwritten in update balance.
        return transaction, from_account, from_account, amount_transferred


    @staticmethod
    def pay_fees(event_data, block, transaction, from_account, to_account, amount_transferred, extrinsic_function_name,
                 length_transaction):
        """
        This function handles the settlement of transaction fees (validator and treasury).
        There exist some blocks where there are no fees. (i.e. first blocks of era)
        """
        validator_node = list(block.has_author.triples())[0][-1]
        validator_account = list(validator_node.account.triples())[0][-1]
        treasury_account = Account.get_treasury()
        try:
            validator_fee = int(event_data[-2]["attributes"][1]["value"] / length_transaction)
            treasury_fee = int(event_data[-3]["attributes"][0]["value"] / length_transaction)
            treasury_account.update_balance(transferable=treasury_fee)
            transaction.reward_treasury.add(treasury_account.get_current_balance())
        except IndexError:
            try:
                validator_fee = int(event_data[-2]["attributes"][1]["value"] / length_transaction)
                treasury_fee = 0
            except IndexError:
                validator_fee = 0
                treasury_fee = 0

        validator_account.update_balance(transferable=validator_fee)
        if validator_fee+treasury_fee:
            transaction.reward_validator.add(validator_account.get_current_balance())
        total_fee = int((validator_fee+treasury_fee) / length_transaction)
        if extrinsic_function_name in ['bond', 'bond_extra']:
            from_account.update_balance(transferable=-(amount_transferred + total_fee),
                                        bonded=amount_transferred)
        else:
            if from_account != to_account and to_account is not None:
                to_account.update_balance(transferable=+amount_transferred)
                from_account.update_balance(block.block_number, to_account,
                                            transferable=-(amount_transferred + total_fee))
            else:
                from_account.update_balance(transferable=-(amount_transferred + total_fee))
        if extrinsic_function_name in ["transfer", "transfer_all", "transfer_keep_alive"]:
            transaction.from_balance.add(from_account.get_current_balance())
            transaction.to_balance.add(to_account.get_current_balance())
        return validator_fee+treasury_fee

    @staticmethod
    def handle_set_payee(transaction_data, event_data, block, transaction):
        account_address = Utils.convert_public_key_to_polkadot_address(transaction_data["address"])
        account = Account.get(account_address)
        if not account:
            account = Account.create(account_address)
        reward_destination = transaction_data['call']['call_args'][0]['value']
        account.reward_destination = reward_destination
        Account.save(account)
        amount_transferred = 0
        return transaction, account, account, amount_transferred

    @staticmethod
    def handle_payout_stakers(transaction_data, event_data, block, transaction):
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
                Account.save(nominator_account)
                nominator.reward = nominator_reward
                Nominator.save(nominator)
                validator.has_nominator.add(nominator)
                Validator.save(validator)

        amount_transferred = 0
        from_account_address = transaction_data['address']
        from_account = Account.get(from_account_address)
        if from_account is None:
            from_account = Account.create(from_account_address)
        return transaction, from_account, from_account, amount_transferred

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




class ExtrinsicFunction(GraphObject):
    __primarykey__ = "name"
    name = Property()


    @staticmethod
    def get(name):
        return ExtrinsicFunction.match(Driver().get_driver(), name).first()

    @staticmethod
    def create(function_name: str, module_name: str) -> "ExtrinsicFunction":
        extrinsic_function = ExtrinsicFunction(
                name=function_name
                )
        extrinsic_module = ExtrinsicModule.get(module_name)
        if not extrinsic_module:
            extrinsic_module = ExtrinsicModule.create(module_name)

        extrinsic_module.has_function.add(extrinsic_function)
        ExtrinsicFunction.save(extrinsic_function)
        ExtrinsicModule.save(extrinsic_module)

        return extrinsic_function

    @staticmethod
    def save(extrinsic_function: "ExtrinsicFunction"):
        Driver().get_driver().save(extrinsic_function)

class ExtrinsicModule(GraphObject):
    __primarykey__ = "name"

    name = Property()
    has_function = RelatedTo("ExtrinsicFunction")

    @staticmethod
    def get(name):
        return ExtrinsicModule.match(Driver().get_driver(), name).first()

    @staticmethod
    def create(module_name: str) -> "ExtrinsicModule":
        extrinsic_module = ExtrinsicModule(
                name=module_name,
                )
        ExtrinsicModule.save(extrinsic_module)
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

    has_balances = RelatedTo("Balance")
    current_balance = RelatedTo("Balance")
    transfer_to = RelatedTo("Account")
    controls = RelatedTo("Account")
    is_validator = RelatedTo("Validator")
    is_nominator = RelatedTo("Nominator")


    def get_current_balance(self):
        triples = list(self.current_balance.triples())
        if not len(triples):
            balance = Balance.create(0,0,0,0)
        else:
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
        Account.save(account)
        return account

    @staticmethod
    def get(address: str):
        return Account.match(Driver().get_driver(), address).first()
    
    @staticmethod
    def save(account: "Account"):
        Driver().get_driver().save(account)
    
    @staticmethod
    def get_treasury():
        treasury = Account.match(Driver().get_driver(), treasury_address).first()
        if not treasury:
            treasury = Account.create(treasury_address)
        return treasury


    def update_balance(self, block_number=None, other_account: "Account"=None,
                       transferable=0, reserved=0, bonded=0, unbonding=0):

        last_balance = self.get_current_balance()

        last_balance.transferable += transferable
        last_balance.reserved += reserved
        last_balance.bonded += bonded
        last_balance.unbonding += unbonding



        from_balance = Balance.createFromObject(last_balance, last_balance)

        self.has_balances.add(from_balance)
        self.current_balance.remove(last_balance)
        self.current_balance.add(from_balance)

        if other_account is not None and block_number is not None:
            self.transfer_to.add(other_account, {"block_number": block_number})

        Account.save(self)

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

        Balance.save(balance)
        return balance

    @staticmethod
    def createFromObject(balance: "Balance", previous_balance) -> "Balance":
        
        return Balance.create(balance.transferable, balance.reserved, balance.bonded, balance.unbonding, previous_balance)


    @staticmethod
    def save(balance: "Balance"):
        Driver().get_driver().save(balance)


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
        ValidatorPool.save(validatorpool)
        return validatorpool

    @staticmethod
    def save(validatorpool: "ValidatorPool"):
        Driver().get_driver().save(validatorpool)


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

        Validator.save(validator)
        account.is_validator.add(validator)
        Account.save(account)
        return validator

    @staticmethod
    def save(validator: "Validator"):
        Driver().get_driver().save(validator)
        

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

        Nominator.save(nominator)
        account.is_nominator.add(nominator)
        Account.save(account)
        return nominator

    @staticmethod
    def save(nominator: "Nominator"):
        Driver().get_driver().save(nominator)
