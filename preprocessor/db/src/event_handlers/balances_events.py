from src.event_handlers.utils import event_error_handling
from src.models import Account, Block, Extrinsic, Event, Balance, Transfer
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
        account.balances.append(balance)
        account.save()

    @staticmethod
    def __get_account(address: str, block_number: int):
        try:
            account = Account.objects.get(address=address)
        except DoesNotExist:
            balance = Balance(
                transferable=0,
                reserved=0,
                locked=[],
                block_number=block_number
            )
            balance.save()
            account = Account(
                address=address,
                balances=[balance],
                extrinsics=[],
                transfers=[],
                vote=[],
                reward_slash=[],
                account_index=None,
                nonce=None,
                role=None)

            account.save()
        return account


    @staticmethod
    def __get_balance():

        pass

    @staticmethod
    def __handle_transfer(block: Block, extrinsic: Extrinsic, event: Event):

        print(event.attributes)


        from_account = BalancesEventHandler.__get_account(event.attributes[0]["value"], block.number)
        to_account = BalancesEventHandler.__get_account(event.attributes[1]["value"], block.number)
        from_account_balance = from_account.balances[-1]
        to_account_balance = to_account.balances[-1]

        from_account_balance.transferable -= event.attributes[2]["value"]  # Subtract Balance from from_account
        to_account_balance.transferable += event.attributes[2]["value"]    # Add Balance to to_account

        from_account.balances.append(from_account_balance)
        to_account.balances.append(to_account_balance)

        transfer = Transfer(
            block_number=block.number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=event.attributes[2]["value"],
            extrinsic=extrinsic
        )
        transfer.save()
        from_account.transfers.append(transfer)
        to_account.transfers.append(transfer)

        from_account.save()
        to_account.save()




