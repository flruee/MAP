from src.event_handlers.utils import event_error_handling, get_account
from src.models import Account, Block, Extrinsic, Event, Balance, Transfer
from mongoengine.errors import DoesNotExist
from src.event_handlers.utils import transfer
import logging
from copy import deepcopy


class BalancesEventHandler:

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

    @staticmethod
    def __get_balance():

        pass

    @staticmethod
    #@event_error_handling(Exception)
    def __handle_transfer(block: Block, extrinsic: Extrinsic, event: Event):

        from_account = get_account(event.attributes[0]["value"], block.block_number)
        to_account = get_account(event.attributes[1]["value"], block.block_number)
        subbalance = "transferable"
        from_account, to_account = transfer(from_account, to_account, event.attributes[2]["value"],
                                            subbalance, subbalance)

        transfer = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=event.attributes[2]["value"],
            extrinsic=extrinsic,
            type="Transfer"
        )
        transfer.save()

        from_account.transfers.append(transfer)
        to_account.transfers.append(transfer)

        from_account.save()
        to_account.save()




