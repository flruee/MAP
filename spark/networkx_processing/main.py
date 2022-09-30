import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

"""
def plot_centralities(graphs: Dict[str,nx.Graph]):
    degrees = {}
    closenesses = {}
    betweennesses = {}
    eigenvectors = {}
    for key, value in graphs.items():
        degrees[key] = list(degree_centrality(value).values())
        closenesses[key] = list(closeness_centrality(value).values())
        betweennesses[key] = list(betweenness_centrality(value).values())
        eigenvectors[key] = list(eigenvector_centrality(value).values())
        

    plot_scatter(degrees,closenesses,"closeness~degree")
    plot_scatter(degrees,betweennesses,"betweenness~degree")
    plot_scatter(degrees,eigenvectors,"eigenvector~degree")
    plot_scatter(closenesses,betweennesses,"betweenness~closeness")
    plot_scatter(closenesses,eigenvectors,"eigenvector~closeness")
    plot_scatter(eigenvectors,betweennesses,"betweenness~eigenvector")
    
    

def plot_scatter(xs, ys, title: str):
    keys = list(xs.keys())
    fig, axs = plt.subplots(1,3,figsize=(28,10))
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

        ax.text(0.5,-0.2,text,ha="center",transform=ax.transAxes)

    for ax in axs:
        ax.set_xlim(min_x-0.01,max_x+0.01)
        ax.set_ylim(min_y-0.01,max_y+0.01)
    print(min_x, max_x)
    print(min_y, max_y)
    plt.show()
"""
if __name__ == "__main__":
    """    df = pd.read_parquet("../results/transfer_all.parquet")
    graph = nx.from_pandas_edgelist(df, source="from_address", target="to_address", edge_attr=["value", "type"], create_using = nx.DiGraph)
    df2 = pd.read_parquet("../results/transfernetwork.parquet")
    account_series = df2['account']
    to_series = df2['b']
    relation_series = df2['transfer_to']
    for index, row in enumerate(account_series.values):
        print(index)
        account_series.values[index] = row['address']
    for index, row in enumerate(to_series.values):
        print(index)
        to_series.values[index] = row['address']
    df2['account'] = account_series
    df2['b'] = to_series
    graph = nx.from_pandas_edgelist(df2, source="account",target="b", create_using = nx.DiGraph)
    """
    #nx.write_gml(graph, "transfer_network.gml", )
    graph = nx.read_gml("transfer_network.gml")
    print("graph loaded")
    fig, ax = plt.subplots(figsize=(30, 16))
    print("subplots created")
    nx.draw(graph, node_size=10)
    print("graph drawn, showing")
    plt.show()
    