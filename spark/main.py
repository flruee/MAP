import argparse
from pyspark.sql import SparkSession
from networkx_processing.networkx_visualisation import plot_graph

spark = SparkSession \
    .builder \
    .appName("MAP Polkadot Pyspark") \
    .config("spark.jars", "./postgresql-42.2.6.jar") \
    .getOrCreate()


def read_spark(dbtable: str, ipaddress: str = "localhost"):
    return   \
        spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://" + ipaddress + ":5432/map") \
        .option("dbtable", dbtable) \
        .option("user", "mapUser") \
        .option("password", "mapmap") \
        .option("driver", "org.postgresql.Driver") \
        .load()


def spark_select(dataframe, column: str):
    return dataframe.select(column).collect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",   "--tablename",    help="table name",                type=str)
    parser.add_argument("-i",   "--ipaddress",    help="default: localhost",        type=str)
    parser.add_argument("-c",   "--column",       help="column name",               type=str)
    parser.add_argument("-max", "--maxrequest",   help="Maximum amount of rows",    type=int)
    parser.add_argument("-q",   "--query",        help="enter SQL query",           type=str)
    parser.add_argument("-p",   "--plot",         help="plot of graph",             type=bool)
    args = parser.parse_args()
    df = read_spark("account")
    if args.plot:
        plot_graph()


