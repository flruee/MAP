from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String,BigInteger
from preprocessor.db.src.pg_models.account import Account
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic

class Transfer(Base):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    block_number = Column(Integer, ForeignKey(Block.block_number))
    from_account = Column(Integer, ForeignKey(Account.id))
    to_account = Column(Integer, ForeignKey(Account.id))
    value = Column(BigInteger)
    extrinsic = Column(Integer, ForeignKey(Extrinsic.id))
    type = Column(String)
