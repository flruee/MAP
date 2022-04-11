from src.models.models import Account, Block, Extrinsic, Event, Balance, Transfer, RewardSlash
from src.event_handlers_pg.utils import event_error_handling, get_account, transfer


class StakingEventHandler:

    @staticmethod
    def handle_event(block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_id == "Bonded":
            StakingEventHandler.__handle_bonded(block, extrinsic, event)
        elif event.event_id == "EraPaid":  # todo: no erapaid in small block data set
            StakingEventHandler.__handle_era_paid(block, extrinsic, event)
        elif event.event_id == "Reward":
            StakingEventHandler.__handle_rewarded(block, extrinsic, event)
        elif event.event_id == "Slash":  # todo: no slashed in small block dataset
            StakingEventHandler.__handle_slashed(block, extrinsic, event)
        elif event.event_id == "Unbonded":
            StakingEventHandler.__handle_unbonded(block, extrinsic, event)
        elif event.event_id == "Withdrawn":
            StakingEventHandler.__handle_withdrawn(block, extrinsic, event)

    @staticmethod
    #@event_error_handling(Exception)
    def __handle_bonded(block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves dot from transferable to bonded
        """
        account = get_account(event.attributes[0]['value'], block.block_number)
        value = event.attributes[1]['value']

        from_subbalance = "transferable"
        to_subbalance = "bonded"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance)

        from_account.save()

    @staticmethod
    def __handle_era_paid(block: Block, extrinsic: Extrinsic, event: Event):
        pass

    @staticmethod
    #@event_error_handling(Exception)
    def __handle_rewarded(block: Block, extrinsic: Extrinsic, event: Event):
        from_account = get_account(extrinsic.address, block.block_number)
        to_account = get_account(event.attributes[0]["value"], block.block_number)
        value = event.attributes[1]["value"]

        subbalance = "transferable"
        from_account, to_account = transfer(from_account, to_account, value, subbalance, subbalance)

        transfer_obj = Transfer(
            block_number=block.block_number,
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

    @staticmethod
    def __handle_slashed(block: Block, extrinsic: Extrinsic, event: Event):
        account = get_account(event.attributes[0]['value'], block.block_number)
        value = event.attributes[1]['value']

        treasury_account_address = '0xTreasury'
        treasury_account = get_account(treasury_account_address, block.block_number)

        subbalance = "transferable"
        from_account, to_account = transfer(account, treasury_account, value, subbalance, subbalance)

        transfer_obj = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=treasury_account.address,  # todo: find treasury address
            value=value,
            extrinsic=extrinsic,
            type="Slash",
        )

        transfer_obj.save()
        from_account.transfers.append(transfer_obj)
        to_account.transfers.append(transfer_obj)
        from_account.save()
        to_account.save()





    @staticmethod
    #@event_error_handling(Exception)
    def __handle_unbonded(block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from bonded to unbonding (for minimum of 28 days before it can be withdrawn)
        """
        account = get_account(event.attributes[0]['value'], block.block_number)
        value = event.attributes[1]['value']

        from_subbalance = "bonded"
        to_subbalance = "unbonding"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance)

        from_account.save()

    @staticmethod
    #@event_error_handling(Exception)
    def __handle_withdrawn(block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from unbonding to transferable
        """
        account = get_account(event.attributes[0]['value'], block.block_number)
        value = event.attributes[1]['value']

        from_subbalance = "unbonding"
        to_subbalance = "transferable"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance)

        from_account.save()









