from src.event_handlers_pg.utils import event_error_handling, get_account
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import transfer
import logging
from copy import deepcopy
from mongoengine.errors import DoesNotExist

class BalancesEventHandler:
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

        from_account = get_account(event.attributes[0]["value"], block.block_number, self.session)
        to_account = get_account(event.attributes[1]["value"], block.block_number, self.session)

        subbalance = "transferable"
        from_account, to_account = transfer(from_account, to_account, event.attributes[2]["value"],
                                            subbalance, subbalance, self.session)

        transferObj = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=event.attributes[2]["value"],
            extrinsic=extrinsic.id,
            type="Transfer"
        )
        self.session.add(transferObj)
        #transferObj.save()



        self.session.add(from_account)
        self.session.add(to_account)
        self.session.commit()




