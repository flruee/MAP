from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer
from src.driver_singleton import Driver
from src.pg_models.account import Account

from src.pg_models.base import Base

######### Note: Not needed anymore ############

class ValidatorConfig(Base):
    __tablename__ = "validator_config"
    account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"), primary_key=True,index=True)
    commission = Column(Integer)
    block_number = Column(Integer, ForeignKey("block.block_number",ondelete="CASCADE"),primary_key=True,index=True)


    def create(account_id: int, commission: int,block: "Block") -> "ValidatorConfig":
        validator = ValidatorConfig(
            account = account_id,
            commission = commission,
            block_number = block.block_number
        )
        ValidatorConfig.save(validator)
        return validator
    
    def save(validator_config: "ValidatorConfig"):
        session = Driver().get_driver()
        session.add(validator_config)
        session.flush()
    
    def get_from_account_id(account_id: int) -> "ValidatorConfig":
        session = Driver().get_driver()
        return session.query(ValidatorConfig).filter(ValidatorConfig.account == account_id).first()   