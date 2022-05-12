import matplotlib.pyplot as plt
import networkx as nx
from typing import Tuple, List

import numpy as np
from networkx import random_reference
import pandas as pd

def setup_graph(graphtype: str = "undirected", nodes=None, edges: List = None) -> nx.Graph:
    if graphtype == "undirected":
        graph = nx.Graph()
    elif graphtype == "directed":
        graph = nx.DiGraph()
    if edges is not None:
        graph.add_edges_from(list(zip(edges[0], edges[1])))
    return graph



def plot_histo(graph: nx.Graph, bins=None, x_log=False, y_log=False, title=""):
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


def read_parquet(filename):
    return pd.read_parquet("../results/" + filename)


def plot_hist(data: List[float],label: str, xlabel: str = "", density=True, show=True):
    plt.hist(data, label=label, density=density)
    plt.xlabel(xlabel)
    plt.ylabel(f"{'density' if density else 'count'} ")
    if show:
        plt.legend()
        plt.show()

if __name__ == "__main__":
    column = 'reserved'
    df = read_parquet("balances_last.parquet")
    result_df = df.loc[:, ['account', column]].groupby('account').sum().value_counts().sort_index()
    transformed_index = result_df.reset_index()[column] / 1e10
    result_df = result_df.reset_index()
    result_df[column] = transformed_index
    print(result_df.shape)
    result_df = result_df[result_df[column]!=0]
    result_df = result_df[result_df[column]>-1e4]
    result_df = result_df[result_df[column]<1e4]
    print(result_df.shape)
    binning = pd.cut([index for index in result_df[column]],50)
    result_df.index = result_df[column]
    result_df.drop(column, inplace=True, axis=1)
    ax = result_df.groupby(binning).agg(['count']).plot.bar()

    plt.title(column + ' balance distribution (50 bins)')
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.tight_layout()
    plt.show()

