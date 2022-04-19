from pyspark.sql import SparkSession
import networkx as nx
import matplotlib.pyplot as plt

spark = SparkSession \
    .builder \
    .appName("MAP Polkadot Pyspark") \
    .config("spark.jars", "./postgresql-42.2.6.jar") \
    .getOrCreate()

df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://localhost:5432/map") \
    .option("dbtable", "transfer") \
    .option("user", "mapUser") \
    .option("password", "mapmap") \
    .option("driver", "org.postgresql.Driver") \
    .load()


from_address = df.select("from_address").collect()
to_address = df.select("to_address").collect()

directed_graph = nx.DiGraph()
directed_graph.add_edges_from(list(zip(from_address, to_address)))

pos = nx.spring_layout(directed_graph)
nx.draw_networkx(directed_graph, pos=nx.spring_layout(directed_graph),
                 with_labels=False, node_size=50)
plt.figure(figsize=(1500,1500))
plt.show()

