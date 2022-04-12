from select import select
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import event_error_handling, get_account, transfer


class StakingEventHandler:
    def __init__(self, session):
        self.session = session
    
    def handle_event(self,block: Block, extrinsic: Extrinsic, event: Event):
        if event.event_name == "Bonded":
            self.__handle_bonded(block, extrinsic, event)
        elif event.event_name == "EraPaid":  # todo: no erapaid in small block data set
            self.__handle_era_paid(block, extrinsic, event)
        elif event.event_name == "Reward":
            self.__handle_rewarded(block, extrinsic, event)
        elif event.event_name == "Slash":  # todo: no slashed in small block dataset
            self.__handle_slashed(block, extrinsic, event)
        elif event.event_name == "Unbonded":
            self.__handle_unbonded(block, extrinsic, event)
        elif event.event_name == "Withdrawn":
            self.__handle_withdrawn(block, extrinsic, event)

    
    #@event_error_handling(Exception)
    def __handle_bonded(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves dot from transferable to bonded
        """
        account = get_account(event.attributes[0]['value'], block.block_number, self.session)
        value = event.attributes[1]['value']

        from_subbalance = "transferable"
        to_subbalance = "bonded"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance, self.session)


    
    def __handle_era_paid(self,block: Block, extrinsic: Extrinsic, event: Event):
        pass

    
    #@event_error_handling(Exception)
    def __handle_rewarded(self,block: Block, extrinsic: Extrinsic, event: Event):
        from_account = get_account(extrinsic.address, block.block_number, self.session)
        to_account = get_account(event.attributes[0]["value"], block.block_number, self.session)
        value = event.attributes[1]["value"]

        subbalance = "transferable"
        from_account, to_account = transfer(from_account, to_account, value, subbalance, subbalance, self.session)
        print(event.attributes)
        transferObj = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Reward"
        )
        self.session.add(transferObj)
        self.session.add(from_account)
        self.session.add(to_account)
        self.session.commit()

    
    def __handle_slashed(self,block: Block, extrinsic: Extrinsic, event: Event):
        account = get_account(event.attributes[0]['value'], block.block_number, self.session)
        value = event.attributes[1]['value']

        treasury_account_address = '0xTreasury'
        treasury_account = get_account(treasury_account_address, block.block_number, self.session)

        subbalance = "transferable"
        from_account, to_account = transfer(account, treasury_account, value, subbalance, subbalance, self.session)

        transferObj = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Slash"
        )
        self.session.add(transferObj)
        self.session.add(from_account)
        self.session.add(to_account)
        self.session.commit()





    
    #@event_error_handling(Exception)
    def __handle_unbonded(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from bonded to unbonding (for minimum of 28 days before it can be withdrawn)
        """
        account = get_account(event.attributes[0]['value'], block.block_number, self.session)
        value = event.attributes[1]['value']

        from_subbalance = "bonded"
        to_subbalance = "unbonding"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance, self.session)


    #@event_error_handling(Exception)
    def __handle_withdrawn(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from unbonding to transferable
        """
        account = get_account(event.attributes[0]['value'], block.block_number, self.session)
        value = event.attributes[1]['value']

        from_subbalance = "unbonding"
        to_subbalance = "transferable"
        from_account, _ = transfer(account, account, value, from_subbalance, to_subbalance, self.session)










