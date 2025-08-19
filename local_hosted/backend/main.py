# backend/main.py
from fastapi import FastAPI, HTTPException, Query
import pandas as pd, networkx as nx, os
from typing import Optional, List, Dict



app = FastAPI(title="SF Traffic API")

# --- load CSVs relative to this file ---
HERE = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(HERE, "..", "data"))
nodes_path = os.path.join(DATA_DIR, "nodes.csv")
edges_path = os.path.join(DATA_DIR, "edges.csv")

nodes_df = pd.read_csv(nodes_path)
edges_df = pd.read_csv(edges_path)

# normalize types
nodes_df["osmid"] = nodes_df["osmid"].astype(str)
edges_df["u"] = edges_df["u"].astype(str)
edges_df["v"] = edges_df["v"].astype(str)
if "real" in edges_df.columns:
    edges_df["real"] = edges_df["real"].astype(str).str.lower().isin(["1", "true", "yes"])
else:
    edges_df["real"] = True

# build graph
G = nx.Graph()
for _, r in nodes_df.iterrows():
    G.add_node(r["osmid"], x=float(r["x"]), y=float(r["y"]))
for _, r in edges_df.iterrows():
    attrs = {"real": bool(r["real"])}
    if "length" in r and pd.notna(r["length"]): attrs["length"] = float(r["length"])
    if "name" in r and pd.notna(r["name"]):     attrs["name"]   = str(r["name"])
    G.add_edge(r["u"], r["v"], **attrs)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    comps = list(nx.connected_components(G))
    return {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "num_components": len(comps),
        "largest_component_size": max((len(c) for c in comps), default=0),
    }

@app.get("/shortest-path")
def shortest_path(
    source: str = Query(..., alias="source"),
    target: str = Query(..., alias="target"),
    use_length: bool = Query(False, alias="use_length"),
):
    if source not in G or target not in G:
        raise HTTPException(status_code=404, detail="Source or target not in graph")
    weight = "length" if use_length and all("length" in G[u][v] for u, v in G.edges) else None
    try:
        path = nx.shortest_path(G, source=source, target=target, weight=weight)
        return {"path": path}
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path between nodes")


@app.get("/shortest-path-detail")
def shortest_path_detail(
    source: str = Query(..., alias="source"),
    target: str = Query(..., alias="target"),
    use_length: bool = Query(False, alias="use_length"),
):
    if source not in G or target not in G:
        raise HTTPException(status_code=404, detail="Source or target not in graph")

    weight = "length" if use_length and all("length" in G[u][v] for u, v in G.edges) else None

    try:
        path: List[str] = nx.shortest_path(G, source=source, target=target, weight=weight)
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path between nodes")

    segments: List[Dict[str, Optional[str]]] = []
    total_length = 0.0
    total_length_ok = True

    for a, b in zip(path, path[1:]):
        edata = G[a][b]
        name = edata.get("name")
        length = edata.get("length")
        seg = {
            "from_osmid": a,
            "to_osmid": b,
            "road_name": name if name is not None else None,
            "length": float(length) if length is not None else None,
        }
        segments.append(seg)
        if length is None:
            total_length_ok = False
        else:
            total_length += float(length)

    return {
        "segments": segments,
        "total_hops": max(0, len(path) - 1),
        "total_length": (total_length if total_length_ok else None),
        "weighted": bool(weight),
        "path_nodes": path,  # keep the raw nodes too (optional)
    }


# --- Path as coordinates for mapping ---

@app.get("/path-geo")
def path_geo(
    source: str = Query(...),
    target: str = Query(...),
    use_length: bool = Query(False),
):
    if source not in G or target not in G:
        raise HTTPException(status_code=404, detail="Source or target not in graph")

    weight = "length" if use_length and all("length" in G[u][v] for u, v in G.edges) else None
    try:
        path: List[str] = nx.shortest_path(G, source=source, target=target, weight=weight)
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path between nodes")

    # Build node list with coords (assumes x=lon, y=lat)
    nodes_geo: List[Dict[str, Optional[float]]] = []
    coords: List[List[float]] = []
    for n in path:
        node = G.nodes[n]
        lon = node.get("x")
        lat = node.get("y")
        if lon is None or lat is None:
            raise HTTPException(status_code=400, detail=f"Node {n} missing coordinates x/y")
        nodes_geo.append({"id": n, "lon": float(lon), "lat": float(lat)})
        coords.append([float(lon), float(lat)])

    return {
        "nodes": nodes_geo,     # for scatter/markers
        "line": coords,         # for a path line
        "path_nodes": path,     # raw ids too
        "weighted": bool(weight)
    }
# --- Entire graph as line segments for mapping ---
from typing import List, Dict, Optional

@app.get("/graph-geo")
def graph_geo():
    """
    Returns all edges as line segments with coordinates.
    Assumes node attrs: x = lon, y = lat.
    """
    edges_real: List[Dict[str, float]] = []
    edges_art: List[Dict[str, float]] = []

    # Build line segments from node coords
    for u, v, edata in G.edges(data=True):
        nu = G.nodes[u]; nv = G.nodes[v]
        lon1, lat1 = nu.get("x"), nu.get("y")
        lon2, lat2 = nv.get("x"), nv.get("y")
        if lon1 is None or lat1 is None or lon2 is None or lat2 is None:
            continue
        item = {
            "lon1": float(lon1), "lat1": float(lat1),
            "lon2": float(lon2), "lat2": float(lat2),
        }
        if edata.get("real", True):
            edges_real.append(item)
        else:
            edges_art.append(item)

    # Choose a reasonable center (mean of first 5 nodes with coords)
    lons, lats = [], []
    for n, nd in list(G.nodes(data=True))[: min(200, G.number_of_nodes())]:
        if "x" in nd and "y" in nd:
            lons.append(float(nd["x"]))
            lats.append(float(nd["y"]))
    center = {
        "lon": (sum(lons) / len(lons)) if lons else -122.4194,
        "lat": (sum(lats) / len(lats)) if lats else 37.7749,
    }

    return {
        "edges_real": edges_real,
        "edges_artificial": edges_art,
        "center": center,
    }
