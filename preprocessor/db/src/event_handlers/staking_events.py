


from src.models.models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers.utils import event_error_handling, get_account, transfer

class StakingEventHandler():

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "Reward":
            StakingEventHandler.__handle_rewarded(block, extrinsic, event)

    @staticmethod
    #@event_error_handling(Exception)
    def __handle_rewarded(block: Block, extrinsic: Extrinsic, event: Event):
        from_account = get_account(extrinsic.address, block.number)
        to_account = get_account(event.attributes[0]["value"], block.number) 
        value = event.attributes[1]["value"]

        from_account, to_account = transfer(from_account, to_account, value)

        transfer_obj = Transfer(
            block_number=block.number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=value,
            extrinsic=extrinsic,
            type="Reward",
        )

        transfer_obj.save()
        from_account.transfers.append(transfer_obj)
        to_account.transfers.append(transfer_obj)

        from_account.save()
        to_account.save()
        print(from_account.address)



