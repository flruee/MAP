from src.models.models import Account, Block, Extrinsic, Event, Balance
from src.event_handlers.utils import event_error_handling


class SystemEventHandler:

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "NewAccount":
            SystemEventHandler.__handle_new_account(block, extrinsic, event)

    @staticmethod
    @event_error_handling(Exception)
    def __handle_new_account(block: Block, extrinsic: Extrinsic, event: Event):
        balance = Balance(
            transferable=0,
            reserved=0,
            bonded=0,
            unbonding=0,
            block_number=block.block_number
        )
        balance.save()
        
        account = Account(
            address=event.attributes[0]["value"],
            balances=[balance],
            extrinsics=[],
            transfers=[],
            vote=[],
            reward_slash=[],
            account_index=None,
            nonce=None,
            role=None  # Todo: check if List
        )
        account.save()

