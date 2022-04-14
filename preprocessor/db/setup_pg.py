from sqlalchemy import create_engine
from src.pg_models import *
engine = create_engine('postgresql://mapUser:mapmap@172.23.149.214/map', echo=True)

engine.connect()

print(Base.metadata.create_all(engine))
