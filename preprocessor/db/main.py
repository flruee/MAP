from mongoengine import connect
from src.models.models import Account
from src.insertions import handle_blocks
from src.queries.schema import schema
import logging




if __name__ == "__main__":
    logging.basicConfig(filename='db.log', level=logging.INFO,format='%(asctime)s,%(levelname)s :%(message)s')



    db_connection = connect("example", host="mongomock://localhost", alias="default")

    handle_blocks(4712248, 4712249)
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
            }
            }
    """
    result = schema.execute(query)
    print(result)
    #result = Account.objects.get(address="12vT2aGAtnqBHopieTcj7ETpsLm9YkXkcK41BAjFcfwxabHJ")
    

