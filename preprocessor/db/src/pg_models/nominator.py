from wsgiref.validate import validator
from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer, BigInteger, String, Numeric
from src.driver_singleton import Driver
from src.pg_models.account import Account
from src.pg_models.validator import Validator
from src.pg_models.base import Base



class Nominator(Base):
    __tablename__ = "nominator"
    id = Column(Integer, primary_key=True)
    account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"), index=True)
    validator = Column(Integer, ForeignKey("validator.id",ondelete="CASCADE"),index=True)
    reward = Column(Numeric(22,0))
    reward_transfer = Column(ForeignKey("transfer.id",ondelete="CASCADE"),index=True)
    era = Column(Integer, ForeignKey("validator_pool.era",ondelete="CASCADE"),index=True)
    stake = Column(Numeric(22,0))


    def get_from_account(account: Account) -> "Nominator":
        session = Driver().get_driver()
        
        return session.query(Nominator).filter(Nominator.account == account.id).first()


    def create(account: Account, validator: Validator,stake: int, era: int) -> "Nominator":
        nominator = Nominator(
            account = account.id,
            validator = validator.id,
            stake = stake,
            era = era
        )
        Nominator.save(nominator)
        return nominator


    def update_rewards(nominator: "Nominator", reward: int, reward_transfer: "Transfer") -> "Nominator":
        nominator.reward = reward
        nominator.reward_transfer = reward_transfer.id
        Nominator.save(nominator)
        return nominator


    def save(nominator: "Nominator"):
        session = Driver().get_driver()
        session.add(nominator)
        session.flush()
    
    def get(era, validator, nominator_account) -> "Nominator":
        session = Driver().get_driver()

        return session.query(Nominator).filter(Nominator.validator == validator.id,Nominator.era == era, Nominator.account==nominator_account.id).first()   