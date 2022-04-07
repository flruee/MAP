import time
from mongoengine import connect
from src.models.models import Account
from src.insertions import handle_blocks
from src.queries.schema import schema
import logging
import time



if __name__ == "__main__":
    db_connection = connect("example", host="mongodb://127.0.0.1:27017/map", alias="default")

    query = """
        {
        account {
            address
            balances {
                transferable,
                bonded,
                unbonding,
                blockNumber
            }
        transfers{
        value,
        type
        }
        }
        }
    """
    start = time.time()
    result = schema.execute(query)
    print(time.time()-start)
    print(result)