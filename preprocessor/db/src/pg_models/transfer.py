from requests import session
from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String,BigInteger, Numeric
from src.pg_models.balance import Balance
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.account import Account

class Transfer(Base):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    block_number = Column(Integer, ForeignKey(Block.block_number,ondelete="CASCADE"),index=True)
    from_account = Column(Integer, ForeignKey(Account.id,ondelete="CASCADE"))
    to_account = Column(Integer, ForeignKey(Account.id,ondelete="CASCADE"))
    from_balance = Column(Integer, ForeignKey(Balance.id,ondelete="CASCADE"))
    to_balance = Column(Integer, ForeignKey(Balance.id,ondelete="CASCADE"))
    value = Column(Numeric(22,0))
    extrinsic = Column(Integer, ForeignKey("extrinsic.id",ondelete="CASCADE"))
    type = Column(String)

    @staticmethod
    def create(
        block_number: int,
        from_account: Account,
        to_account: Account, 
        from_balance: Balance,
        to_balance: Balance,
        value: int,
        extrinsic: "Extrinsic",
        type: str
        ) -> "Transfer":
        transfer = Transfer(
            block_number=block_number,
            from_account=from_account.id if from_account else None,
            to_account=to_account.id,
            from_balance=from_balance.id if from_balance else None,
            to_balance=to_balance.id,
            value=value,
            extrinsic=extrinsic.id,
            type=type
        )

        Transfer.save(transfer)
        return transfer

    @staticmethod
    def save(transfer: "Transfer"):
        session = Driver().get_driver()
        session.add(transfer)
        session.flush()
    
    @staticmethod
    def count(block: "Block") -> int:
        """
        Returns the number of transfers stored in the db. Used for Aggregation.
        """
        session = Driver().get_driver()
        return session.query(Transfer.id).filter(Transfer.block_number == block.block_number).count()
