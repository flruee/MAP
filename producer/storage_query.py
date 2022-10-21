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
        params=[1],
        block_hash="0x1d3c2abe129e4e816daf24fc164b4e64f09e8254126f27a4e731a9b63dccba92"

    )

    result2 = substrate.query(
        module="Balances",
        storage_function="Reserves",
        params=['124BaHGGCNSZSLTsyEuEaZjpVNfDpe9SGfEk2PYwBSrFPW1t'],
        block_hash='0x1d3c2abe129e4e816daf24fc164b4e64f09e8254126f27a4e731a9b63dccba92'
    )
    print(result2)
