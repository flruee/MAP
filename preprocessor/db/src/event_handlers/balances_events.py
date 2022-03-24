from src.event_handlers.utils import event_error_handling
from src.models import Account, Block, Extrinsic, Event, Balance
from mongoengine.errors import DoesNotExist
import logging
class BalancesEventHandler():

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "Endowed":
            BalancesEventHandler.__handle_endowed(block, extrinsic, event)
        elif event.event_id == "Transfer":
            BalancesEventHandler.__handle_transfer(block, extrinsic, event)

    @staticmethod
    @event_error_handling(DoesNotExist)
    def __handle_endowed(block: Block, extrinsic: Extrinsic, event: Event):
        """
        This event can be ignored because it is followed by another event (Transfer) that contains more relevant data
        """
        pass 
        
        account = Account.objects.get(address=event.attributes[0]["value"])
        print(event.attributes)
        balance = Balance(
            transferable=event.attributes[1]["value"],
            reserved=0,
            locked=[]
        )
        balance.save()
        account.balance.append(balance)
        account.save()
    
    @staticmethod
    def __handle_transfer(block: Block, extrinsic: Extrinsic, event: Event):

        print(event.attributes)
        account = Account.objects.get(address=event.attributes[0]["value"])
        balance = Balance(
            transferable=event.attributes[1]["value"],
            reserved=0,
            locked=[]
        )
        balance.save()
        account.balance.append(balance)
        account.save()