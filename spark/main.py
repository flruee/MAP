import argparse
import time
from pyspark.sql import SparkSession
#from networkx_processing.networkx_visualisation import plot_graph


queries = {
    "get_balances_all": "select * from balance",
    "get_balances_year": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 5256000 , 0) from balance b)",
    "get_balances_month": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 432000 , 0) from balance b)",
    "get_balances_day": "select * from balance b where b.block_number > (select greatest(max(b.block_number) - 14400 , 0) from balance b)",
    "get_transfers_all": "select * from transfer",
    "get_accounts_all": "select * from account",
    "get_blocks_all": "select * from block",
    "get_transfers_and_accounts": "select * from transfer t inner join account a1 on a1.address = t.from_address inner join account a2  on a2.address = t.to_address"
}


def init_spark(query: str, ipaddress: str):
    if ipaddress is None:
        ipaddress = "localhost"
    print(query)
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


def main(args):
    start = time.perf_counter()
    if args.query is not None:
        query = args.query
    else:
        query = queries[args.preset]
    spark = init_spark(query, ipaddress=args.ipaddress)
    end = time.perf_counter()
    print(end - start)
    print(spark.head())
    if args.save:
        if args.name is None:
            name = "untitled"
        else:
            name = args.name
        spark.write.parquet(path=f"./results/{name}.parquet")


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q",   "--query",                              help="enter SQL query",           type=str)
    parser.add_argument("-ip",   "--ipaddress",                          help="default: localhost",        type=str)
    parser.add_argument("-n",   "--name",                               help="name for file results",     type=str)
    parser.add_argument("-pre", "--preset",                           help="choose predefined query",   type=str)
    parser.add_argument("-p",   "--plot",    action='store_true',       help="plot of graph")
    parser.add_argument("-s",   "--save",    action='store_true',       help="Save to /results")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = argparser()
    if arguments.query is None and arguments.preset is None:
        raise UserWarning("A predefined or userdefined query via flags {-q, -pre} is required")
        exit()
    if arguments.query is not None and arguments.preset is not None:
        raise UserWarning("Cannot process predefined AND userdefined query. Select one and remove other")
        exit()

    main(arguments)







