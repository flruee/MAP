

from ast import arg
from src.models import Block, Extrinsic, Event
import logging

def decorator_factory(decorator):
    """
    Meta decorator
    Is used to decorate other decorators such that they can have passed an argument
    e.g. 
    @decorator(argument)
    would not work if decorator isn't decorated with this decorator
    It is used mostly for the event_error_handling such that we can decorate a function with an exception and
    log it if something bad happened
    """

    def layer(error,*args, **kwargs):

        def repl(f,*args, **kwargs):
            return decorator(f, error, *args, **kwargs)
        
        return repl
    return layer

@decorator_factory
def event_error_handling(function, error, *args, **kwargs):
    """
    This decorator is used for error handling and logging

    Usage:
    @event_error_handling(LikelyExceptionThatShouldBeLogged)
    def foo(bar):
        ...
    
    """
    def wrapper( block, extrinsic, event,*args, **kwargs):

        try:
            return function(block, extrinsic, event,*args, **kwargs)
        except error as e:
            
            logging.error(f"{error.__name__}: {e}\t {function.__name__} failed at block {block.number} in extrinsic {extrinsic.extrinsic_hash} in event {event.extrinsic_idx}, {event.module_id}: {event.event_id}")

    return wrapper
