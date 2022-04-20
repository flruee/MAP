import argparse
import configparser
import sys
import networkx as nx
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession

import networkx.readwrite.gml as graph_reader
from networkx.algorithms.smallworld import random_reference
from typing import Tuple, List, Dict


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


def setup_graph(graphtype: str = "undirected", nodes=None, edges: List = None) -> nx.Graph:
    if graphtype == "undirected":
        graph = nx.Graph()
    elif graphtype == "directed":
        graph = nx.DiGraph()
    if edges is not None:
        graph.add_edges_from(list(zip(edges[0], edges[1])))
    return graph


def get_max_degree(graph: nx.Graph) -> Tuple[int, int]:
    degree_dict = dict(graph.degree)
    node_max_degree = max(degree_dict, key=degree_dict.get)
    return node_max_degree, degree_dict[node_max_degree]


def plot_hist(graph: nx.Graph, bins=None, x_log=False, y_log=False, title=""):
    degrees = [graph.degree(i) for i in graph.nodes()]
    plt.hist(degrees,
             density=True,
             stacked=True)

    if x_log:
        plt.xscale("log")
        plt.xlabel("log degree")
    else:
        plt.xscale("linear")
        plt.xlabel("degree")

    if y_log:
        plt.yscale("log")
        plt.ylabel("log n_occurences")
    else:
        plt.yscale("linear")
        plt.ylabel("n_occurences")

    plt.title(title)

    plt.show()


def randomise_graph(graph: nx.Graph):
    return random_reference(graph,
                            connectivity=False)


def plot_graph(graph, node_size=100, arrow_size=50):
    nx.draw_networkx(graph,
                     pos=nx.spring_layout(graph),
                     with_labels=False,
                     node_size=node_size,
                     arrowsize=arrow_size)
    plt.show()


def calculate_average_degree(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / graph.number_of_nodes()


def calculate_network_density(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / (graph.number_of_nodes()*(graph.number_of_nodes()-1))


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


