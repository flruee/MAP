from tkinter import N
from src.event_handlers_pg.abstract_event_handler import AbstractEventHandler
from src.event_handlers_pg.utils import event_error_handling, get_account
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import transfer
import logging
from copy import deepcopy
from mongoengine.errors import DoesNotExist

class ClaimsEventHandler(AbstractEventHandler):
    def __init__(self, session):
        self.session=session

    
    def handle_event(self, block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_name == "Claimed":
            self.__handle_claimed(block, extrinsic, event)


    @event_error_handling(DoesNotExist)
    def __handle_claimed(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        if used in Claims(attest) then the event is usable, else it is redundant.

        """
        print(event.attributes)
        address = event.attributes[0]["value"]
        ethereum_address = event.attributes[1]["value"]

        account = self.get_or_create_account(address)
        ethereum_account = self.get_or_create_account(address, role="Ethereum address")


        value = event.attributes[2]["value"]

        balance = self.get_last_balance(account)
        if balance is None:
            balance = self.create_empty_balance(account.address, commit=False)
            balance.transferable = value

        transfer = Transfer(
            block_number=block.block_number,
            from_address=ethereum_address,
            to_address=address,
            value=value,
            extrinsic=extrinsic.id,
            type="Claimed"
        )

        self.session.add(balance)
        self.session.add(transfer)
        self.session.commit()

  