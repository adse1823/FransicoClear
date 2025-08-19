import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(page_title="San Francisco Traffic Graph", layout="wide")
st.title("San Francisco Traffic Graph")

# --- Section: Graph Stats ---
st.subheader("Graph Stats")
if st.button("Get Stats", key="btn_stats"):
    r = requests.get(f"{API_BASE}/stats", timeout=10)
    st.json(r.json() if r.ok else {"error": r.status_code, "text": r.text})

st.divider()

# --- Section: Shortest Path (Detailed Table) ---
st.subheader("Find Shortest Path (Detailed Table)")

col1, col2, col3 = st.columns([2,2,2])

with col1:
    src = st.text_input("Source node ID", "1", key="src_detail")
with col2:
    dst = st.text_input("Target node ID", "3", key="dst_detail")
with col3:
    use_len = st.checkbox("Use 'length' weight", value=False, key="use_len_detail")

if st.button("Compute Path (Table)", key="btn_detail"):
    if not src or not dst:
        st.warning("Please enter both source and target node IDs.")
    else:
        try:
            params = {"source": src, "target": dst, "use_length": str(use_len).lower()}
            r = requests.get(f"{API_BASE}/shortest-path-detail", params=params, timeout=20)
            if not r.ok:
                st.error(f"/shortest-path-detail {r.status_code}: {r.text}")
            else:
                data = r.json()
                segments = data.get("segments", [])
                if not segments:
                    st.info("No segments returned.")
                else:
                    df = pd.DataFrame(segments, columns=["from_osmid", "to_osmid", "road_name", "length"])
                    st.markdown("**Path Segments**")
                    st.dataframe(df, use_container_width=True)

                # Optional summary
                st.caption(
                    f"Hops: {data.get('total_hops')}  •  "
                    f"Weighted: {data.get('weighted')}  •  "
                    f"Total length: {data.get('total_length') if data.get('total_length') is not None else '(n/a)'}"
                )
        except Exception as e:
            st.error(f"Request failed: {e}")

import os, requests, pandas as pd, streamlit as st, pydeck as pdk

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
st.set_page_config(page_title="San Francisco Traffic Graph", layout="wide")
st.title("San Francisco Traffic Graph")

# --- existing sections (stats / table) stay as-is ---

st.divider()
st.subheader("Map View: Shortest Path")

colA, colB, colC = st.columns([2,2,2])
with colA:
    src_map = st.text_input("Source node ID (map)", value="1", key="src_map")
with colB:
    dst_map = st.text_input("Target node ID (map)", value="3", key="dst_map")
with colC:
    use_len_map = st.checkbox("Use 'length' weight (map)", value=False, key="use_len_map")

if st.button("Show on Map", key="btn_map"):
    try:
        params = {"source": src_map, "target": dst_map, "use_length": str(use_len_map).lower()}
        r = requests.get(f"{API_BASE}/path-geo", params=params, timeout=20)
        if not r.ok:
            st.error(f"/path-geo {r.status_code}: {r.text}")
        else:
            data = r.json()
            nodes = data["nodes"]          # [{id, lon, lat}, ...]
            line_coords = data["line"]     # [[lon, lat], ...]

            if not nodes:
                st.info("No nodes to plot.")
            else:
                # Center view on first node
                center_lon, center_lat = nodes[0]["lon"], nodes[0]["lat"]

                # Layers: path line + endpoints
                path_layer = pdk.Layer(
                    "PathLayer",
                    data=[{"path": [[c[0], c[1]] for c in line_coords], "name": "route"}],
                    get_path="path",
                    width_scale=1,
                    width_min_pixels=4,
                    get_color=[0, 0, 255, 180],
                    pickable=True,
                )
                nodes_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=nodes,
                    get_position="[lon, lat]",
                    get_radius=8,
                    radius_min_pixels=4,
                    get_fill_color=[255, 0, 0, 200],
                    pickable=True,
                )

                deck = pdk.Deck(
                    initial_view_state=pdk.ViewState(
                        longitude=center_lon,
                        latitude=center_lat,
                        zoom=13,
                        pitch=0,
                        bearing=0,
                    ),
                    layers=[path_layer, nodes_layer],
                    map_style="mapbox://styles/mapbox/light-v9",  # optional; works without Mapbox token
                    tooltip={"text": "{name}"},
                )
                st.pydeck_chart(deck, use_container_width=True)

                # Optional: show node table under the map
                st.caption("Path nodes (lon/lat)")
                st.dataframe(pd.DataFrame(nodes), use_container_width=True)

    except Exception as e:
        st.error(f"Map request failed: {e}")

