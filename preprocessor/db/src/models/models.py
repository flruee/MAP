from mongoengine import Document
from mongoengine.fields import IntField, StringField, DictField, ReferenceField, ListField, DateTimeField, \
    BooleanField, DynamicField, FloatField,LongField

"""
BlockHeader Model
"""

class Header(Document):
    meta = {'collection': 'header'}

    extrinsicsRoot = StringField()
    parentHash = StringField()
    stateRoot = StringField()
    digest = DictField()
    author = StringField()
    """
    @staticmethod
    def create(json: dict) -> Header:
        return Header(*json) 
    """
class Event(Document):

    event_order_id = IntField() #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
    phase = StringField()
    extrinsic_idx = IntField()
    event_id = IntField()
    event_index = IntField()
    module_id = StringField()
    event_id = StringField()
    attributes = DynamicField()
    topics = ListField()
    

class Extrinsic(Document):
    extrinsic_hash = StringField()
    extrinsic_length = IntField()
    address = StringField()
    signature = DictField()
    era = ListField()
    nonce = IntField()
    tip = IntField()
    call = DictField()
    events = ListField(ReferenceField(Event))
    was_successful = BooleanField()
    fee = FloatField()


class Block(Document):
    meta = {'collection': 'block'}
    number = IntField(required=True, unique=True)
    hash = StringField()
    timestamp = DateTimeField(required=True)
    header = ReferenceField(Header)
    extrinsics = ListField(ReferenceField(Extrinsic))


"""
Transfer Model
"""


class Transfer(Document):
    extrinsic_id = StringField()
    block = IntField()
    time = DateTimeField()
    from_address = StringField()
    to_address = StringField()
    value = FloatField()
    extrinsic = ReferenceField(Extrinsic)


"""
Vote Model
"""


class Vote(Document):
    validator = StringField()
    validator_bonded = FloatField()
    total_bonded = FloatField()
    nominator = IntField()
    commission = FloatField()
    my_share = FloatField()


"""
reward&slashed Model
"""


class RewardSlash(Document):
    event_id = StringField()
    action = StringField()
    validator = StringField()
    era = IntField()
    value = IntField()
    time = DateTimeField()


"""
Account Model
"""


class Validator(Document):
    address = StringField()
    commission = FloatField()
    grandpa_vote = IntField()
    reward_point = IntField()
    latest_mining = IntField()
    nominator = IntField()



class Locked(Document):
    bonded = IntField()
    unbonding = IntField()
    democracy = IntField()
    election = IntField()
    vesting = IntField()


class Balance(Document):
    # Values are bigger than 32bit int can handle, therefore used float as a workaround
    #TODO find another field type
    transferable = FloatField()
    reserved = IntField()
    locked = ListField(ReferenceField(Locked))



class Account(Document):
    address = StringField(required=True, unique=True)
    balance = ListField(ReferenceField(Balance))
    extrinsics = ListField(ReferenceField(Extrinsic))
    transfers = ListField(ReferenceField(Transfer))
    vote = ListField(ReferenceField(Vote))
    reward_slash = ListField(ReferenceField(RewardSlash))
    account_index = IntField()
    nonce = IntField()
    role = StringField()


"""
Crowdloan Model
"""


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


"""
Bid Model
"""


class Bid(Document):
    auction_index = IntField()
    lease_period = StringField()
    best_bid = FloatField()
    campaign_status = BooleanField() # maybe its string



"""
Auction Model
"""

class Auction(Document):
    auction_index = IntField()
    lease_period = StringField()
    winner = StringField()
    status = StringField()
    start_block = IntField()
    ending_period_starts = IntField()
    end_block = IntField()
    retroactive_ending_block = IntField()



"""
Parachain Model
"""


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


"""
Chain Model
"""

class Chain(Document):
    consensus = StringField()
    blocks = ListField(ReferenceField(Block))
    accounts = ListField(ReferenceField(Account))
    parachains = ListField(ReferenceField(Parachain))

