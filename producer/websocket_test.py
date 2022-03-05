import kafka
from substrateinterface import SubstrateInterface
import json
import logging
from kafka import KafkaProducer
from websocket import create_connection
import ssl



if __name__ == "__main__":
    
    config = json.load(open("config.json"))
    url = config["node"]["url"]
    sslopt = {"cert_reqs": ssl.CERT_NONE}
    create_connection(url, sslopt=sslopt)