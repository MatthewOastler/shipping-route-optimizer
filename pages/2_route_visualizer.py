# import matplotlib.pyplot as plt
# import networkx as nx

# def plot_route(G,path):
#  pos=nx.spring_layout(G,seed=1)
#  nx.draw(G,pos,with_labels=True,node_color='lightblue')
#  nx.draw_networkx_edges(G,pos,edgelist=list(zip(path,path[1:])),edge_color='red',width=3)
#  plt.show()







# pages/2_route_visualizer.py

import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from optimizer.dijkstra import build_graph, shortest_path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Route Visualizer",
    layout="wide"
)

st.title("Route Visualizer")

st.caption(
    "Accurate results without lying to ourselves"
)

# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"

routes = pd.read_csv(ROUTES_FILE)

graph = build_graph(routes)

ports = sorted(
    set(routes["origin_port"]).union(
        set(routes["destination_port"])
    )
)

# ============================================================
# INPUTS
# ============================================================

col1, col2 = st.columns(2)

with col1:
    start_port = st.selectbox(
        "Origin Port",
        ports
    )

with col2:
    end_port = st.selectbox(
        "Destination Port",
        ports
    )

# ============================================================
# VISUALIZE
# ============================================================

if st.button("Visualize Route"):

    try:

        path, cost = shortest_path(
            graph,
            start_port,
            end_port
        )

    except Exception as err:

        st.error(
            f"Unable to calculate route: {err}"
        )

        st.stop()

    # ========================================================
    # ROUTE DETAILS
    # ========================================================

    st.subheader("Selected Route")

    st.write(
        " → ".join(path)
    )

    st.write(
        f"Total Cost: {round(cost, 2)}"
    )

    # ========================================================
    # ROUTE BREAKDOWN
    # ========================================================

    rows = []

    for i in range(len(path) - 1):

        origin = path[i]
        destination = path[i + 1]

        edge = graph[origin][destination]

        rows.append({

            "From": origin,
            "To": destination,

            "Distance NM":
                round(edge["distance"], 2),

            "Fuel Cost":
                round(edge["fuel_cost"], 2),

            "Weather Risk":
                round(edge["weather_risk"], 2),

            "Piracy Risk":
                round(edge["piracy_risk"], 2),

            "Carbon Cost":
                round(edge["carbon_cost"], 2),

            "Total Cost":
                round(edge["total_cost"], 2)

        })

    st.subheader("Route Leg Details")

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

    # ========================================================
    # NETWORK VISUALIZATION
    # ========================================================

    st.subheader("Network Visualization")

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    pos = nx.spring_layout(
        graph,
        seed=42
    )

    # Base graph
    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=600,
        ax=ax
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=8,
        ax=ax
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        alpha=0.25,
        ax=ax
    )

    # Highlight chosen route
    route_edges = list(
        zip(path, path[1:])
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        edgelist=route_edges,
        width=4,
        edge_color="red",
        ax=ax
    )

    ax.set_title(
        "Optimal Route Highlighted"
    )

    ax.axis("off")

    st.pyplot(fig)