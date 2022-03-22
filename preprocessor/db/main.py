from mongoengine import connect
from src.insertions import handle_blocks
from src.queries.queries import block_schema





if __name__ == "__main__":
    db_connection = connect("example", host="mongomock://localhost", alias="default")

    handle_blocks(4710599,4710599)
    db_connection
    query = """
        query {
            block {
                hash
            }
        }
    """
    result = block_schema.execute(query)
    print(result)