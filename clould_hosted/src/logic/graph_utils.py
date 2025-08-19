import pandas as pd
import networkx as nx

# Paths to your subset files
nodes_csv = "data/processed/subset_nodes.csv"
edges_csv = "data/processed/subset_edges.csv"

# Load
nodes = pd.read_csv(nodes_csv)
edges = pd.read_csv(edges_csv)

# Ensure IDs are numeric
nodes["osmid"] = pd.to_numeric(nodes["osmid"], errors="raise")
edges["u"] = pd.to_numeric(edges["u"], errors="raise")
edges["v"] = pd.to_numeric(edges["v"], errors="raise")

# Build directed graph
G = nx.DiGraph()

# Add nodes with attributes (everything except 'osmid' becomes attributes)
for row in nodes.itertuples(index=False):
    d = row._asdict()
    osmid = int(d.pop("osmid"))
    G.add_node(osmid, **d)

# Add edges with attributes (everything except u,v becomes attributes)
for row in edges.itertuples(index=False):
    d = row._asdict()
    u = int(d.pop("u")); v = int(d.pop("v"))
    G.add_edge(u, v, **d)

print("✅ Graph built:", G.number_of_nodes(), "nodes,", G.number_of_edges(), "edges")


# take a small induced subgraph around a seed node
seed = next(iter(G.nodes()))
nbrs = set(nx.single_source_shortest_path_length(G.to_undirected(), seed, cutoff=2).keys())
V = list(nbrs)[:200]  # cap to 200 nodes for plotting
H = G.subgraph(V).copy()

# quick draw (matplotlib) — positions from (x,y) if available
import matplotlib.pyplot as plt
pos = {n:(d.get("x",0), d.get("y",0)) for n,d in H.nodes(data=True)}
nx.draw(H, pos=pos if all(v!=(0,0) for v in pos.values()) else None,
        node_size=10, width=0.5, with_labels=False)
plt.show()
