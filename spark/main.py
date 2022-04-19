import argparse
import configparser

from pyspark.sql import SparkSession
import sys
import networkx as nx
import matplotlib.pyplot as plt

spark = SparkSession \
    .builder \
    .appName("MAP Polkadot Pyspark") \
    .config("spark.jars", "./postgresql-42.2.6.jar") \
    .getOrCreate()


def read_spark(dbtable: str):
    return   \
        spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://localhost:5432/map") \
        .option("dbtable", dbtable) \
        .option("user", "mapUser") \
        .option("password", "mapmap") \
        .option("driver", "org.postgresql.Driver") \
        .load()


def spark_select(df, column: str):
    return df.select(column).collect()

"""
from_address = df.select("from_address").collect()
to_address = df.select("to_address").collect()

directed_graph = nx.DiGraph()
directed_graph.add_edges_from(list(zip(from_address[0:500], to_address[0:500])))

pos = nx.spring_layout(directed_graph)
nx.draw_networkx(directed_graph, pos=nx.spring_layout(directed_graph),
                 with_labels=False, node_size=1, arrowsize=1)
plt.show()

degree_centrality = nx.degree_centrality(directed_graph)
"""




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",   "--tablename",    help="table name")
    parser.add_argument("-c",   "--column",       help="column name")
    parser.add_argument("-max", "--maxrequest",   help="Maximum amount of rows", type=int)
    args = parser.parse_args()
    df = read_spark(args.tablename)
    spark_select(df, "from_address")


