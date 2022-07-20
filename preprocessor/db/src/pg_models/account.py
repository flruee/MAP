from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, DateTime, JSON, TEXT, Boolean,BigInteger
from src.pg_models.base import Base
import datetime
from src.driver_singleton import Driver
from src.pg_models import Block

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    address = Column(String)
    nonce = Column(Integer)