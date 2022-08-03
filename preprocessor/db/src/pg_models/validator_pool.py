from requests import session
from sqlalchemy import BigInteger, Column, null
from sqlalchemy import Integer
from src.driver_singleton import Driver
from src.pg_models.account import Account
from src.pg_models.event import Event
from src.pg_models.base import Base



class ValidatorPool(Base):
    __tablename__ = "validator_pool"
    era = Column(Integer, primary_key=True)
    validator_payout = Column(BigInteger)
    treasury_payout = Column(BigInteger)

    def create(event: Event) -> "ValidatorPool":
        print(event.attributes)
        try:
            validator_pool = ValidatorPool(
                era = event.attributes[0]["value"],
                validator_payout = event.attributes[1]["value"],
                treasury_payout = event.attributes[2]["value"]
            )
            ValidatorPool.save(validator_pool)
        except IndexError:
            validator_pool = ValidatorPool(
                era = event.attributes[0],
                validator_payout = event.attributes[1],
                treasury_payout = event.attributes[2]
            )
            ValidatorPool.save(validator_pool)
        return validator_pool
    
    def save(validator_pool: "ValidatorPool"):
        session = Driver().get_driver()
        session.add(validator_pool)
        session.flush()
    