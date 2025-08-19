from pathlib import Path
import pandas as pd
import numpy as np
import re

# ==== CONFIG ====
# DATA_DIR = Path("data/processed")     # change if needed
NODES = "subset_nodes.csv"     # your full nodes file
EDGES = "subset_edges.csv"     # your full edges file

# Columns you expect (script auto-intersects with actual headers)
NODE_COLS = ["osmid","y","x","street_count","highway","ref","railway","geometry"]
EDGE_COLS = ["u","v","key","osmid","highway","lanes","maxspeed","name","oneway",
             "ref","reversed","length","bridge","tunnel","geometry","width","access","junction"]

# ===== Helpers =====
def hdr(path):
    try:
        return pd.read_csv(path, nrows=0).columns
    except Exception as e:
        print(f"[ERROR] Failed reading headers from {path}: {e}")
        raise

def pct(n, d):
    return f"{(100*n/d):.2f}%" if d else "n/a"

# ===== Load with only needed columns =====
node_headers = hdr(NODES)
edge_headers = hdr(EDGES)
use_node_cols = [c for c in NODE_COLS if c in node_headers]
use_edge_cols = [c for c in EDGE_COLS if c in edge_headers]

print("== Loading files ==")
nodes = pd.read_csv(NODES, usecols=use_node_cols, low_memory=False)
edges = pd.read_csv(EDGES, usecols=use_edge_cols, low_memory=False)
print(f"nodes: {nodes.shape} columns={list(nodes.columns)}")
print(f"edges: {edges.shape} columns={list(edges.columns)}\n")

# ===== Basic dtypes / NA =====
print("== Dtypes ==")
print(nodes.dtypes, "\n")
print(edges.dtypes, "\n")

print("== Missing values (top 10) ==")
print("nodes NA:\n", nodes.isna().sum().sort_values(ascending=False).head(10), "\n")
print("edges NA:\n", edges.isna().sum().sort_values(ascending=False).head(10), "\n")

# ===== Node-level checks =====
issues = []

if "osmid" in nodes:
    dup_nodes = nodes["osmid"].duplicated().sum()
    if dup_nodes:
        issues.append(f"[WARN] {dup_nodes} duplicate node osmids")
    print(f"Unique node osmids: {nodes['osmid'].nunique()} (dups: {dup_nodes})")

if {"y","x"}.issubset(nodes.columns):
    # Rough SF bounds; adjust if needed
    lat_min, lat_max = nodes["y"].min(), nodes["y"].max()
    lon_min, lon_max = nodes["x"].min(), nodes["x"].max()
    print(f"Latitude range: {lat_min:.6f} .. {lat_max:.6f}")
    print(f"Longitude range: {lon_min:.6f} .. {lon_max:.6f}")
    if not (37.5 <= lat_min <= 38.2 and 37.5 <= lat_max <= 38.2):
        issues.append("[WARN] Node latitude range looks unusual for SF")
    if not (-122.7 <= lon_min <= -122.2 and -122.7 <= lon_max <= -122.2):
        issues.append("[WARN] Node longitude range looks unusual for SF")

print()

# ===== Edge-level checks =====
# Ensure numeric endpoints
for col in ("u","v"):
    if col in edges and edges[col].dtype == object:
        edges[col] = pd.to_numeric(edges[col], errors="coerce")

# Basic counts
print("== Edge integrity ==")
if "length" in edges:
    neg_len = (edges["length"] < 0).sum()
    print(f"edges with negative length: {neg_len} ({pct(neg_len, len(edges))})")
    if neg_len:
        issues.append(f"[WARN] {neg_len} edges have negative length")

# Endpoint coverage: u,v must exist in node osmid
if {"u","v"}.issubset(edges.columns) and "osmid" in nodes.columns:
    node_ids = set(nodes["osmid"].dropna().astype("int64"))
    missing_u = (~edges["u"].isin(node_ids)).sum()
    missing_v = (~edges["v"].isin(node_ids)).sum()
    print(f"edges with u NOT in nodes: {missing_u} ({pct(missing_u, len(edges))})")
    print(f"edges with v NOT in nodes: {missing_v} ({pct(missing_v, len(edges))})")
    if missing_u or missing_v:
        issues.append("[WARN] Some edges reference endpoints not present in nodes")

# Duplicate edge pairs (directed)
if {"u","v"}.issubset(edges.columns):
    dup_edge_pairs = edges.duplicated(subset=["u","v","key"] if "key" in edges else ["u","v"]).sum()
    print(f"duplicate (u,v[,key]) rows: {dup_edge_pairs}")
    if dup_edge_pairs:
        issues.append(f"[WARN] {dup_edge_pairs} duplicate edge rows")

# One-way distribution (if string flags)
if "oneway" in edges:
    oneway_counts = edges["oneway"].value_counts(dropna=False)
    print("\noneway distribution:\n", oneway_counts, "\n")

# Maxspeed quick parse (optional: first mph to kph)
if "maxspeed" in edges:
    def mph_to_kph_first(s):
        if pd.isna(s): return None
        m = re.search(r"(\d+)\s*mph", str(s))
        return int(m.group(1))*1.60934 if m else None
    parsed = edges["maxspeed"].dropna().head(2000).map(mph_to_kph_first)
    pct_parsed = parsed.notna().mean() if len(parsed) else 0
    print(f"maxspeed parse (first 2000 rows): parsed {pct_parsed*100:.1f}% to kph (sample)")
    # (You can add a real column later if needed)

# ===== Connectivity sketch: degree on subset of edges =====
if {"u","v"}.issubset(edges.columns) and "osmid" in nodes.columns:
    deg = pd.concat([edges["u"], edges["v"]]).value_counts()
    isolated = (~nodes["osmid"].isin(deg.index)).sum()
    print(f"\nAvg node degree (approx): {deg.mean():.2f}")
    print(f"Isolated nodes (no incident edges): {isolated} ({pct(isolated, len(nodes))})")

# ===== Sample rows =====
print("\n== Samples ==")
print("nodes sample:\n", nodes.sample(min(5, len(nodes)), random_state=0), "\n")
print("edges sample:\n", edges.sample(min(5, len(edges)), random_state=0), "\n")

# ===== Final summary =====
print("== Summary ==")
if issues:
    for msg in issues:
        print(msg)
else:
    print("No obvious issues found in quick checks.")
