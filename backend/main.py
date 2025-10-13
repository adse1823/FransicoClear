# backend/main.py
import os
import pandas as pd
import networkx as nx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---- Config (defaults; can override via env) ----
DATA_DIR = os.getenv("DATA_DIR", "./data")
UI_PORT = os.getenv("UI_PORT", "8501")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", f"http://localhost:{UI_PORT}").split(",")

# ---- Load CSVs & build graph on startup ----
def load_graph():
    # Accept common column names
    def pick(cols, options):
        for c in options:
            if c in cols: return c
        raise KeyError(f"Expected one of {options} in {list(cols)}")

    # nodes = pd.read_csv(os.path.join(DATA_DIR, "nodes.csv"))
    # edges = pd.read_csv(os.path.join(DATA_DIR, "edges.csv"))

    nodes = pd.read_csv('../data/nodes.csv')
    edges = pd.read_csv('../data/edges.csv')

    nid = pick(nodes.columns, ["osmid", "id", "node_id"])
    xcol = pick(nodes.columns, ["x", "lon", "longitude"])
    ycol = pick(nodes.columns, ["y", "lat", "latitude"])

    nodes = nodes.rename(columns={nid: "id", xcol: "x", ycol: "y"})
    nodes["id"] = nodes["id"].astype(str)
    nodes["x"] = nodes["x"].astype(float)
    nodes["y"] = nodes["y"].astype(float)

    # Standardize edges
    if "u" not in edges.columns or "v" not in edges.columns:
        raise KeyError("edges.csv must include 'u' and 'v' columns")
    edges["u"] = edges["u"].astype(str)
    edges["v"] = edges["v"].astype(str)
    if "length" in edges.columns:
        edges.loc[edges["length"].notna(), "length"] = edges.loc[
            edges["length"].notna(), "length"
        ].astype(float)
    if "real" not in edges.columns:
        edges["real"] = True
    else:
        edges["real"] = edges["real"].astype(str).str.lower().isin(["1", "true", "yes"])

    G = nx.Graph()
    for r in nodes.itertuples(index=False):
        G.add_node(r.id, x=float(r.x), y=float(r.y))
    for r in edges.itertuples(index=False):
        attrs = {"real": bool(getattr(r, "real", True))}
        if hasattr(r, "length") and pd.notna(r.length):
            attrs["length"] = float(r.length)
        if hasattr(r, "name") and pd.notna(r.name):
            attrs["name"] = str(r.name)
        G.add_edge(r.u, r.v, **attrs)

    return G

app = FastAPI(title="SF Traffic MVP (Minimal)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

G: nx.Graph = load_graph()

# ---- Endpoints ----

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

@app.get("/graph-geo")
def graph_geo():
    """Return edges as simple line segments and a reasonable center."""
    edges_real, edges_art = [], []
    for u, v, ed in G.edges(data=True):
        nu, nv = G.nodes[u], G.nodes[v]
        if "x" in nu and "y" in nu and "x" in nv and "y" in nv:
            item = {
                "lon1": float(nu["x"]),
                "lat1": float(nu["y"]),
                "lon2": float(nv["x"]),
                "lat2": float(nv["y"]),
            }
            # include length if present so the UI can weight line thickness
            if "length" in ed:
                item["length"] = float(ed["length"])
            (edges_real if ed.get("real", True) else edges_art).append(item)

    # simple center: average of first up-to-200 nodes with coords
    lons, lats = [], []
    for _, nd in list(G.nodes(data=True))[: min(200, G.number_of_nodes())]:
        if "x" in nd and "y" in nd:
            lons.append(float(nd["x"]))
            lats.append(float(nd["y"]))
    center = {
        "lon": (sum(lons) / len(lons)) if lons else -122.4194,
        "lat": (sum(lats) / len(lats)) if lats else 37.7749,
    }

    return {"edges_real": edges_real, "edges_artificial": edges_art, "center": center}
