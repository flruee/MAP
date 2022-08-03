from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,BigInteger
from src.pg_models.base import Base

from src.driver_singleton import Driver
from src.pg_models.block import Block

class Aggregator(Base):
    __tablename__ = "aggregator"
    block_number = Column(Integer, ForeignKey(Block.block_number), primary_key=True)
    total_extrinsics = Column(Integer)
    total_events = Column(Integer)
    total_accounts = Column(Integer)
    total_transfers = Column(Integer)
    total_currency = Column(BigInteger)
    total_staked = Column(BigInteger)

    