from ctypes import util
from multiprocessing import Event
from charset_normalizer import from_bytes
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, JSON, Boolean,BigInteger
from src.pg_models.base import Base
from typing import List
import datetime
from src.driver_singleton import Driver
from src.pg_models.block import Block
from src.pg_models.account import Account
from src.pg_models.balance import Balance
from src.pg_models.event import Event
from src.pg_models.transfer import Transfer
from src.utils import extract_event_attributes, convert_public_key_to_polkadot_address
class Extrinsic(Base):
    __tablename__ = "extrinsic"
    id = Column(Integer,primary_key=True)
    extrinsic_hash = Column(String)
    extrinsic_length = Column(Integer)
    account = Column(Integer, ForeignKey(Account.id,ondelete="CASCADE"))
    signature = Column(JSON)
    era = Column(JSON)
    nonce = Column(Integer)
    tip = Column(BigInteger)
    module_name = Column(String)
    function_name = Column(String)
    call_args = Column(JSON)
    block_number = Column(Integer, ForeignKey(Block.block_number,ondelete="CASCADE"),index=True)
    #treasury_balance = Column(Integer, ForeignKey("balance.id"))
    #validator_balance = Column(Integer, ForeignKey("balance.id"))
    
    was_successful = Column(Boolean)
    fee = Column(BigInteger)

    @staticmethod
    def create(block: "Block",extrinsic_data,event_data) -> "Extrinsic":
        Extrinsic.__clean_fields(extrinsic_data)
        was_successful = event_data[-1]["event_id"] == "ExtrinsicSuccess"
        sender_account = Extrinsic.__extract_sender_account(extrinsic_data)
        

        extrinsic = Extrinsic(
            extrinsic_hash = extrinsic_data["extrinsic_hash"],
            extrinsic_length = extrinsic_data["extrinsic_length"],
            account = sender_account.id if sender_account is not None else None,
            signature = extrinsic_data["signature"],
            era = extrinsic_data["era"],
            nonce = extrinsic_data["nonce"],
            tip = extrinsic_data["tip"],
            module_name = extrinsic_data["call"]["call_module"],
            function_name = extrinsic_data["call"]["call_function"],
            call_args = extrinsic_data["call"]["call_args"],
            was_successful = was_successful,
            block_number = block.block_number,
            
        )
        #awkward to save it twice, but can't really see a better way
        # extrinsic needs the fee from the handle_fees function
        # but the function needs the id from extrinsic which is only
        # created after saving
        Extrinsic.save(extrinsic)
        if extrinsic.function_name in ["set_heads"] or sender_account is None:
            return extrinsic
            
        fee = Extrinsic.__handle_fees(extrinsic, event_data,sender_account,block)
        extrinsic.fee = fee
        Extrinsic.save(extrinsic)

        return extrinsic

    @staticmethod
    def create_from_batch(block: Block, data, events: List[Event], parent: "Extrinsic", was_successful: bool) -> "Extrinsic":
        extrinsic = Extrinsic(
            extrinsic_hash = parent.extrinsic_hash,
            extrinsic_length = None,
            account = parent.account,
            signature = None,
            era = None,
            nonce = None,
            tip = None,
            module_name = data["call_module"],
            function_name = data["call_function"],
            call_args = data["call_args"],
            was_successful = was_successful,
            block_number = block.block_number,
            fee=0
            
        )

        Extrinsic.save(extrinsic)


        return extrinsic

    @staticmethod
    def create_from_proxy(block: Block, parent: "Extrinsic", events: List[Event]) -> "Extrinsic":
        was_successful = False
        for event in events:
            if event.module_name == "Proxy" and event.event_name == "ProxyExecuted":
                if event.attributes[0]["value"] == "Ok":
                    was_successful = True
                break
            elif event.module_name == "System" and event.event_name == "ExtrinsicSuccess":
                was_successful = True
                

        address = parent.call_args[0]["value"]
        account = Account.get_from_address(address)
        if account is None:
            account = Account.create(address)

        extrinsic_data = parent.call_args[2]["value"]
        extrinsic = Extrinsic(
            extrinsic_hash = parent.extrinsic_hash,
            extrinsic_length = None,
            account = account.id,
            signature = None,
            era = None,
            nonce = None,
            tip = None,
            module_name = extrinsic_data["call_module"],
            function_name = extrinsic_data["call_function"],
            call_args = extrinsic_data["call_args"],
            was_successful = was_successful,
            block_number = block.block_number,
            fee=0     
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


    @staticmethod
    def __handle_fees(extrinsic: "Extrinsic", event_data, author_account: Account, block: Block):
        validator_account = Account.get_from_address(block.author)
        if not validator_account:
            validator_account = Account.create(block.author)
        treasury_account = Account.get_treasury()
        author_balance = Balance.get_last_balance(author_account)
        if len(event_data) <= 1 or validator_account is None:
            return 0
        
        validator_event_index = -2
        treasury_event_index = -3
        try:
            validator_fee = None
            if event_data[validator_event_index]["module_id"] != "Balances" or event_data[validator_event_index]["event_id"] != "Deposit":
                if event_data[validator_event_index -1]["module_id"] == "Balances" and event_data[validator_event_index-1]["event_id"] == "Deposit":
                    validator_event_index -= 1
                else:
                    validator_fee = 0
                
            if validator_fee is None:
                validator_fee = int(extract_event_attributes(event_data[validator_event_index],1))

            validator_balance = validator_account.update_balance(extrinsic,transferable=validator_fee)
            author_balance = author_account.update_balance(extrinsic,transferable=-validator_fee)
            Transfer.create(extrinsic.block_number, author_account, validator_account, author_balance,validator_balance,validator_fee,extrinsic,"ValidatorFee")

            treasury_fee = None
            if event_data[treasury_event_index]["module_id"] != "Treasury" or event_data[treasury_event_index]["event_id"] != "Deposit":
                treasury_fee = 0
            
            if treasury_fee is None:
                treasury_fee = int(extract_event_attributes(event_data[-3],0))
            treasury_balance = treasury_account.update_balance(extrinsic,transferable=treasury_fee)
            author_balance = author_account.update_balance(extrinsic,transferable=-treasury_fee)
            Transfer.create(extrinsic.block_number, author_account, treasury_account, author_balance,treasury_balance,treasury_fee,extrinsic,"TreasuryFee")

        except (IndexError,ValueError,TypeError):
            try:
                validator_fee = int(extract_event_attributes(event_data[-2],1))
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
            address = extrinsic_data["address"]
            if address is None:
                return None

            # Extrinsic in batches have the 0x prefix
            if "0x" in address:
                address = address[2:]
            sender_account = Account.get_from_address(address)
            if sender_account is None:
                sender_account = Account.create(address)
            return sender_account
        else:
            return None

    @staticmethod
    def create_from_sudo(block: Block, parent: "Extrinsic", events: List[Event]) -> "Extrinsic":
        
        account = Account.get(parent.account)
        was_successful = True
        for event in events:
            if event.module_name == "Sudo" and event.event_name == "Sudid":
                if event.attributes[0]["value"] != "Ok":
                    was_successful = False
                break

        # In case of 'SudoAs' the sudo account makes a call on behalf of another account
        # Get the correct account and select the real call data
        if parent.call_args[0]["name"] == "who":
            extrinsic_data = parent.call_args[1]["value"]
            address = parent.call_args[0]["value"][2:]
            account = Account.get_from_address(address)
            if account is None:
                account = Account.create(address)
        else:
            extrinsic_data = parent.call_args[0]["value"]

        extrinsic = Extrinsic(
            extrinsic_hash = parent.extrinsic_hash,
            extrinsic_length = None,
            account = account.id,
            signature = None,
            era = None,
            nonce = None,
            tip = None,
            module_name = extrinsic_data["call_module"],
            function_name = extrinsic_data["call_function"],
            call_args = extrinsic_data["call_args"],
            was_successful = was_successful, 
            block_number = block.block_number,
            fee=0     
        )

        Extrinsic.save(extrinsic)
        return extrinsic