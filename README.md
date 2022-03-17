# MAP


## Producer
The producer module subscribes to the ```chain_subscribeFinalizedHeads``` JSON-RPC method of the polkadot node. It then transforms the resulting data of each new block to JSON and sends it to kafka.