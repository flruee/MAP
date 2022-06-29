from logging.handlers import RotatingFileHandler
from select import select
import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer
import ssl
from src.serializer import Serializer
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session


if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    polkadot_config = config["node"]
    kafka_config = config["kafka"]
    producer_config = config["producer"]

    logging_filename = 'producer.log'
    logger = logging.getLogger('producer')
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    handler = RotatingFileHandler(logging_filename, maxBytes=1024**3, backupCount=2)
    logging.basicConfig(filename=logging_filename, level=producer_config["logLevel"], handlers=[handler], format=log_formatter)

    #needed for self signed certificate
    sslopt = {
        "sslopt": {
            "cert_reqs": ssl.CERT_NONE
            }
    }

    substrate = SubstrateInterface(
        url=polkadot_config["url"],
        ss58_format=polkadot_config["ss58_format"],
        type_registry_preset=polkadot_config["type_registry_preset"],

        ws_options=sslopt
    )
    engine = create_engine('postgresql://mapUser:mapmap@localhost/map')

    producer = KafkaProducer(
        bootstrap_servers=kafka_config["bootstrap_servers"],
        max_request_size=317344026,
        value_serializer=lambda x: 
            json.dumps(x).encode('utf-8')
    )

    serializer = Serializer(producer, substrate, producer_config, polkadot_config, kafka_config)
    while True:
        engine = create_engine('postgresql://mapUser:mapmap@localhost/map')
        x = engine.connect()
        max_db = x.execute("Select max(block_number) from block;").fetchone()[0]
        hash = substrate.get_chain_head()
        max_polka = substrate.get_block_number(hash)
        if max_polka > max_db:
            serializer.direct_block_handler(max_db+1,max_polka)
        else:
            result = substrate.subscribe_block_headers(serializer.subscription_handler, include_author=True, finalized_only=True)
            break
