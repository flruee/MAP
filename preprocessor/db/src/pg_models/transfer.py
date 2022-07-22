from requests import session
from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String,BigInteger
from src.pg_models.balance import Balance
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic
from src.pg_models.account import Account

class Transfer(Base):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    block_number = Column(Integer, ForeignKey(Block.block_number))
    from_account = Column(Integer, ForeignKey(Account.id))
    to_account = Column(Integer, ForeignKey(Account.id))
    from_balance = Column(Integer, ForeignKey(Balance.id))
    to_balance = Column(Integer, ForeignKey(Balance.id))
    value = Column(BigInteger)
    extrinsic = Column(Integer, ForeignKey(Extrinsic.id))
    type = Column(String)

    @staticmethod
    def create(
        block_number: int,
        from_account: Account,
        to_account: Account, 
        from_balance: Balance,
        to_balance: Balance,
        value: int,
        extrinsic: int,
        type: str
        ) -> "Transfer":
        transfer = Transfer(
            block_number=block_number,
            from_account=from_account.id,
            to_account=to_account.id,
            from_balance=from_balance.id,
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