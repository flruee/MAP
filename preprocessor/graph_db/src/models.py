
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
    author = Property("author")

    has_extrinsics = RelatedTo("Extrinsic")
    #has_balances = RelatedTo("Balance")
    last_block = RelatedTo("Block")
    next_block = RelatedTo("Block")


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

    has_block = RelatedTo("Block")
    has_events = RelatedTo("Event")
    #has_callee = RelatedTo("Account")


class Event(GraphObject):

    phase = Property()
    module_name =  Property()
    event_name =  Property()
    attributes = Property()
    topics = Property()

    has_extrinsic = RelatedTo("Extrinsic")

    event_before = RelatedTo("Event")
    event_after = RelatedTo("Event")