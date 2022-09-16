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
    def get_last_balance(account: "Account") -> "Balance":
        session = Driver().get_driver()
        """
        #stmt = select(Balance).where(account=account.id).order_by(Balance.id.desc())
        #balance = session.query(Balance).filter(Balance.account==account.id).order_by(Balance.id.desc()).order_by(Balance.transferable).first()
        with_query = session.query(Balance).filter(Balance.account==account.id)
        with_query = with_query.cte("last_balance_selection")
        balance = session.query(with_query).order_by(with_query.c.id.desc()).first()
        #balance = session.query(Balance).filter(Balance.account==account.id).order_by(Balance.id.desc()).all()
        """
        balance = session.query(Balance).filter(Balance.id==account.last_balance).first()
        if balance is None or len(balance) == 0:
            return Balance(
                transferable=0,
                reserved=0,
                bonded=0,
                unbonding=0,
            )
        #balance = Balance(
        #        balance
        #        )
        
        return balance