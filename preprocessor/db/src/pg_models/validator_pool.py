from unicodedata import numeric
from requests import session
from sqlalchemy import BigInteger, Column, null, Numeric, ForeignKey
from sqlalchemy import Integer
from src.driver_singleton import Driver
from src.pg_models.account import Account
from src.pg_models.event import Event
from src.pg_models.base import Base



class ValidatorPool(Base):
    __tablename__ = "validator_pool"
    era = Column(Integer, primary_key=True)
    validator_payout = Column(Numeric(22,0))
    treasury_payout = Column(Numeric(22,0))
    total_stake = Column(Numeric(22,0))
    block_number = Column(Integer, ForeignKey("block.block_number", ondelete="CASCADE"), index=True)

    def create(event: Event,block:"Block") -> "ValidatorPool":
        try:
            validator_pool = ValidatorPool(
                era = event.attributes[0]["value"],
                validator_payout = event.attributes[1]["value"],
                treasury_payout = event.attributes[2]["value"],
                block_number = block.block_number
            )
            ValidatorPool.save(validator_pool)
        except (IndexError, TypeError):
            validator_pool = ValidatorPool(
                era = event.attributes[0],
                validator_payout = event.attributes[1],
                treasury_payout = event.attributes[2],
                block_number = block.block_number
            )
            ValidatorPool.save(validator_pool)
        return validator_pool
    
    def save(validator_pool: "ValidatorPool"):
        session = Driver().get_driver()
        session.add(validator_pool)
        session.flush()
    
    def get(era):
        session = Driver().get_driver()
        
        
        return session.query(ValidatorPool).where(ValidatorPool.era == era).first()
    