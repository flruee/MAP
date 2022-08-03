from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer
from src.driver_singleton import Driver
from src.pg_models.account import Account

from src.pg_models.base import Base



class Validator(Base):
    __tablename__ = "validator"
    id = Column(Integer, primary_key=True)
    account = Column(Integer, ForeignKey("account.id"))
    era = Column(Integer, ForeignKey("validator_pool.era"))


    def create(account: Account, era: int) -> "Validator":
        validator = Validator(
            account = account.id,
            era = era
        )
        Validator.save(validator)
        return validator
    
    def save(validator: "Validator"):
        session = Driver().get_driver()
        session.add(validator)
        session.flush()
    
    def get_from_account(account: Account) -> "Validator":
        session = Driver().get_driver()
        return session.query(Validator).filter(Validator.account == account.id).first()   