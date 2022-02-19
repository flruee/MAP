from mongoengine import Document
from mongoengine.fields import IntField, StringField, DictField, ReferenceField, ListField, DateTimeField, BooleanField,DynamicField
from mongoengine import connect
import json
from typing import List
import datetime

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
    

def handle_full_block(data):
    with open("block_data/9038779.json", "r") as f:
        data = json.loads(f.read())

    header = insert_header(data["header"])
    extrinsics = handle_extrinsics_and_events(data)

    #first extrinsic contains the timestamp
    #datetime.fromtimestamp doesn't handle milliseconds
    timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]
    timestamp = datetime.datetime(1970,1,1) + datetime.timedelta(milliseconds=timestamp)

    block = Block(
        number = data["number"],
        hash = data["hash"],
        header = header,
        extrinsics = extrinsics,
        timestamp=timestamp
    )
    block.save()


def insert_header(header_data) -> Header:
    header = Header(**header_data["header"], author=header_data["author"])
    header.save()
    return header

def handle_extrinsics_and_events(data) -> List[Extrinsic]:
    events_data = data["events"]

    extrinsics = []
    for i in range(2,len(data["extrinsics"])):
        """
        #index 0 is reserved for the timestamp transaction in extrinsics.
        
        if i in 0:
            timestamp = extrinsic_data["call"]["call_args"][0]["value"]
            print(timestamp)
            continue
        
        #index 1 is for paraInherents which probably have to be handled differently
        if i == 1:
            continue
        """
        extrinsic_data = data["extrinsics"][i]
        # an extrinsic_hash of None indicates ParaInherent transactions or Timestamp transactions
        # timestamp is already handled above
        current_events = handle_events(events_data, i)
        print(type(current_events))
        print(type(current_events[0]))
        #last event denotes if ectrinsic was successfull
        was_successfull = current_events[-1].event_id == "ExtrinsicSuccess"        
        extrinsic = Extrinsic(**extrinsic_data, events=current_events, was_successfull=was_successfull)
        extrinsic.save()

        extrinsics.append(extrinsic)
        


        
    return extrinsics

def handle_events(events, extrinsic_idx) -> List[Event]:
    """
        Iterates through events, selects those that have the same extrinsic_idx as the given one
        stores them in the db and returns all found events


        The events correspond to the transactions based on the order the transactions were executed
        The last event of a transaction indicates if the transaction was executed successfully
        i.e. the first transaction (timestamp) with index 0 has one event (with extrinsic_id 0) that indicates if it was successfull.
        an extrinsic (lets say it was extrinsic n) that sends DOT to an other account has multiple events (all with the same extrinic_id = n-1)

    """
    current_events = []
    for event_data in events:
        if event_data["extrinsic_idx"] == extrinsic_idx:
            current_events.append(insert_event(event_data))

    return current_events


def insert_event(event_data):
    """
    Stores event data in db
    """

    event_data.pop("event")
            
    event = Event(**event_data)
    event.save()

    return event





if __name__ == "__main__":
    db_connection = connect("example", host="mongomock://localhost", alias="default")
    with open("block_data/9038779.json", "r") as f:
        data = json.loads(f.read())    
    handle_full_block(data)