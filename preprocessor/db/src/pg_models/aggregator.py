from multiprocessing.context import set_spawning_popen
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,BigInteger,Numeric
from sqlalchemy.orm import relationship
from .account import Account
from .extrinsic import Extrinsic
from src.pg_models.base import Base
from typing import List
from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.event import Event
from src.pg_models.transfer import Transfer

class Aggregator(Base):
    __tablename__ = "aggregator"
    block_number = Column(Integer, ForeignKey(Block.block_number,ondelete="CASCADE"), primary_key=True, index=True)
    #block_number = relationship(Block,)
    total_extrinsics = Column(Integer)
    total_events = Column(Integer)
    total_accounts = Column(Integer)
    total_transfers = Column(Integer)
    total_currency = Column(Numeric(22,0))
    total_staked = Column(Numeric(22,0))


    def create(block: Block, extrinsics: List[Extrinsic], events: List[List[Event]],staked_amount,accounts):
        previous_aggregator = Aggregator.get(block.block_number-1)

        n_extrinsics = previous_aggregator.total_extrinsics + len(extrinsics)
        n_events = sum([len(e) for e in events]) + previous_aggregator.total_events
        n_accounts = previous_aggregator.total_accounts + accounts
        n_transfers = Transfer.count(block)+previous_aggregator.total_transfers
        n_currency = 0
        n_staked = previous_aggregator.total_staked + staked_amount
        
        aggregator = Aggregator(
            block_number = block.block_number,
            total_extrinsics = n_extrinsics,
            total_events = n_events,
            total_accounts = n_accounts,
            total_transfers = n_transfers,
            total_currency =  n_currency,# how?
            total_staked = n_staked 

        )

        Aggregator.save(aggregator)
        return aggregator
    
            
            
    @staticmethod
    def get(block_number: int) -> "Aggregator":
        session = Driver().get_driver()
        aggregator = session.query(Aggregator).filter(Aggregator.block_number == block_number).first()
        if aggregator is None:
            aggregator =  Aggregator(
                total_extrinsics=0,
                total_events=0,
                total_accounts=0,
                total_transfers=0,
                total_currency=0,
                total_staked=0
            )
        return aggregator

    @staticmethod
    def save(aggregator: "Aggregator"):
        session = Driver().get_driver()
        session.add(aggregator)
        session.flush()