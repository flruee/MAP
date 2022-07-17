from re import I
from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, DateTime, JSON, TEXT, Boolean,BigInteger
from sqlalchemy.orm import declarative_base

import datetime
from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic
from src.pg_models.base import Base

class Event(Base):
    __tablename__ = "event"
    id = Column(Integer, primary_key=True)
    event_order_id = Column(Integer) #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
    phase = Column(String)
    extrinsic = Column(Integer, ForeignKey(Extrinsic.id))
    block_number = Column(Integer, ForeignKey(Block.block_number))
    module_name =  Column(String)
    event_name =  Column(String)
    attributes = Column(JSON)
    topics = Column(JSON)

    @staticmethod
    def create(event_data,extrinsic_id,block_number):
        event = Event(
            extrinsic=extrinsic_id,
            event_order_id = event_data["extrinsic_idx"], #denotes in which order the events happened. given n events the first event in block has 0 last event has n-1
            phase = event_data["phase"],
            module_name =  event_data["module_id"],
            event_name =  event_data["event_id"],
            attributes = event_data["attributes"],
            topics = event_data["topics"],
            block_number=block_number

        )
        Event.save(event)
        return event

    @staticmethod
    def save(event: "Event"):
        session = Driver().get_driver()
        session.add(event)
        session.flush()
