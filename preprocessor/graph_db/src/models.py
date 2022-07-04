
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo
from src.driver_singleton import Driver
Base = declarative_base()
"""
Block
"""
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


class Transaction(GraphObject):
    extrinsic_hash = Property()
    amount_transfered = Property()
    has_extrinsic_function = RelatedTo("ExtrinsicFunction")
    has_event_function = RelatedTo("EventFunction")

    from_balance = RelatedTo("Balance")
    to_balance = RelatedTo("Balance")
    validator_balance = RelatedTo("Balance")
    treasury_balance = RelatedTo("Balance")


    
    def __init__(self,transaction_data):
        self.extrinsic_hash = transaction_data["extrinsic_hash"]
        super(Transaction, self).__init__()

        self.__connect_functions(transaction_data)

    @staticmethod
    def create(transaction_data):
        print(transaction_data)
        transaction = Transaction()

    def __connect_functions(self, transaction_data):
        extrinsic_function = ExtrinsicFunction.get(transaction_data["call"]["call_function"])
        if not extrinsic_function:
            ExtrinsicFunction.create(transaction_data["call"]["call_function"], transaction_data["call"]["call_module"])




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
    transfer_to = RelatedTo("Account")


class Balance(GraphObject):
    __tablename__ = "balance"
    # Values are bigger than 32bit int can handle, therefore used float as a workaround
    #TODO find another field type
    transferable = Property()
    reserved = Property()
    bonded = Property()
    unbonding = Property()
