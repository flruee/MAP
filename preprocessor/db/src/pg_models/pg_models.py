from graphene import Int
from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, DateTime, JSON, TEXT, Boolean,BigInteger
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship



Base = declarative_base()
"""
Block
"""
class Block(Base):
    __tablename__ = "block"
    block_number = Column(Integer, primary_key=True)
    hash = Column(String, nullable=False)
    timestamp = Column(DateTime,nullable=False)
    extrinsicsRoot = Column(String, nullable=False)
    parentHash = Column(String, nullable=False)
    stateRoot = Column(String, nullable=False)
    author = Column(String,nullable=False)


    def __repr__(self):
        return f"Block {self.block_number}"

class Extrinsic(Base):
    __tablename__ = "extrinsic"
    id = Column(Integer,primary_key=True)
    extrinsic_hash = Column(String)
    block_number = Column(Integer, ForeignKey("block.block_number"))
    extrinsic_length = Column(Integer, nullable=False)
    address = Column(String)
    signature = Column(JSON)
    era = Column(JSON)
    nonce = Column(Integer)
    tip = Column(BigInteger)
    module_name = Column(String)
    function_name = Column(String)
    call_args = Column(JSON)
    
    was_successful = Column(Boolean)
    fee = Column(BigInteger)

class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    event_order_id = Column(Integer) #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
    phase = Column(String)
    extrinsic = Column(Integer, ForeignKey("extrinsic.id"))
    block_number = Column(Integer, ForeignKey("block.block_number"))
    module_name =  Column(String)
    event_name =  Column(String)
    attributes = Column(JSON)
    topics = Column(JSON)
    


class Balance(Base):
    __tablename__ = "balance"
    # Values are bigger than 32bit int can handle, therefore used float as a workaround
    #TODO find another field type
    id = Column(Integer, primary_key=True)
    transferable = Column(BigInteger)
    reserved = Column(BigInteger)
    bonded = Column(BigInteger)
    unbonding = Column(BigInteger)
    block_number = Column(Integer, ForeignKey("block.block_number"))
    account = Column(String, ForeignKey("account.address"))

    def copy(self):
        return Balance(
            transferable=self.transferable,
            reserved=self.reserved,
            locked=self.locked,
            block_number=self.block_number
        )

class Account(Base):
    __tablename__ = "account"
    address = Column(String, primary_key=True)
    account_index = Column(Integer)
    nonce = Column(Integer)
    role = Column(String)

class Transfer(Base):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    block_number = Column(Integer, ForeignKey("block.block_number"))
    from_address = Column(String, ForeignKey("account.address"))
    to_address = Column(String, ForeignKey("account.address"))
    value = Column(BigInteger)
    extrinsic = Column(Integer, ForeignKey("extrinsic.id"))
    type = Column(String)

    
"""







class Vote(Document):
    validator = StringField()
    validator_bonded = FloatField()
    total_bonded = FloatField()
    nominator = IntField()
    commission = FloatField()
    my_share = FloatField()





class RewardSlash(Document):
    event_id = StringField()
    action = StringField()
    validator = StringField()
    era = IntField()
    value = IntField()
    block_number = IntField()





class Validator(Document):
    address = StringField()
    commission = FloatField()
    grandpa_vote = IntField()
    reward_point = IntField()
    latest_mining = IntField()
    nominator = IntField()






class Account(Document):
    address = StringField(required=True, unique=True)
    balances = ListField(ReferenceField(Balance))
    extrinsics = ListField(ReferenceField(Extrinsic))
    transfers = ListField(ReferenceField(Transfer))
    vote = ListField(ReferenceField(Vote))
    reward_slash = ListField(ReferenceField(RewardSlash))
    account_index = IntField()
    nonce = IntField()
    role = StringField()





class Crowdloan(Document):
    status = StringField() # selection of [active, completed, retired]
    para_id = IntField()
    project = StringField()
    owner = StringField()
    lease_period = StringField()
    fund_raised = IntField()
    fund_cap = IntField()
    countdown = DateTimeField() # example : 96 days 5 hrs
    contributor = IntField()





class Bid(Document):
    auction_index = IntField()
    lease_period = StringField()
    best_bid = FloatField()
    campaign_status = BooleanField() # maybe its string




class Auction(Document):
    auction_index = IntField()
    lease_period = StringField()
    winner = StringField()
    status = StringField()
    start_block = IntField()
    ending_period_starts = IntField()
    end_block = IntField()
    retroactive_ending_block = IntField()





class Parachain(Document):
    para_id = StringField(required=True)
    project_name = StringField()
    fund_id = StringField()
    fund_account = StringField()
    sovereign_account = StringField()
    lease_period = StringField()
    owner = StringField()
    parachain_total_slot = IntField()
    parathread = IntField()
    auction = ListField(ReferenceField(Auction))
    current_lease = IntField()
    register_status = StringField()
    register_extrinsic = StringField()
    slot_type = StringField()




class Chain(Document):
    consensus = StringField()
    blocks = ListField(ReferenceField(Block))
    accounts = ListField(ReferenceField(Account))
    parachains = ListField(ReferenceField(Parachain))

"""