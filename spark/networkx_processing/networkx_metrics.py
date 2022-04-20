import networkx as nx
from typing import Tuple


def get_max_degree(graph: nx.Graph) -> Tuple[int, int]:
    degree_dict = dict(graph.degree)
    node_max_degree = max(degree_dict, key=degree_dict.get)
    return node_max_degree, degree_dict[node_max_degree]


def calculate_average_degree(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / graph.number_of_nodes()


def calculate_network_density(graph: nx.Graph) -> float:
    return graph.number_of_edges() * 2 / (graph.number_of_nodes()*(graph.number_of_nodes()-1))
