from multiprocessing import Event
from substrateinterface.utils import ss58
from typing import Any

def convert_public_key_to_polkadot_address(address):
    if address is None:
        return None
    address = address.replace("0x","")
    if address[0] == '1':
        return address
    return ss58.ss58_encode(ss58_format=0, address=address)

def extract_event_attributes(event, index) -> Any:
    """
    Due to a spec change the event attributes extraction changes over time
    in the old version the attributes are of the form:
    attributes: [
        {
            "name": "ATTRIBUTE_NAME1",
            "value": "VALUE1"
        },
        {
            ...
        }
    ]
    in newer versions the name is ommited and all values are in a list like this;
    attributes: [
        VALUE1,
        VALUE2,
        ...
    ]
    except when there only is one value:
    attributes: SOLE_VALUE
    This function tries the old way first and if it fails does the new way.
    """
    try:
        result = event["attributes"][index]["value"]
    except TypeError:
        try:
            result = event["attributes"][index]
        except TypeError:
            result = event["attributes"]
    return result

def extract_event_attributes_from_object(event: Event, index:int):
    """
    Same as above but with the event object
    """

    try:
        result = event.attributes[index]["value"]
    except TypeError:
        try:
            result = event.attributes[index]
        except TypeError:
            result = event.attributes
    return result

def extract_address_from_extrinsic(extrinsic,index):
    address = extrinsic.call_args[index]["value"]
    try:
        address = address.replace("0x","")
    except AttributeError:
        print(type(address))
        print(address)
        address = address["Address32"].replace("0x","")
    
    return address
