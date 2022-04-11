from src.pg_models.pg_models import Account, Block, Extrinsic, Event, Balance
from src.event_handlers_pg.utils import event_error_handling


class SystemEventHandler:
    def __init__(self, session):
        self.session = session
    
    def handle_event(self,block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_name == "NewAccount":
            self.__handle_new_account(block, extrinsic, event)

    
    @event_error_handling(Exception)
    def __handle_new_account(self,block: Block, extrinsic: Extrinsic, event: Event):
        balance = Balance(
            transferable=0,
            reserved=0,
            bonded=0,
            unbonding=0,
            block_number=block.block_number,
            account = event.attributes[0]["value"]
        )
        
        account = Account(
            address=event.attributes[0]["value"],
            account_index=None,
            nonce=None,
            role=None  # Todo: check if List
        )
        self.session.add(account)
        self.session.commit()
        self.session.add(balance)
        self.session.commit()

