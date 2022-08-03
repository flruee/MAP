from multiprocessing import Event
from charset_normalizer import from_bytes
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
from src.pg_models.transfer import Transfer
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
        sender_account = Extrinsic.__extract_sender_account(extrinsic_data)

        print(extrinsic_data["nonce"])

        extrinsic = Extrinsic(
            extrinsic_hash = extrinsic_data["extrinsic_hash"],
            extrinsic_length = extrinsic_data["extrinsic_length"],
            account = sender_account.id,
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
        #awkward to save it twice, but can't really see a better way
        # extrinsic needs the fee from the handle_fees function
        # but the function needs the id from extrinsic which is only
        # created after saving
        Extrinsic.save(extrinsic)
        if extrinsic.function_name not in ["set_heads"]:
            fee = Extrinsic.__handle_fees(extrinsic, event_data,sender_account,block)
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
    def __handle_fees(extrinsic: "Extrinsic", event_data, author_account: Account, block: Block):
        validator_account = Account.get_from_address(block.author)
        if not validator_account:
            validator_account = Account.create(block.author)
        treasury_account = Account.get_treasury()
        author_balance = Balance.get_last_balance(author_account)
        if len(event_data) <= 1 or validator_account is None:
            return 0
        
        try:
            validator_fee = int(event_data[-2]["attributes"][1]["value"])
            validator_balance = validator_account.update_balance(extrinsic,transferable=validator_fee)
            author_balance = author_account.update_balance(extrinsic,transferable=-validator_fee)
            Transfer.create(extrinsic.block_number, author_account, validator_account, author_balance,validator_balance,validator_fee,extrinsic,"ValidatorFee")

            treasury_fee = int(event_data[-3]["attributes"][0]["value"])
            treasury_balance = treasury_account.update_balance(extrinsic,transferable=treasury_fee)
            author_balance = author_account.update_balance(extrinsic,transferable=-treasury_fee)
            Transfer.create(extrinsic.block_number, author_account, treasury_account, author_balance,treasury_balance,treasury_fee,extrinsic,"TreasuryFee")

        except (IndexError,ValueError):
            try:
                validator_fee = int(event_data[-2]["attributes"][1]["value"])
                validator_balance = validator_account.update_balance(extrinsic,transferable=validator_fee)
                author_balance = author_account.update_balance(extrinsic,transferable=-validator_fee)
                treasury_balance = Balance.create(treasury_account,extrinsic,transferable=treasury_fee)
                Transfer.create(extrinsic.block_number, author_account, validator_account, author_balance,validator_balance,validator_fee,extrinsic,"ValidatorFee")

                treasury_fee = 0

            except Exception:
                validator_fee = 0
                treasury_fee = 0
       
        return validator_fee+treasury_fee


    @staticmethod
    def __extract_sender_account(extrinsic_data):
        if extrinsic_data["call"]["call_function"] not in ["final_hint"]:
            sender_account = Account.get_from_address(extrinsic_data["address"])
            if sender_account is None:
                sender_account = Account.create(extrinsic_data["address"])
            return sender_account
        else:
            return None