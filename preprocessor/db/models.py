from mongoengine import Document
from mongoengine.fields import IntField, StringField, DictField, ReferenceField, ListField, DateTimeField, BooleanField,DynamicField

class Header(Document):
    number = IntField()
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
    was_successfull = BooleanField()


class Block(Document):
    number = IntField(required=True, unique=True)
    hash = StringField()
    timestamp = DateTimeField(required=True)
    header = ReferenceField(Header)
    extrinsics = ListField(ReferenceField(Extrinsic))
    
