from src.event_handlers_pg.utils import event_error_handling, get_account
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import transfer
import logging
from copy import deepcopy
from mongoengine.errors import DoesNotExist

class ClaimsEventHandler:
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
        value = event.attributes[2]["value"]
        balance = Balance(
                transferable=value,
                reserved=0,
                bonded=0,
                unbonding=0,
                block_number=block.block_number,
                account=address
            )

        account = Account(
            address=address,
            account_index=None,
            nonce=None,
            role=None
            )

        transferObj = Transfer(
            block_number=block.block_number,
            from_address=ethereum_address,
            to_address=address,
            value=value,
            extrinsic=extrinsic.id,
            type="Claimed"
        )

        self.session.add(account)
        self.session.commit()
        self.session.add(balance)
        self.session.add(transferObj)
        self.session.commit()

  