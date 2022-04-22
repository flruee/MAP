from src.event_handlers_pg.abstract_event_handler import AbstractEventHandler
from src.event_handlers_pg.utils import event_error_handling, get_account
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import transfer
import logging
from copy import deepcopy
from mongoengine.errors import DoesNotExist

class BalancesEventHandler(AbstractEventHandler):
    def __init__(self, session):
        self.session=session

    
    def handle_event(self, block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_name == "Endowed":
            self.__handle_endowed(block, extrinsic, event)
        elif event.event_name == "Transfer":
            self.__handle_transfer(block, extrinsic, event)

    @event_error_handling(DoesNotExist)
    def __handle_endowed(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        if used in Claims(attest) then the event is usable, else it is redundant.

        """
        pass

    def __get_balance():

        pass

    #@event_error_handling(Exception)
    def __handle_transfer(self,block: Block, extrinsic: Extrinsic, event: Event):
        from_address = event.attributes[0]["value"]
        to_address =event.attributes[0]["value"]

        from_account = self.get_or_create_account(from_address)
        to_account = self.get_or_create_account(to_address)

        from_balance = self.get_or_create_last_balance(from_account, block.block_number)
        to_balance = self.get_or_create_last_balance(to_account, block.block_number)

        subbalance = "transferable"
        value = event.attributes[2]["value"]
        self.create_transfer_in_balances(from_balance, to_balance, value,subbalance, subbalance)

        transfer = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Transfer"
        )

        self.session.add(transfer)
        self.session.add(from_account)
        self.session.add(to_account)
        self.session.commit()




