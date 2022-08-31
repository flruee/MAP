
from requests import session
from sqlalchemy import BigInteger, Column, ForeignKey, null
from sqlalchemy import Integer
from src.driver_singleton import Driver
from src.pg_models.account import Account
from src.pg_models.event import Event
from src.pg_models.base import Base
from src.pg_models.nominator import Nominator
from src.pg_models.validator import Validator

class ValidatorToNominator(Base):
    __tablename__ = "validator_to_nominator"
    nominator = Column(Integer, ForeignKey("nominator.id"), primary_key=True)
    validator = Column(Integer, ForeignKey("validator.id"), primary_key=True)
    era = Column(Integer, primary_key=True)

    def create(nominator: Nominator, validator: Validator, era: int ) -> "ValidatorToNominator":
        vtn = ValidatorToNominator(
            nominator=nominator.id,
            validator=validator.id,
            era=era
        )
        ValidatorToNominator.save(vtn)
        return vtn
    
    def save(vtn: "ValidatorToNominator"):
        session = Driver().get_driver()
        session.add(vtn)
        session.flush()