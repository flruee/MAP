from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,BigInteger
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.account import Account

class Balance(Base):
    __tablename__ = "balance"
    id = Column(Integer, primary_key=True)
    transerable = Column(BigInteger)
    reserved = Column(BigInteger)
    bonded = Column(BigInteger)
    unbonding = Column(BigInteger)
    account = Column(Integer, ForeignKey(Account.id))
    block_number = Column(Integer, ForeignKey(Block.block_number))