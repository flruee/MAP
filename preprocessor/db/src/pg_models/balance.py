from sqlalchemy import select

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,BigInteger, Numeric
from sqlalchemy.orm import relationship
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
#from src.pg_models.account import Account

class Balance(Base):
    __tablename__ = "balance"
    id = Column(Integer, primary_key=True, index=True)
    nonce = Column(Integer)
    transferable = Column(Numeric(22,0))
    reserved = Column(Numeric(22,0))
    bonded = Column(Numeric(22,0))
    unbonding = Column(Numeric(22,0))
    account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"), index=True)
    block_number = Column(Integer, ForeignKey(Block.block_number,ondelete="CASCADE"),index=True)
    extrinsic = Column(Integer, ForeignKey("extrinsic.id",ondelete="CASCADE"))


    @staticmethod
    def create(account: "Account", extrinsic: "Extrinsic",transferable: int=0, reserved:int=0, bonded:int=0, unbonding:int=0) -> "Balance":
        # get last balance
        last_balance = Balance.get_last_balance(account)
        balance = Balance(
            transferable=last_balance.transferable+transferable,
            reserved = last_balance.reserved + reserved,
            bonded = last_balance.bonded + bonded,
            unbonding = last_balance.unbonding + unbonding,
            account = account.id,
            block_number = extrinsic.block_number,
            extrinsic=extrinsic.id,
        )

        Balance.save(balance)

        return balance
        

    @staticmethod
    def save(balance: "Balance"):
        session = Driver().get_driver()
        session.add(balance)
        session.flush()
    
    @staticmethod
    def get_last_balance(account: "Account") -> "Balance":
        """
        Returns current balance of Account.
        If Account has no current balance (meaning the account is freshly created)
        an empty balance object is returned
        """
        session = Driver().get_driver()
       
        balance = session.query(Balance).filter(Balance.id==account.current_balance).first()
        if balance is None:
            return Balance(
                transferable=0,
                reserved=0,
                bonded=0,
                unbonding=0,
            )
        
        return balance