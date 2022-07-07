
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo
from src.driver_singleton import Driver
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
    
    has_author = RelatedTo("Account")
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

        transaction = Transaction(
            extrinsic_hash = transaction_data["extrinsic_hash"]
        )
        extrinsic_function = ExtrinsicFunction.get(transaction_data["call"]["call_function"])
        if not extrinsic_function:
            extrinsic_function = ExtrinsicFunction.create(transaction_data["call"]["call_function"], transaction_data["call"]["call_module"])        

        transaction.has_extrinsic_function.add(extrinsic_function)

        from_account = Account.get(transaction_data["address"].replace("0x", ""))
        if not from_account:
            from_account = Account.create(transaction_data["address"].replace("0x", ""))
        print(extrinsic_function.name)
        if extrinsic_function.name in ["transfer", "transfer_all"]:
            to_account = Account.get(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))
            validator_account = list(block.has_author.triples())[0][-1]

            if not to_account:
                to_account = Account.create(transaction_data["call"]["call_args"][0]["value"].replace("0x", ""))

            validator_fee = event_data[-2]["attributes"][1]["value"]
            treasury_fee = event_data[-3]["attributes"][0]["value"]
            treasury_account = Account.get_treasury()


            # If a keep alive flag is set then the amount remaining on the from balance
            # has to be 1 Dot. To achieve this here we set a deduct_fee_multiplier variable
            # If keep alive is False then we deduct fees normally (fees multiplied with deduct_fees_multiplier)
            # if keep alive is true we subtract 1 Dot from the amount transferred, set deduct_fees_multiplier to 0
            # therefore the from balance will not subtract the fees additionally.
            # We do the opposite in the to_account
            deduct_fees_multpilier = 1
            if extrinsic_function.name == "transfer_all":
                #TODO check correctness ex. 6451916
                amount_transferred = from_account.get_current_balance().transferable
                #check keep alive
                if transaction_data["call"]["call_args"][1]["value"] == True:
                    amount_transferred -= int(1e10)
                    deduct_fees_multpilier = 0


            amount_transferred = transaction_data["call"]["call_args"][1]["value"]
            transaction.amount_transferred = amount_transferred

            from_account.update_balance(block.block_number, to_account,transferable=-amount_transferred - (treasury_fee + validator_fee)*deduct_fees_multpilier)
            to_account.update_balance(transferable=amount_transferred - (treasury_fee+validator_fee) * (not deduct_fees_multpilier))
            treasury_account.update_balance(transferable=treasury_fee)
            validator_account.update_balance(transferable=validator_fee)

            transaction.from_balance.add(from_account.get_current_balance())
            transaction.to_balance.add(to_account.get_current_balance())
            transaction.reward_validator.add(validator_account.get_current_balance())
            transaction.reward_treasury.add(treasury_account.get_current_balance())
    
 
        
        Transaction.save(transaction)
        block.has_transaction.add(transaction)
        Block.save(block)
        return transaction

    @staticmethod
    def save(transaction: "Transaction"):
        Driver().get_driver().save(transaction)


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
        print(extrinsic_function.name)
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
        print(module_name)
        extrinsic_module = ExtrinsicModule(
                name=module_name,
                )
        ExtrinsicModule.save(extrinsic_module)
        return extrinsic_module

    @staticmethod
    def save(extrinsic_module: "ExtrinsicModule"):
        print(extrinsic_module.name)
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

    def get_current_balance(self):
        triples = list(self.current_balance.triples())
        if not len(triples):
            balance = Balance.create(0,0,0,0)
        else:
            balance = triples[0][-1]
        print("eyy")
        print(balance)
        return balance


    @staticmethod
    def create(address: str):
        account = Account(
            address=address
        )
        null_balance = Balance.create(0,0,0,0)
        print(null_balance)
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
        last_balance.transferable += reserved
        last_balance.transferable += bonded
        last_balance.transferable += unbonding



        from_balance = Balance.createFromObject(last_balance, last_balance)

        self.has_balances.add(from_balance)
        self.current_balance.remove(last_balance)
        self.current_balance.add(from_balance)

        if other_account is not None and block_number is not None:
            self.transfer_to.add(other_account, {"block_number": block_number})

        Account.save(self)

class Balance(GraphObject):
    __tablename__ = "balance"
    # Values are bigger than 32bit int can handle, therefore used float as a workaround
    #TODO find another field type
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
