from sqlalchemy import Column, null
from sqlalchemy import ForeignKey
from sqlalchemy import Integer,String, DateTime, JSON, TEXT, Boolean,BigInteger
from src.pg_models.base import Base
import datetime
from src.driver_singleton import Driver

"""
Block
"""
class Block(Base):
    __tablename__ = "block"
    block_number = Column(Integer, primary_key=True)
    hash = Column(String, nullable=False)
    timestamp = Column(DateTime,nullable=False)
    extrinsicsRoot = Column(String, nullable=False)
    parentHash = Column(String, nullable=False)
    stateRoot = Column(String, nullable=False)
    author = Column(String,nullable=False)

    @staticmethod
    def create(data):
        header = Block.__clean_header(data["header"])
        timestamp = Block.__get_timestamp(data)

        block = Block(
            block_number=data["number"],
            hash=data["hash"],
            extrinsicsRoot = header["header"]["extrinsicsRoot"],
            parentHash = header["header"]["parentHash"],
            stateRoot = header["header"]["stateRoot"],
            author = header["author"],
            timestamp=timestamp
        )

        Block.save(block)

        return block

    @staticmethod
    def save(block: "Block"):
        session = Driver().get_driver()
        session.add(block)
        session.flush()

    def __repr__(self):
        return f"Block {self.block_number}"

    @staticmethod
    def __clean_header(header_data):
        """
        Removes unnecessary fields from header data 
        """
        header_data["header"].pop("number")
        header_data["header"].pop("hash")

        return header_data
    
    @staticmethod
    def __get_timestamp(data) -> int:
        """
        extracts the block unix time out of the data and transforms it to a valid timestap
        It will fail on block 0, therefore we hardcoded its timestamp

        """

        try:
            timestamp = data["extrinsics"][0]["call"]["call_args"][0]["value"]

        except IndexError:
            timestamp = 1590507378000 - 6

        return datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=timestamp)