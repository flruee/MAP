from dotenv import load_dotenv, find_dotenv
import os
import ast
import time
import json
import logging
from kafka import KafkaConsumer
from mongoengine import connect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from src.driver_singleton import Driver
from src.pg_models.block import Block
DB = "postgres"
if DB == "postgres":
    from src.insertions_pg import PGBlockHandler
else:
	from src.insertions import handle_blocks
from src.queries.schema import schema
import logging
import traceback
from src.pg_models.raw_data import RawData

load_dotenv(find_dotenv())


from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging
from logging.handlers import RotatingFileHandler

from src.pg_models.event import Event
from substrateinterface import SubstrateInterface
import ssl
from src.pg_models.validator_pool import ValidatorPool
from src.pg_models.validator import Validator
from src.pg_models.nominator import Nominator
from src.pg_models.block import Block
from src.pg_models.account import Account
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

def create_substrate_connection():
        with open("config.json","r") as f:
            node_config=json.loads(f.read())["node"]
        sslopt = {
        "sslopt": {
            "cert_reqs": ssl.CERT_NONE
            }
        }
        substrate = SubstrateInterface(
            url=node_config["url"],
            ss58_format=node_config["ss58_format"],
            type_registry_preset=node_config["type_registry_preset"],

            ws_options=sslopt
        )
        return substrate
    
def handle_special_events(hash, era, block_number):
    """
    Certain features, like an era change, are only captured in events.
    """
    # Denotes that a new era has started. Note that EraPayout and EraPaid are the same event, they just got
    # renamed after some time.
    # From the following event we get the total reward of the last era
    block = Block(hash=hash)
    validator_pool = ValidatorPool.get(era)

    
    substrate = create_substrate_connection()
    # Get all validators of era
    validator_reward_points= substrate.query(
        module='Staking',
        storage_function='ErasRewardPoints',
        params=[validator_pool.era],
        block_hash=block.hash
    ).value
    staking_sum = 0
    for validator_address,reward_points in validator_reward_points["individual"]:

        validator_account = Account.get_from_address(validator_address)
        if validator_account is None:
            validator_account = Account.create(validator_address)

        validator_staking= substrate.query(
            module='Staking',
            storage_function='ErasStakers',
            params=[validator_pool.era,validator_address],
            block_hash=block.hash
        ).value
        commission = substrate.query(
            module='Staking',
            storage_function='ErasValidatorPrefs',
            params=[validator_pool.era,validator_address],
            block_hash=block.hash
        ).value
        validator = Validator.get(era, validator_account)
        if validator is None:
            validator = Validator.create(validator_account, validator_pool.era, reward_points,validator_staking["total"], validator_staking["own"], commission["commission"])
        else:
            validator.reward_points = reward_points
            validator.total_stake = validator_staking["total"]
            validator.own_stake = validator_staking["own"],
            validator.commission =  commission["commission"]
            Validator.save(validator)
        staking_sum += validator.total_stake

        for element in validator_staking["others"]:
            nominator_address = element["who"]
            nominator_stake = element["value"]
            nominator_account = Account.get_from_address(nominator_address)
            if nominator_account is None:
                nominator_account = Account.create(nominator_address)
            
            nominator = Nominator.get(era, validator, nominator_account)
            if nominator is None:
                nominator = Nominator.create(nominator_account, validator, nominator_stake, validator_pool.era)
            else:
                nominator.stake = nominator_stake
                Nominator.save(nominator)

    validator_pool.total_stake = staking_sum
    validator_pool.block_number = block_number
    ValidatorPool.save(validator_pool)

DATABASE_USERNAME = env('DATABASE_USERNAME')
DATABASE_PASSWORD = env('DATABASE_PASSWORD')
DATABASE_URL = env('DATABASE_URL')
DATABASE_NAME = env("DATABASE_NAME")
RAW_DATA_DATABASE_NAME = env("RAW_DATA_DATABASE_NAME")
MODE = env("MODE")

if __name__ == "__main__":
    engine = create_engine(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE_NAME}')
    with Session(engine) as session:
        driver = Driver()
        driver.add_driver(session)
        logging.info("hi")
        q = session.execute(
            """
            Select * from event e
            inner join block b
                on b.block_number = e.block_number
            where e.module_name = 'Staking'
            and e.event_name in ('EraPayout', 'EraPaid')
            Order by b.block_number
            """
        )
        #substrate = create_substrate_connection()
        for x in q:
            print(x["block_number"])
            handle_special_events(x["hash"], x["attributes"][0]["value"], x["block_number"])
            session.commit()
