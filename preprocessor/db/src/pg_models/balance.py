from sqlalchemy import select

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,BigInteger
from sqlalchemy.orm import relationship
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
#from src.pg_models.account import Account

class Balance(Base):
    __tablename__ = "balance"
    id = Column(Integer, primary_key=True, index=True)
    nonce = Column(Integer)
    transferable = Column(BigInteger)
    reserved = Column(BigInteger)
    bonded = Column(BigInteger)
    unbonding = Column(BigInteger)
    account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"), index=True)
    block_number = Column(Integer, ForeignKey(Block.block_number,ondelete="CASCADE"))
    extrinsic = Column(Integer, ForeignKey("extrinsic.id",ondelete="CASCADE"))


    @staticmethod
    def create(account: "Account", extrinsic: "Extrinsic",transferable: int=0, reserved:int=0, bonded:int=0, unbonding:int=0,executing=False) -> "Balance":
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
    def get_last_balance(account) -> "Balance":
        session = Driver().get_driver()
        #stmt = select(Balance).where(account=account.id).order_by(Balance.id.desc())
        balance = session.query(Balance).filter(Balance.account==account.id).order_by(Balance.id.desc()).order_by(Balance.transferable).first()
        if balance is None:
            return Balance(
                transferable=0,
                reserved=0,
                bonded=0,
                unbonding=0,
            )
        return balance
        