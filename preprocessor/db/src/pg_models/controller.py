
from requests import session
from sqlalchemy import Column, ForeignKey, null
from sqlalchemy import Integer,String, DateTime
from src.pg_models.account import Account
from src.pg_models.base import Base
import datetime
from src.driver_singleton import Driver


class Controller(Base):
    __tablename__ = "controller"
    id = Column(Integer, primary_key=True)
    controller_account = Column(Integer,ForeignKey("account.id",ondelete="CASCADE"))
    controlled_account = Column(Integer, ForeignKey("account.id",ondelete="CASCADE"))

    @staticmethod
    def create(controller_account: Account, controlled_account: Account) -> "Controller":
        controller = Controller(
            controller_account=controller_account.id,
            controlled_account=controlled_account.id
        )

        Controller.save(controller)
        return controller
    
    @staticmethod
    def save(controller: "Controller"):
        session = Driver().get_driver()
        session.add(controller)
        session.flush()
