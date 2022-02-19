from mongoengine import connect
import json
from insertions import handle_full_block
from queries import block_schema


if __name__ == "__main__":
    db_connection = connect("example", host="mongomock://localhost", alias="default")
    with open("../block_data/9038779.json", "r") as f:
        data = json.loads(f.read())    
    handle_full_block(data)

    with open("../block_data/9038780.json", "r") as f:
        data = json.loads(f.read())    
    handle_full_block(data)  

    query = """
        query {
            blocks {
                number
            }
        }
    """
    result = block_schema.execute(query)
    print(result)