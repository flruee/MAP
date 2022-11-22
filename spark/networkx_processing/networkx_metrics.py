import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

import networkx.readwrite.gml as graph_reader
import pandas as pd
from networkx.algorithms.smallworld import random_reference
from networkx.algorithms.assortativity import average_degree_connectivity, degree_pearson_correlation_coefficient
from networkx.algorithms.cluster import clustering
from typing import Tuple, List, Dict
import seaborn as sns


import networkx as nx
from networkx import read_graphml
import networkx.readwrite.gml as graph_reader
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple
import random
from collections import Counter
from scipy.special import factorial
import time
import pickle
import json
from networkx.algorithms.assortativity import average_degree_connectivity, degree_pearson_correlation_coefficient
from networkx.algorithms.cluster import clustering
from networkx.algorithms.smallworld import random_reference
from networkx.algorithms import degree_centrality, closeness_centrality, betweenness_centrality, eigenvector_centrality
from scipy.stats import pearsonr, spearmanr, kendalltau
#Wheter the data set should be downloaded from the internet, must be done once.
LOAD = False


def get_max_degree(graph: nx.Graph) -> Tuple[int, int]:
    degree_dict = dict(graph.degree)
    node_max_degree = max(degree_dict, key=degree_dict.get)
    return node_max_degree, degree_dict[node_max_degree]


