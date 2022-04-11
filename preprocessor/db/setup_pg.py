from sqlalchemy import create_engine
from src.pg_models import *
engine = create_engine('postgresql://mapUser:mapmap@localhost/map', echo=True)

engine.connect()

print(Base.metadata.create_all(engine))