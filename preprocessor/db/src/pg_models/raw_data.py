
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.orm import declarative_base
Base = declarative_base()
"""
Block
"""
class RawData(Base):
    __tablename__ = "raw_data"
    block_number = Column(Integer, primary_key=True)
    data = Column(JSON)


    def __repr__(self):
        return f"Block {self.block_number}"
        