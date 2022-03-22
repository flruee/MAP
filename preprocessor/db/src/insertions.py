from typing import List
import datetime
import json
from src.models.models import Block,Header,Extrinsic,Event


def handle_blocks(start, end):
    for i in range(start, end+1):
        with open(f"small_block_dataset/{i}.json", "r") as f:
            data = json.loads(f.read())  

        handle_full_block(data)



def handle_full_block(data):

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
    """
    Removes unnecessary fields from header data, then creates a Header object, stores it and returns it 
    """
    header_data["header"].pop("number")
    header_data["header"].pop("hash")
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
        #last event denotes if ectrinsic was successfull
        was_successful = current_events[-1].event_id == "ExtrinsicSuccess"
        extrinsic = Extrinsic(**extrinsic_data, events=current_events, was_successful=was_successful)
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


