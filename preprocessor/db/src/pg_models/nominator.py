from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer, BigInteger, String
from src.driver_singleton import Driver
from src.pg_models.account import Account
from src.pg_models.validator import Validator
from src.pg_models.base import Base



class Nominator(Base):
    __tablename__ = "nominator"
    id = Column(Integer, primary_key=True)
    account = Column(Integer, ForeignKey("account.id"))
    validator = Column(Integer, ForeignKey("validator.id"))
    stake = Column(BigInteger)
    era = Column(Integer, ForeignKey("validator_pool.era"))


    def get_from_account(account: Account) -> "Nominator":
        session = Driver().get_driver()
        
        return session.query(Nominator).filter(Nominator.account == account.id).first()


    def create(account: Account, validator: Validator, stake: int,era: int) -> "Nominator":
        nominator = Nominator(
            account = account.id,
            validator = validator.id,
            stake = stake,
            era = era
        )
        Nominator.save(nominator)
        return nominator
    
    def save(nominator: "Nominator"):
        session = Driver().get_driver()
        session.add(nominator)
        session.flush()
    