# frontend/app.py
import os
import math
import streamlit as st
from streamlit_folium import st_folium
import folium
import requests

# ---- Config (defaults; can override via env) ----
API_BASE = os.getenv("API_BASE", f"http://localhost:{os.getenv('API_PORT','8000')}").rstrip("/")

st.set_page_config(page_title="SF Traffic MVP (Minimal)", 
                   layout="wide")

st.title("SF Traffic — Minimal MVP")
st.caption("Graph stats + city map. Toggle changes line thickness by edge length (if available).")

# ---- Sidebar: stats + toggle ----
with st.sidebar:
    st.subheader("Backend")
    try:
        r = requests.get(f"{API_BASE}/stats", timeout=20)
        r.raise_for_status()
        s = r.json()
        st.success(f"{s['num_nodes']} nodes · {s['num_edges']} edges · {s['num_components']} components")
    except Exception as e:
        st.error(f"API not reachable: {e}")
        st.stop()

    weight_by_length = st.checkbox("Use length as weight", value=True,
                                   help="Thicker lines for longer edges (if 'length' exists).")

# ---- Fetch graph geometry ----
try:
    r = requests.get(f"{API_BASE}/graph-geo", timeout=60)
    r.raise_for_status()
    geo = r.json()
except Exception as e:
    st.error(f"Could not load map data: {e}")
    st.stop()

center = geo["center"]
m = folium.Map(location=[center["lat"], center["lon"]], zoom_start=13, tiles="cartodbpositron")

# Compute normalization for lengths (if present)
max_len = None
if weight_by_length:
    lengths = [e.get("length") for e in geo["edges_real"] if "length" in e and e["length"] is not None]
    max_len = max(lengths) if lengths else None

def edge_weight(item):
    if not weight_by_length or max_len is None:
        return 1.5  # default thin line
    # normalize 0..1, map to 1.5..6 px (log-ish for visual balance)
    L = max(0.0, min(1.0, float(item.get("length", 0.0)) / (max_len or 1.0)))
    return 1.5 + 4.5 * math.sqrt(L)

# Draw real edges
for e in geo["edges_real"]:
    w = edge_weight(e)
    folium.PolyLine([(e["lat1"], e["lon1"]), (e["lat2"], e["lon2"])], weight=w, opacity=0.8).add_to(m)

# Draw artificial edges lighter/dashed (if any)
for e in geo["edges_artificial"]:
    folium.PolyLine([(e["lat1"], e["lon1"]), (e["lat2"], e["lon2"])],
                    weight=1, opacity=0.4, dash_array="4").add_to(m)

st_folium(m, use_container_width=True, returned_objects=[])
