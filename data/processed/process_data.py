import pandas as pd


# NODE_COLS = ["osmid","y","x","street_count","highway","ref","railway","geometry"]
# EDGE_COLS = ["u","v","key","osmid","highway","lanes","maxspeed","name","oneway",
#              "ref","reversed","length","bridge","tunnel","geometry","width","access","junction"]


# # Auto-intersect with actual file headers to avoid KeyErrors
# node_headers = pd.read_csv('sf_nodes.csv', nrows=0).columns
# edge_headers = pd.read_csv('sf_edges.csv', nrows=0).columns
# use_node_cols = [c for c in NODE_COLS if c in node_headers]
# use_edge_cols = [c for c in EDGE_COLS if c in edge_headers]


# min_lat, max_lat = 37.70, 37.7462
# min_lon, max_lon = -122.52, -122.4657

# nodes = pd.read_csv('sf_nodes.csv', usecols=use_node_cols)
# nodes_box = nodes[nodes["y"].between(min_lat, max_lat) & nodes["x"].between(min_lon, max_lon)].copy()
# nodes_sub = nodes_box.copy()  # cap to ~1000 if you want a fixed size
# keep_osmids = set(nodes_sub["osmid"])

# print(len(keep_osmids))


# nodes_sub.to_csv('subset_nodes.csv',index=False)


# edges = pd.read_csv('sf_edges.csv',usecols=use_edge_cols, low_memory=False)

# edges["u"] = pd.to_numeric(edges["u"], errors="coerce")
# edges["v"] = pd.to_numeric(edges["v"], errors="coerce")

# edges_sub = edges[edges["u"].isin(keep_osmids) & edges["v"].isin(keep_osmids)].copy()
# print(edges_sub)
# edges_sub.to_csv('subset_edges.csv', index=False)


