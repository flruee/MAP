# src

## driver_singleton.py
This is a singleton class that holds the database connection. Since the database connection is used in multiple different locations in the code we used a singleton approach to more easily share the connection.

## insertions_pg.py
The heart of the postgres preprocessor. The inserter receives the raw data and translates it into our data models found in `models`. It also handles special interactions of certain extrinsics such as `Utility(Batch)`.

## node_connection.py
The node connection creates a direct connection to our polkadot node. Its use is twofold. Firstly it is used to execute `Storage Function` calls which allow us to get more data on certain topics such as accurate staking numbers. Secondly it can also be used to debug while no connection to the raw data database can be made.

## utils.py
This file contains multiple utility functions used throughout the code. The functions were designed in response to the many specification changes in the blockchain that changed the way raw data was accessed. The functions allow a smooth transition between specification changes.