from multiprocessing import Event
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, JSON, Boolean,BigInteger
from src.pg_models.base import Base

import datetime
from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.account import Account
from src.pg_models.balance import Balance
from src.pg_models.event import Event
class Extrinsic(Base):
    __tablename__ = "extrinsic"
    id = Column(Integer,primary_key=True)
    extrinsic_hash = Column(String)
    extrinsic_length = Column(Integer, nullable=False)
    account = Column(Integer, ForeignKey(Account.id))
    signature = Column(JSON)
    era = Column(JSON)
    nonce = Column(Integer)
    tip = Column(BigInteger)
    module_name = Column(String)
    function_name = Column(String)
    call_args = Column(JSON)
    success = Column(Boolean)
    block_number = Column(Integer, ForeignKey(Block.block_number))
    #treasury_balance = Column(Integer, ForeignKey("balance.id"))
    #validator_balance = Column(Integer, ForeignKey("balance.id"))
    
    was_successful = Column(Boolean)
    fee = Column(BigInteger)

    @staticmethod
    def create(block: "Block",extrinsic_data,event_data) -> "Extrinsic":
        Extrinsic.__clean_fields(extrinsic_data)
        was_successful = event_data[-1]["event_id"] == "ExtrinsicSuccess"
        validator_account = Extrinsic.__extract_validator_account(extrinsic_data)

        
        extrinsic = Extrinsic(
            extrinsic_hash = extrinsic_data["extrinsic_hash"],
            extrinsic_length = extrinsic_data["extrinsic_length"],
            account = validator_account,
            signature = extrinsic_data["signature"],
            era = extrinsic_data["era"],
            nonce = extrinsic_data["nonce"],
            tip = extrinsic_data["tip"],
            module_name = extrinsic_data["call"]["call_module"],
            function_name = extrinsic_data["call"]["call_function"],
            call_args = extrinsic_data["call"]["call_args"],
            success = was_successful,
            block_number = block.block_number,
            
        )
        print(extrinsic.function_name)
        if extrinsic.function_name not in ["set_heads"]:
            fee = Extrinsic.__handle_fees(extrinsic, event_data)
            extrinsic.fee = fee
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


    @staticmethod
    def __handle_fees(extrinsic, event_data):
        validator_account = Account.get(extrinsic.account)
        treasury_account = Account.get_treasury()
        
        if len(event_data) <= 1 or validator_account is None:
            return 0
        try:
            validator_fee = int(event_data[-2]["attributes"][1]["value"])
            treasury_fee = int(event_data[-3]["attributes"][0]["value"])
            validator_balance = Balance.create(validator_account,extrinsic.block_number,transferable=validator_fee)
            treasury_balance = Balance.create(treasury_account,extrinsic.block_number,transferable=treasury_fee)
            
        except (IndexError,ValueError):
            try:
                validator_fee = int(event_data[-2]["attributes"][1]["value"])
                treasury_fee = 0
                validator_balance = Balance.create(validator_account,extrinsic.block_number,transferable=validator_fee)
            except Exception:
                validator_fee = 0
                treasury_fee = 0
       
        return validator_fee+treasury_fee


    @staticmethod
    def __extract_validator_account(extrinsic_data):
        if extrinsic_data["call"]["call_function"] not in ["final_hint"]:
            validator_account = Account.get_from_address(extrinsic_data["address"])
            if validator_account is None:
                validator_account = Account.create(extrinsic_data["address"])
            return validator_account.id
        else:
            return None