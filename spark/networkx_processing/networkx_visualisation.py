import matplotlib.pyplot as plt
import networkx as nx
from typing import Tuple, List
from networkx import random_reference

def setup_graph(graphtype: str = "undirected", nodes=None, edges: List = None) -> nx.Graph:
    if graphtype == "undirected":
        graph = nx.Graph()
    elif graphtype == "directed":
        graph = nx.DiGraph()
    if edges is not None:
        graph.add_edges_from(list(zip(edges[0], edges[1])))
    return graph



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