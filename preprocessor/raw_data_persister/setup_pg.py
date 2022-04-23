from sqlalchemy import create_engine
from src.models import *
engine = create_engine('postgresql://mapUser:mapmap@localhost/raw_data', echo=True)

engine.connect()

print(Base.metadata.create_all(engine))
