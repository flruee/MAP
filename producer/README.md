# Producer

This module subscribes to new block events and sends the data to kafka.

## Setup

Setup python environment with requirements.txt  
```pip install -r requirements.txt```

In kafka_config.json specify:
* The URI's for the kafka servers
* The topic name

In polkadot_config.json specify:
* The URI to the polkadot node

Start the program with   
```python main.py```

## producer config
Refer [here](https://docs.python.org/3/library/logging.html#levels) for logging levels.