def calculate_average_degree(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / graph.number_of_nodes()


def calculate_network_density(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / (graph.number_of_nodes()*(graph.number_of_nodes()-1))


def calculate_degree_distribution(graph: nx.Graph) -> List[Tuple[int, float]]:
    n = graph.number_of_nodes()
    distribution = {}
    for key in graph.nodes.keys():
        # degree = graph.degree[key]
        degree = len(graph.adj[key])
        if degree not in distribution.keys():
            distribution[degree] = 1
        else:
            distribution[degree] += 1

    # for key in distribution:
    #    distribution[key] /= n
    distribution = sorted(distribution.items())
    return [d[0] for d in distribution], [d[1] for d in distribution]


def plot_distribution(graph: nx.Graph, bins=None, x_log=False, y_log=False, title=""):
    degrees = [graph.degree(i) for i in graph.nodes()]
    cnt = 0
    for i in degrees:
        if i <= 1:
            cnt += 1
    if bins is None:
        bins = [i for i in range(min(degrees), max(degrees) + 1)]
    print(degrees)
    plt.hist(degrees, density=True, bins=bins, stacked=True)

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


def plot_centralities(graphs: Dict[str, nx.Graph]):
    degrees = {}
    closenesses = {}
    betweennesses = {}
    eigenvectors = {}
    for key, value in graphs.items():
        degrees[key] = list(degree_centrality(value).values())
        print("degree done")
        closenesses[key] = list(closeness_centrality(value).values())
        print("closeness done")
        #betweennesses[key] = list(betweenness_centrality(value).values())
        print("betweeness done")
        eigenvectors[key] = list(eigenvector_centrality(value).values())
        print("eigen done")

    plot_scatter(degrees, closenesses, "closeness~degree")
    #plot_scatter(degrees, betweennesses, "betweenness~degree")
    plot_scatter(degrees, eigenvectors, "eigenvector~degree")
    #plot_scatter(closenesses, betweennesses, "betweenness~closeness")
    plot_scatter(closenesses, eigenvectors, "eigenvector~closeness")
    #plot_scatter(eigenvectors, betweennesses, "betweenness~eigenvector")


def plot_scatter(xs, ys, title: str):
    keys = list(xs.keys())
    fig, axs = plt.subplots(1, 3, figsize=(28, 10))
    fig.suptitle(title)
    max_x = 0
    min_x = 99
    max_y = 0
    min_y = 0
    for i in range(len(xs)):
        key = keys[i]
        x = xs[key]
        y = ys[key]
        ax = axs[i]

        if max_x < max(x):
            max_x = max(x)
        if max_y < max(y):
            max_y = max(y)

        if min_x > min(x):
            min_x = min(x)
        if min_y > min(y):
            min_y = min(y)

        labels = title.split("~")

        pearson = pearsonr(x, y)
        spearman = spearmanr(x, y)
        kendall = kendalltau(x, y)

        text = f"pearson: {pearson[0]}\nspearman: {spearman[0]}\nkendall: {kendall[0]}"
        ax.scatter(x, y)

        ax.set_title(f"{key}")
        ax.set_xlabel(labels[1])
        ax.set_ylabel(labels[0])

        ax.text(0.5, -0.2, text, ha="center", transform=ax.transAxes)

    for ax in axs:
        ax.set_xlim(min_x - 0.01, max_x + 0.01)
        ax.set_ylim(min_y - 0.01, max_y + 0.01)
    print(min_x, max_x)
    print(min_y, max_y)
    plt.show()



def plot_average_degree(graph_og: nx.Graph, graph_random: nx.Graph, name: str):
    key_value_og = get_k_value(average_degree_connectivity(graph_og))
    key_value_random = get_k_value(average_degree_connectivity(graph_random))
    plt.scatter(key_value_og[0],key_value_og[1], label="original", color="r")
    plt.scatter(key_value_random[0],key_value_random[1], label="random", color="b")
    plt.xlabel("k")
    plt.ylabel("average degree")
    plt.title(f"{name} Knn average degree")
    plt.legend()
    plt.show()


def get_k_value(knn: dict) -> Tuple[List, List]:
    """
    return k and the average value as two sorted lists
    """
    keys = list(knn.keys())
    keys.sort()
    values = [knn[key] for key in keys]
    return keys, values

def solve_A02_1(graph):
    graph_og = graph
    print(len(graph_og.nodes))
    graph_random = nx.directed_configuration_model(dict(graph.in_degree()).values(), dict(graph.out_degree()).values(), seed=128)
    plot_average_degree(graph_og, graph_random,"transfer network")
    print(f"Pearson Correlation coefficient Original: {degree_pearson_correlation_coefficient(graph_og)}")
    print(f"Pearson Correlation coefficient Random: {degree_pearson_correlation_coefficient(graph_random)}")

if __name__=="__main__":
    """ graph = nx.read_gml("transfer.gml")
    graphs = {}
    graphs['transfer'] = graph

    #solve_A02_1(graph)
    print(np.max(degree_centrality(graph)))
    print(np.max(closeness_centrality(graph)))"""

    """    print(f"n nodes: {len(graph.nodes())}")
    print(f"n edges: {len(graph.edges())}")
    print(f"graph is directed: {nx.is_directed(graph)}")
    print(f"graph weakly connected: {nx.is_weakly_connected(graph)}") # Treat edges as undirected
    print(f"graph strongly connected: {nx.is_strongly_connected(graph)}") # Treat edges as directed
    node_max_degree, degree = get_max_degree(graph)
    print(f"node with max degree: {node_max_degree} has degree: {degree}")
    average_degree = calculate_average_degree(graph)
    print(f"average degree of network: {average_degree}")
    network_density = calculate_network_density(graph)
    print(f"network density is: {network_density}")
    plot_distribution(graph, x_log=True, y_log=True, title="degree distribution of transfer network")"""

    #plot_centralities(graphs)

    df = pd.read_csv("../results/full_validator_network_neo.csv/part-00000-a2d01f7d-d9c9-4e55-a9df-838aa1c6a5f9-c000.csv")
    df = df.rename(columns={'31': 'era', '15yyudqwLHT6VcKdEug98wt1rCbyg5TBvr6ikakL4rNVAYXf': 'validator','14UpRGUeAfsSZHFN63t4ojJrLNupPApUiLgovXtm7ZiAHUDA':'nominator'})
    eras = df['era'].unique()
    average_degrees = []
    network_densities = []
    centrality_degrees = []
    number_nodes = []
    number_edges = []
    for era in eras:
        print(era)
        subdf = df.loc[df['era'] == era]
        graph = nx.from_pandas_edgelist(subdf, source='validator', target='nominator')
        average_degree = calculate_average_degree(graph)
        average_degrees.append(average_degree)
        print(f"average degree of network: {average_degree}")
        network_density = calculate_network_density(graph)
        network_densities.append(network_density)
        print(f"network density is: {network_density}")
        centrality_degree = max(degree_centrality(graph).values())
        centrality_degrees.append(centrality_degree)
        print(f"degree centrality {centrality_degree}")
        number_nodes.append(len(graph.nodes()))
        number_edges.append(len(graph.edges()))

    #plt.plot(eras,average_degrees, label='average degree')
    #plt.plot(eras,network_densities, label='average network density')
    plt.plot(eras,centrality_degrees, label='centrality degree')
    #plt.plot(era, number_nodes, label='number of nodes')
    #plt.plot(era, number_edges, label='number of edges')
    plt.xlabel('Era')
    plt.legend()
    plt.title('Centrality degree over eras')
    plt.show()
    plt.savefig('./edges')
