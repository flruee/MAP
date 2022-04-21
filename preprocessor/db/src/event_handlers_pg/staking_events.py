from select import select
from src.pg_models import Account, Block, Extrinsic, Event, Balance, Transfer
from src.event_handlers_pg.utils import event_error_handling
from .abstract_event_handler import AbstractEventHandler

class StakingEventHandler(AbstractEventHandler):
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

        address = event.attributes[0]['value']
        account = self.get_or_create_account(address)
        balance = self.get_or_create_last_balance(account, block.block_number, commit=False)

        value = event.attributes[1]['value']

        from_subbalance = "transferable"
        to_subbalance = "bonded"
        self.create_transfer_in_balances(balance, balance, value, from_subbalance, to_subbalance)


        transfer = Transfer(
            block_number=block.block_number,
            from_address=account.address,
            to_address=account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Bonded"
        )

        self.session.add(transfer)
        self.session.commit()


    
    def __handle_era_paid(self,block: Block, extrinsic: Extrinsic, event: Event):
        pass

    
    #@event_error_handling(Exception)
    def __handle_rewarded(self,block: Block, extrinsic: Extrinsic, event: Event):
        from_address = extrinsic.address
        to_address = event.attributes[0]["value"]

        from_account = self.get_or_create_account(from_address)
        to_account = self.get_or_create_account(to_address)


        from_balance = self.get_or_create_last_balance(from_account, block.block_number,commit=False)
        to_balance = self.get_or_create_last_balance(to_account, block.block_number, commit=False)

        value = event.attributes[1]["value"]

        subbalance = "transferable"

        self.create_transfer_in_balances(from_balance, to_balance, value, subbalance, subbalance)

        transfer = Transfer(
            block_number=block.block_number,
            from_address=from_account.address,
            to_address=to_account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Reward"
        )
        self.session.add(transfer)
        #self.session.add(from_account)
        #self.session.add(to_account)
        self.session.commit()

    
    def __handle_slashed(self,block: Block, extrinsic: Extrinsic, event: Event):
        address = event.attributes[0]['value']
        account = self.get_or_create_account(self,address)

        treasury_account_address = '0xTreasury'
        treasury_account = self.get_or_create_account(treasury_account_address,role="Treasury")

        account_balance = self.get_or_create_last_balance(account, block.block_number)
        treasury_balance = self.get_or_create_last_balance(treasury_account, block.block_number)

        value = event.attributes[1]['value']
        subbalance = "transferable"
        self.create_transfer_in_balances(account_balance, treasury_balance, value, subbalance, subbalance)

        transfer = Transfer(
            block_number=block.block_number,
            from_address=account.address,
            to_address=treasury_account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Slash"
        )
        self.session.add(transfer)
        #self.session.add(from_account)
        #self.session.add(to_account)
        self.session.commit()
    
    #@event_error_handling(Exception)
    def __handle_unbonded(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from bonded to unbonding (for minimum of 28 days before it can be withdrawn)
        """
        address = event.attributes[0]['value']
        account = self.get_or_create_account(address)

        balance = self.get_or_create_last_balance(account, block.block_number,commit=False)

        value = event.attributes[1]['value']
        from_subbalance = "bonded"
        to_subbalance = "unbonding"
        self.create_transfer_in_balances(balance, balance, value, from_subbalance, to_subbalance)

        transfer = Transfer(
            block_number=block.block_number,
            from_address=account.address,
            to_address=account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Unbonded"
        )
        self.session.add(transfer)
        #self.session.add(from_account)
        #self.session.add(to_account)
        self.session.commit()

    #@event_error_handling(Exception)
    def __handle_withdrawn(self,block: Block, extrinsic: Extrinsic, event: Event):
        """
        Moves DOT from unbonding to transferable
        """
        address = event.attributes[0]["value"]
        account = self.get_or_create_account(address)

        balance = self.get_or_create_last_balance(account, block.block_number)

        value = event.attributes[1]['value']

        from_subbalance = "unbonding"
        to_subbalance = "transferable"
        self.create_transfer_in_balances(balance, balance, value, from_subbalance, to_subbalance, self.session)


        transfer = Transfer(
            block_number=block.block_number,
            from_address=account.address,
            to_address=account.address,
            value=value,
            extrinsic=extrinsic.id,
            type="Withdrawn"
        )
        self.session.add(transfer)
        #self.session.add(from_account)
        #self.session.add(to_account)
        self.session.commit()








