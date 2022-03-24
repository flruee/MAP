from src.event_handlers.utils import event_error_handling
from src.models import Account, Block, Extrinsic, Event
from mongoengine.errors import DoesNotExist
import logging
class BalancesEventHandler():

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "Endowed":
            BalancesEventHandler.__handle_endowed(block, extrinsic, event)

    @staticmethod
    @event_error_handling(DoesNotExist)
    def __handle_endowed(block: Block, extrinsic: Extrinsic, event: Event):
        
        account = Account.objects.get(address="assa")
        