import os, requests, pandas as pd, streamlit as st, pydeck as pdk

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.divider()
st.subheader("Map View: Full Network + Shortest Path")

c1, c2, c3, c4 = st.columns([2,2,2,2])
with c1:
    src_map = st.text_input("Source node ID (map)", value="1", key="src_map2")
with c2:
    dst_map = st.text_input("Target node ID (map)", value="3", key="dst_map2")
with c3:
    use_len_map = st.checkbox("Use 'length' weight (map)", value=False, key="use_len_map2")
with c4:
    zoom_level = st.slider("Zoom", 8, 18, 13, key="zoom_map2")

if st.button("Show Network + Route", key="btn_map2"):
    try:
        # 1) Fetch the whole graph (edges)
        g = requests.get(f"{API_BASE}/graph-geo", timeout=30)
        if not g.ok:
            st.error(f"/graph-geo {g.status_code}: {g.text}")
            st.stop()
        graph = g.json()

        # 2) Fetch the route
        params = {"source": src_map, "target": dst_map, "use_length": str(use_len_map).lower()}
        r = requests.get(f"{API_BASE}/path-geo", params=params, timeout=30)
        if not r.ok:
            st.error(f"/path-geo {r.status_code}: {r.text}")
            st.stop()
        route = r.json()

        # Prepare DataFrames for pydeck LineLayers
        real_df = pd.DataFrame(graph["edges_real"])
        art_df  = pd.DataFrame(graph["edges_artificial"])
        route_line = route["line"]  # [[lon, lat], ...]

        # Center the view
        center_lon = graph["center"]["lon"]
        center_lat = graph["center"]["lat"]

        layers = []

        # Background: real edges (light gray)
        if not real_df.empty:
            layers.append(
                pdk.Layer(
                    "LineLayer",
                    data=real_df,
                    get_source_position=["lon1", "lat1"],
                    get_target_position=["lon2", "lat2"],
                    get_width=1,
                    get_color=[180, 180, 180, 120],  # light gray
                    pickable=False,
                )
            )

        # Background: artificial edges (faint orange)
        if not art_df.empty:
            layers.append(
                pdk.Layer(
                    "LineLayer",
                    data=art_df,
                    get_source_position=["lon1", "lat1"],
                    get_target_position=["lon2", "lat2"],
                    get_width=1,
                    get_color=[255, 140, 0, 100],  # orange-ish
                    pickable=False,
                )
            )

        # Foreground: route (distinct color + thicker)
        if route_line and len(route_line) >= 2:
            layers.append(
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": route_line, "name": "Shortest Path"}],
                    get_path="path",
                    width_scale=1,
                    width_min_pixels=5,
                    get_color=[0, 80, 255, 220],  # vivid blue
                    pickable=True,
                )
            )

        deck = pdk.Deck(
            initial_view_state=pdk.ViewState(
                longitude=center_lon,
                latitude=center_lat,
                zoom=zoom_level,
                pitch=0,
                bearing=0,
            ),
            layers=layers,
            map_style=None,  # works without a Mapbox token
            tooltip={"text": "{name}"},
        )

        st.pydeck_chart(deck, use_container_width=True)

        # Optional mini-table of route nodes
        if "nodes" in route and route["nodes"]:
            st.caption("Route node coordinates")
            st.dataframe(pd.DataFrame(route["nodes"]), use_container_width=True)

    except Exception as e:
        st.error(f"Map error: {e}")
