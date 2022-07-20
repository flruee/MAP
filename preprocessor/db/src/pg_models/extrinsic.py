from sqlalchemy import Column,
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, JSON, Boolean,BigInteger
from src.pg_models.base import Base

import datetime
from src.driver_singleton import Driver
from src.pg_models import Block

class Extrinsic(Base):
    __tablename__ = "extrinsic"
    id = Column(Integer,primary_key=True)
    extrinsic_hash = Column(String)
    extrinsic_length = Column(Integer, nullable=False)
    address = Column(String)
    signature = Column(JSON)
    era = Column(JSON)
    nonce = Column(Integer)
    tip = Column(BigInteger)
    module_name = Column(String)
    function_name = Column(String)
    call_args = Column(JSON)
    block_number = Column(Integer, ForeignKey(Block.block_number))
    treasury_balance = Column(Integer, ForeignKey("balance.id"))
    validator_balance = Column(Integer, ForeignKey("balance.id"))
    
    was_successful = Column(Boolean)
    fee = Column(BigInteger)

    @staticmethod
    def create(block: "Block",extrinsic_data,event_data) -> "Extrinsic":
        print(event_data[-1])
        Extrinsic.__clean_fields(extrinsic_data)
        print(event_data[-1]["event_id"])
        was_successful = event_data[-1]["event_id"] == "ExtrinsicSuccess"
        extrinsic = Extrinsic(
            extrinsic_hash = extrinsic_data["extrinsic_hash"],
            block_number = block.block_number,
            extrinsic_length = extrinsic_data["extrinsic_length"],
            address = extrinsic_data["address"],
            signature = extrinsic_data["signature"],
            era = extrinsic_data["era"],
            nonce = extrinsic_data["nonce"],
            tip = extrinsic_data["tip"],
            module_name = extrinsic_data["call"]["call_module"],
            function_name = extrinsic_data["call"]["call_function"],
            call_args = extrinsic_data["call"]["call_args"],
            was_successful = was_successful,
            
            fee = 0 #TODO get fee
        )
        Extrinsic.save(extrinsic)
        return extrinsic

    @staticmethod
    def __clean_fields(extrinsic_data):
        """
        cleans various fields inplace
        """
        # if no era create an empty list
        if not "era" in extrinsic_data.keys():
            extrinsic_data["era"] = [None]
        # change immortal transactions "00" to -1
        if extrinsic_data["era"] == "00":
            extrinsic_data["era"] = [-1]

        for key in ["address", "signature", "nonce", "tip"]:
            if not key in extrinsic_data.keys():
                extrinsic_data[key] = None

    @staticmethod
    def save(extrinsic: "Extrinsic"):
        session = Driver().get_driver()
        session.add(extrinsic)
        session.flush()