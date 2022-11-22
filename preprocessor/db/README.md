# Postgres preprocessor
This folder contains the postgres preprocessor.


## Setup

Create a python environment using requirements.txt
  * `python -m venv YOUR_ENV_NAME` 
  * `source YOUR_ENV_NAME/bin/activate` 
  * `pip install -r requirements.txt`

Create a .env file as follows:
```
DATABASE_USERNAME=mapUser
DATABASE_PASSWORD=mapmap
DATABASE_URL=localhost
DATABASE_NAME=map
RAW_DATA_DATABASE_NAME=raw_data
MODE=db
```
The `MODE` variable can be set to:
* `node`: The data is retrieved directly from the node
* `db`: The data is retrieved from the raw_data database
* `kafka`: The data is retrieved from kafka

Additionally check if the `config.json` file is in order.

Execute `python setup_pg.py` in the terminal to create the relevant tables in postgres and after that start the preprocessing process with `python main.py`.


## Staking Hotfix

The staking hotfix is here for historical reasons. It was used to add staking information to an already filled database without the need to restart the whole process. It is not needed anymore. 
