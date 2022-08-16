from requests import session
from sqlalchemy import Column, null
from sqlalchemy import ForeignKey, select
from sqlalchemy import Integer,String, DateTime, JSON, TEXT, Boolean,BigInteger
from src.pg_models.base import Base
import datetime
from src.driver_singleton import Driver
#from src.pg_models.extrinsic import Extrinsic
from src.pg_models.balance import Balance

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    address = Column(String)
    nonce = Column(Integer)
    reward_destination = Column(String, nullable=True)

    @staticmethod
    def get(id):
        session = Driver().get_driver()
        
        
        return session.query(Account).where(Account.id == id).first()

    @staticmethod
    def get_treasury():
        """
        helper function to get the treasury
        """
        session = Driver().get_driver()
        
        stmt = select(Account).where(Account.address == "13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB")
        treasury = session.query(Account).where(Account.address == "13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB").first()
        if treasury is None:
            treasury = Account.create("13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB")
        return treasury
        
    @staticmethod
    def get_from_address(address) -> "Account":
        session = Driver().get_driver()
        
        stmt = select(Account).where(Account.address == address)
        return session.query(Account).filter(Account.address == address).first()
    
    @staticmethod
    def create(address) -> "Account":
        account = Account(
            address=address,
            nonce=0
        )
        Account.save(account)
        return account
    
    @staticmethod
    def save(account: "Account"):
        session = Driver().get_driver()
        session.add(account)
        session.flush()

    def update_balance(self, extrinsic: "Extrinsic",transferable=0, reserved=0, bonded=0,
                       unbonding=0):


        balance = Balance.create(
            account=self,
            extrinsic=extrinsic,
            transferable=transferable,
            reserved=reserved,
            bonded=bonded,
            unbonding=unbonding,
        )


        return balance
    
    @staticmethod
    def count() -> int:
        """
        Returns the number of accounts stored in the db, used for the Aggregator.
        """
        session = Driver().get_driver()
        return session.query(Account.id).count()