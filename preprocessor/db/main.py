import time
from mongoengine import connect
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models.models import Account
DB = "postgres"
if DB == "postgres":
	from src.insertions_pg import PGBlockHandler
else:
	from src.insertions import handle_blocks
from src.queries.schema import schema
import logging




if __name__ == "__main__":
    logging.basicConfig(filename='db.log', level=logging.INFO,format='%(asctime)s,%(levelname)s :%(message)s')

    if DB == "postgres":
        engine = create_engine('postgresql://mapUser:mapmap@localhost/map', echo=True)
        with Session(engine) as session:
            block_handler = PGBlockHandler(session)
            block_handler.handle_blocks(4710599, 4721600)



    else:
        db_connection = connect("example", host="mongodb://127.0.0.1:27017/map", alias="default")
        start = time.time()
        #handle_blocks(3182856, 3182857)
        handle_blocks(4710599, 4721600)
        end = time.time()
        #handle_blocks(4714883,4714884)
        print(end-start)
        query = """
            {
            transfer{
            value,
            toAddress,
            type
            }
            }
        """
        result = schema.execute(query)
        print(result)
        #result = Account.objects.get(address="12vT2aGAtnqBHopieTcj7ETpsLm9YkXkcK41BAjFcfwxabHJ")
    

