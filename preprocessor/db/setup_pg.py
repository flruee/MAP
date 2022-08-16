from sqlalchemy import create_engine
# The following classes need to be imported, else they won't be created in psql
from src.pg_models.base import Base
from src.pg_models.block import Block
from src.pg_models.extrinsic import Extrinsic
from src.pg_models.event import Event
from src.pg_models.transfer import Transfer
from src.pg_models.controller import Controller
from src.pg_models.validator import Validator
from src.pg_models.nominator import Nominator
from src.pg_models.validator_pool import ValidatorPool
from src.pg_models.validator_to_nominator import ValidatorToNominator
from src.pg_models.aggregator import Aggregator
from dotenv import load_dotenv, find_dotenv
import os
import ast
load_dotenv(find_dotenv())

def env(key, default=None, required=True):
    """
    Retrieves environment variables and returns Python natives. The (optional)
    default will be returned if the environment variable does not exist.
    """
    try:
        value = os.environ[key]
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value
    except KeyError:
        if default or not required:
            return default
        raise RuntimeError("Missing required environment variable '%s'" % key)


DATABASE_USERNAME = env('DATABASE_USERNAME')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
DATABASE_URL = env('DATABASE_URL')
DATABASE_NAME = env("DATABASE_NAME")
engine = create_engine(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}')

engine.connect()

print(Base.metadata.create_all(engine))
