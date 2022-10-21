from ast import Num
from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer, Numeric
from src.driver_singleton import Driver
from src.pg_models.account import Account

from src.pg_models.base import Base



class Validator(Base):
    __tablename__ = "validator"
    id = Column(Integer, primary_key=True)
    account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"), index=True)
    era = Column(Integer, 
        #ForeignKey("validator_pool.era")
        index=True)
    reward_points = Column(Integer)
    total_stake = Column(Numeric(22,0))
    own_stake = Column(Numeric(22,0))
    commission = Column(Integer)


    def create(account: Account, era: int, reward_points: int, total_stake:int, own_stake:int, commission:int) -> "Validator":
        validator = Validator(
            account = account.id,
            era = era,
            reward_points=reward_points,
            total_stake=total_stake,
            own_stake=own_stake,
            commission=commission
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
    
    def get(era, account) -> "Validator":
        session = Driver().get_driver()
        return session.query(Validator).filter(Validator.account == account.id,Validator.era == era).first()   