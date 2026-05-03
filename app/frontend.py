import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd

from optimizer.dijkstra import build_graph, shortest_path
from optimizer.astar import astar_path
from optimizer.brute_force import brute_force_shortest_path


st.title("Shipping Route Optimizer")
# st.markdown("**Accurate results without lying to ourselves**")


# routes = pd.read_csv("data/global_routes.csv")

routes = pd.read_csv("data/generated_routes.csv")

#############


df = pd.read_csv("data/generated_routes.csv")
print(df.head())
print(len(df))
print(df.describe())

st.subheader("Generated Routes Dataset Debug Summary")
st.write("Preview of generated routes:")
st.dataframe(routes.head())
st.write("Total generated routes:")
st.write(len(routes))
st.write("Numeric summary statistics:")
st.dataframe(routes.describe())

#############

graph = build_graph(routes)

ports = sorted(set(routes["origin_port"]).union(set(routes["destination_port"])))

st.write("Graph nodes:", graph.number_of_nodes())
st.write("Graph edges:", graph.number_of_edges())

s = st.selectbox("Start", ports)
e = st.selectbox("End", ports)

if st.button("Run"):

    if s == e:
        st.warning("Start and destination must be different.")
        st.stop()

    try:
        d_p, d_c = shortest_path(graph, s, e)

    except Exception as err:
        st.error(f"No valid Dijkstra route found: {err}")
        st.stop()

    try:
        a_p, a_c = astar_path(graph, s, e)

    except Exception as err:
        a_p, a_c = "FAILED", str(err)

    try:
        b_p, b_c = brute_force_shortest_path(routes, s, e)

    except Exception as err:
        b_p, b_c = "N/A", str(err)

    results = pd.DataFrame([
        {
            "Algorithm": "Dijkstra",
            "Route": " → ".join(d_p),
            "Cost": d_c
        },
        {
            "Algorithm": "A*",
            "Route": " → ".join(a_p) if isinstance(a_p, list) else a_p,
            "Cost": a_c
        },
        {
            "Algorithm": "Brute Force",
            "Route": " → ".join(b_p) if isinstance(b_p, list) else b_p,
            "Cost": b_c
        }
    ])

    st.subheader("Algorithm Comparison")
    st.dataframe(results)

    if isinstance(a_p, list) and d_p == a_p:
        st.success("Dijkstra and A* agree.")
    else:
        st.warning("Dijkstra and A* do not agree or A* failed.")
        
        
            
    results = pd.DataFrame([
        {
            "Algorithm": "Dijkstra",
            "Route": " → ".join(d_p),
            "Cost": d_c
        },
        {
            "Algorithm": "A*",
            "Route": " → ".join(a_p),
            "Cost": a_c
        },
        {
            "Algorithm": "Brute Force",
            "Route": " → ".join(b_p),
            "Cost": b_c
        }
    ])
    
    st.subheader("Algorithm Comparison")
    st.dataframe(results)
    
    if d_c == a_c == b_c:
        st.success("✔ All algorithms agree: Validation PASSED")
    else:
        st.error("❌ Algorithm mismatch detected: Debug required")
        
        
        
        
        
        
        