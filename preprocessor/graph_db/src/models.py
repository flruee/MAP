
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom
from src.driver_singleton import Driver
from typing import Dict
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

###### Blocks and Transactions
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
    def save(block: "Block"):
        Driver().get_driver().save(block)


class Transaction(GraphObject):
    extrinsic_hash = Property()
    amount_transferred = Property()
    has_extrinsic_function = RelatedTo("ExtrinsicFunction")
    has_event_function = RelatedTo("EventFunction")


    from_balance = RelatedTo("Balance")
    to_balance = RelatedTo("Balance")
    reward_validator = RelatedTo("Balance")
    reward_treasury = RelatedTo("Balance")


    @staticmethod
    def create(block: Block,transaction_data, event_data) -> "Transaction":
        #transaction failed so we don't include it
        if event_data[-1]["event_id"] != "ExtrinsicSuccess":
            return None


        transaction = Transaction(
            extrinsic_hash = transaction_data["extrinsic_hash"]
        )
        extrinsic_function = ExtrinsicFunction.get(transaction_data["call"]["call_function"])
        if not extrinsic_function:
            extrinsic_function = ExtrinsicFunction.create(transaction_data["call"]["call_function"], transaction_data["call"]["call_module"])        

        transaction.has_extrinsic_function.add(extrinsic_function)

        if extrinsic_function.name in ["transfer", "transfer_all", "transfer_keep_alive"]:
            Transaction.handle_transfer(transaction_data, event_data, block, transaction)

        elif extrinsic_function.name in ["bond", "bond_extra"]:
            Transaction.handle_bond(transaction_data, event_data, block, transaction, extrinsic_function)

        elif extrinsic_function.name == "set_controller":
            from_account = Account.get(transaction_data["address"].replace("0x", ""))
            if not from_account:
                from_account = Account.create(transaction_data["address"].replace("0x", ""))

            balance = Account.get_current_balance(from_account)

            controller_address = transaction_data["call"]["call_args"][0]["value"].replace("0x", "")
            print(controller_address)
            
            controller_account = Account.get(controller_address)
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            Account.save(controller_account)

            amount_transferred = 0

            transaction.amount_transferred = amount_transferred
            fee = Transaction.pay_fees(event_data, block, transaction)


            from_account.update_balance(block.block_number, from_account, transferable=-(amount_transferred+fee) ,bonded=amount_transferred)


            transaction.from_balance.add(from_account.get_current_balance())
            transaction.to_balance.add(from_account.get_current_balance())


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

        fee = Transaction.pay_fees(event_data, block, transaction)

        for event in event_data:
            if event['event_id'] == 'Transfer':
                amount_transferred = event['attributes'][2]['value']

        transaction.amount_transferred = amount_transferred

        from_account.update_balance(block.block_number, to_account,transferable= -(amount_transferred + fee) )
        to_account.update_balance(transferable=amount_transferred)


        transaction.from_balance.add(from_account.get_current_balance())
        transaction.to_balance.add(to_account.get_current_balance())

    @staticmethod
    def handle_bond(transaction_data: Dict, event_data: Dict, block: Block, transaction: "Transaction", extrinsic_function: "ExtrinsicFunction"):
        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))

        balance = Account.get_current_balance(from_account)

        if extrinsic_function.name == "bond":
            amount_transferred = transaction_data["call"]["call_args"][1]["value"]
            controller_address = transaction_data["call"]["call_args"][0]["value"].replace("0x", "")
            controller_account = Account.get(controller_address)
            if not controller_account:
                controller_account = Account.create(controller_address)
            controller_account.controls.add(from_account)
            Account.save(controller_account)
        elif extrinsic_function.name == "bond_extra":
            amount_transferred = transaction_data["call"]["call_args"][0]["value"]
        else:
            raise NotImplementedError()

        transaction.amount_transferred = amount_transferred
        fee = Transaction.pay_fees(event_data, block, transaction)


        from_account.update_balance(block.block_number, from_account, transferable=-(amount_transferred+fee) ,bonded=amount_transferred)


        transaction.from_balance.add(from_account.get_current_balance())
        transaction.to_balance.add(from_account.get_current_balance())


    @staticmethod
    def pay_fees(event_data, block, transaction):
        validator_node = list(block.has_author.triples())[0][-1]
        validator_account = list(validator_node.account.triples())[0][-1]
        treasury_account = Account.get_treasury()
        try:
            validator_fee = event_data[-2]["attributes"][1]["value"]
            treasury_fee = event_data[-3]["attributes"][0]["value"]
            treasury_account.update_balance(transferable=treasury_fee)
            transaction.reward_treasury.add(treasury_account.get_current_balance())
        except IndexError:
            validator_fee = event_data[-2]["attributes"][1]["value"]
            treasury_fee = 0

        validator_account.update_balance(transferable=validator_fee)

        transaction.reward_validator.add(validator_account.get_current_balance())

        return (validator_fee+treasury_fee)


class Aggregator(GraphObject):
    totalExtrinsics = Property()
    totalEvents = Property()
    totalAccounts = Property()
    totalTransfers = Property()
    totalIssuance = Property()
    totalStaked = Property()

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


    def update_balance(self,block_number=None,other_account: "Account"=None,transferable=0, reserved=0, bonded=0, unbonding=0):


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
