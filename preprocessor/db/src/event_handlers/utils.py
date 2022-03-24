

from ast import arg
from src.models import Block, Extrinsic, Event
import logging

def decorator_factory(decorator):
    def layer(error,*args, **kwargs):

        def repl(f,*args, **kwargs):
            return decorator(f, error, *args, **kwargs)
        
        return repl
    return layer

@decorator_factory
def event_error_handling(function, error, *args, **kwargs):
    """
    This decorator extracts the username from an request, then uses the username and network
    to find the specific Sender for that network. It finally calls the given function with the given
    data and appends the sender object to it.
    If no sender is found it will redirect to the sendersfunnel signup instead.
    """
    def wrapper( block, extrinsic, event,*args, **kwargs):

        try:
            return function(block, extrinsic, event,*args, **kwargs)
        except error as e:
            
            logging.error(f"{error.__name__}: {e}\t {function.__name__} failed at block {block.number} in extrinsic {extrinsic.extrinsic_hash} in event {event.extrinsic_idx}, {event.module_id}: {event.event_id}")

    return wrapper
