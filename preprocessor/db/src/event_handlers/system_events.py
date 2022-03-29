


from src.models.models import Account, Block, Extrinsic, Event, Balance
from src.event_handlers.utils import event_error_handling


class SystemEventHandler():

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "NewAccount":
            SystemEventHandler.__handle_newAccount(block, extrinsic, event)

    @staticmethod
    @event_error_handling(Exception)
    def __handle_newAccount(block: Block, extrinsic: Extrinsic, event: Event):

        balance = Balance(
            transferable=0,
            reserved=0,
            locked=[],
            block_number=block.number
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
        if account.address == "12SqZEsjmK83VmxEQsuLChWACxMXEnoQTfJyK5XqHVtAmy29":
            print("oh no")
            print(block.number)
        account.save()

