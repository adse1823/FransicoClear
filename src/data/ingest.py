from collections import defaultdict
from itertools import combinations
from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import re

# Load CSV
df = pd.read_csv("data/raw/Street_intersections.csv")

# Rename for convenience
df.rename(columns={"the_geom": "geom"}, inplace=True)

# Extract latitude and longitude from 'POINT (lon lat)'
def extract_lat_lon(geom_str):
    match = re.match(r"POINT \((-?\d+\.\d+)\s+(-?\d+\.\d+)\)", geom_str)
    if match:
        lon, lat = map(float, match.groups())
        return lat, lon
    return None, None

df['LATITUDE'], df['LONGITUDE'] = zip(*df['geom'].map(extract_lat_lon))
df = df[['cnn', 'st_name', 'st_type', 'LATITUDE', 'LONGITUDE']].dropna()
df.drop_duplicates(subset='cnn', inplace=True)


# Normalize street names
df['st_name'] = df['st_name'].str.upper()
df['st_type'] = df['st_type'].str.upper()


# Initialize graph
G = nx.Graph()

# Add nodes to graph
for _, row in df.iterrows():
    G.add_node(
        row['cnn'],
        street1=row['st_name'],
        street2=row['st_type'],
        lat=row['LATITUDE'],
        lon=row['LONGITUDE']
    )


# Group intersections by street name
street_to_cnn = defaultdict(set)
for _, row in df.iterrows():
    street_to_cnn[row['st_name']].add(row['cnn'])
    street_to_cnn[row['st_type']].add(row['cnn'])


edge_count = 0
for street, cnn_list in street_to_cnn.items():
    for cnn1, cnn2 in combinations(cnn_list, 2):
        if not G.has_edge(cnn1, cnn2):
            G.add_edge(cnn1, cnn2, street=street)
            edge_count += 1

print(f"✅ Graph created with {G.number_of_nodes()} intersections and {G.number_of_edges()} edges.")
print(G)


subgraph = G.subgraph(list(G.nodes)[:300])  # sample for plotting
pos = {node: (data['lon'], data['lat']) for node, data in subgraph.nodes(data=True)}

plt.figure(figsize=(10, 10))
nx.draw(subgraph, pos, node_size=10, edge_color="gray", with_labels=False)
plt.title("Sample of SF Road Graph (First 300 Nodes)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True)
plt.show()

