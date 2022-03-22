from mongoengine import connect
from src.insertions import handle_blocks
from src.queries.schema import schema





if __name__ == "__main__":
    db_connection = connect("example", host="mongomock://localhost", alias="default")

    handle_blocks(4710599, 4710600)
    query = """
            {
            block {
                hash
                number
            }
            }
    """
    result = schema.execute(query)
    print(result)