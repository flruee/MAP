
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
from py2neo.ogm import GraphObject, Property, RelatedTo
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

class Block(GraphObject):
    __primarykey__ = "block_number"

    block_number = Property("block_number")
    hash = Property("hash")
    timestamp = Property("timestamp")
    extrinsics_root = Property("extrinsics_root")
    parent_hash = Property("parent_hash")
    state_root = Property("state_root")
    
    has_author = RelatedTo("Account")
    has_extrinsics = RelatedTo("Extrinsic")
    has_balances = RelatedTo("Balance")
    last_block = RelatedTo("Block")


class Extrinsic(GraphObject):
    extrinsic_hash = Property()
    extrinsic_length = Property()
    signature = Property()
    era = Property()
    nonce = Property()
    module_name = Property()
    function_name = Property()
    call_args = Property()
    
    fee = Property() # Found in last event "ApplyExtrinsic"
    was_successful = Property()

    has_events = RelatedTo("Event")


class Event(GraphObject):

    phase = Property()
    module_name =  Property()
    event_name =  Property()
    attributes = Property()
    topics = Property()


    event_before = RelatedTo("Event")

class Account(GraphObject):
    __primarykey__ = "address"
    
    address = Property()
    account_index = Property()
    nonce = Property()

    has_balances = RelatedTo("Balance")


class Balance(GraphObject):
    __tablename__ = "balance"
    # Values are bigger than 32bit int can handle, therefore used float as a workaround
    #TODO find another field type
    transferable = Property()
    reserved = Property()
    bonded = Property()
    unbonding = Property()
