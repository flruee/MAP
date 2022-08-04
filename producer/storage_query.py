from substrateinterface import SubstrateInterface
import json
import ssl
from src.serializer import Serializer

if __name__ == "__main__":

    with open("config.json","r") as f:
        config = json.loads(f.read())

    polkadot_config = config["node"]
    kafka_config = config["kafka"]
    producer_config = config["producer"]



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
    
    result = substrate.query(
        module='Staking',
        storage_function='ErasRewardPoints',
        params=[5000]
    )
    print(result)
