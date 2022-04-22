import argparse
import timeit
from datetime import time
from pyspark.sql import SparkSession
from networkx_processing.networkx_visualisation import plot_graph


def init_spark(query: str, ipaddress: str):
    if ipaddress is None:
        ipaddress = "localhost"
    return \
        SparkSession \
        .builder \
        .appName("MAP Polkadot Pyspark") \
        .config("spark.jars", "./postgresql-42.2.6.jar") \
        .getOrCreate() \
        .read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://" + ipaddress + ":5432/map") \
        .option("user", "mapUser") \
        .option("password", "mapmap") \
        .option("driver", "org.postgresql.Driver") \
        .option("query", query) \
        .load()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q",   "--query",        help="enter SQL query",           type=str)
    parser.add_argument("-i",   "--ipaddress",    help="default: localhost",        type=str)
    parser.add_argument("-p",   "--plot",         help="plot of graph",             type=bool)
    parser.add_argument("-s",   "--save",         help="Save to /results",          type=bool)
    parser.add_argument("-n",   "--name",         help="name for file results",     type=str)
    parser.add_argument("-p",   "--predefined",   help="choose predefined query",   type=str)
    #parser.add_argument("-max", "--maxrequest",   help="Maximum amount of rows",    type=int)
    args = parser.parse_args()
    queries = {
        "get_balances_all": "select * from balances",
        "get_transfers_all": "select * from transfers",


    }
    if args.predefined is not None:
        query = queries[args.predefined]
    start = timeit.timeit()
    spark = init_spark(query=args.query, ipaddress=args.ipaddress)
    end = timeit.timeit()
    print(end-start)
    exit()
    if args.save:
        if args.name is None:
            name = "untitled"
        else:
            name = args.name
        spark.write.parquet(path=f"./results/{name}.parquet")




