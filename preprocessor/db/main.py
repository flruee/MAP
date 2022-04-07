import time
from mongoengine import connect
from src.models.models import Account
from src.insertions import handle_blocks
from src.queries.schema import schema
import logging




if __name__ == "__main__":
    logging.basicConfig(filename='db.log', level=logging.INFO,format='%(asctime)s,%(levelname)s :%(message)s')



    db_connection = connect("example", host="mongodb://127.0.0.1:27017/map", alias="default")
    start = time.time()
    handle_blocks(4714883, 4721600)
    end = time.time()
    #handle_blocks(4714883,4714884)
    print(end-start)
    exit()
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
            value
            }
            }
            }
    """
    result = schema.execute(query)
    print(result)
    #result = Account.objects.get(address="12vT2aGAtnqBHopieTcj7ETpsLm9YkXkcK41BAjFcfwxabHJ")
    

