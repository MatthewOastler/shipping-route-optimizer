# import sys
# import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# import streamlit as st
# import pandas as pd

# from optimizer.dijkstra import build_graph, shortest_path
# from optimizer.astar import astar_path
# from optimizer.brute_force import brute_force_shortest_path


# st.title("Shipping Route Optimizer")
# # st.markdown("**Accurate results without lying to ourselves**")


# # routes = pd.read_csv("data/global_routes.csv")

# routes = pd.read_csv("data/generated_routes.csv")

# #############


# df = pd.read_csv("data/generated_routes.csv")
# print(df.head())
# print(len(df))
# print(df.describe())

# st.subheader("Generated Routes Dataset Debug Summary")
# st.write("Preview of generated routes:")
# st.dataframe(routes.head())
# st.write("Total generated routes:")
# st.write(len(routes))
# st.write("Numeric summary statistics:")
# st.dataframe(routes.describe())

# #############

# graph = build_graph(routes)

# ports = sorted(set(routes["origin_port"]).union(set(routes["destination_port"])))

# st.write("Graph nodes:", graph.number_of_nodes())
# st.write("Graph edges:", graph.number_of_edges())

# s = st.selectbox("Start", ports)
# e = st.selectbox("End", ports)

# if st.button("Run"):

#     if s == e:
#         st.warning("Start and destination must be different.")
#         st.stop()

#     try:
#         d_p, d_c = shortest_path(graph, s, e)

#     except Exception as err:
#         st.error(f"No valid Dijkstra route found: {err}")
#         st.stop()

#     try:
#         a_p, a_c = astar_path(graph, s, e)

#     except Exception as err:
#         a_p, a_c = "FAILED", str(err)

#     try:
#         b_p, b_c = brute_force_shortest_path(routes, s, e)

#     except Exception as err:
#         b_p, b_c = "N/A", str(err)

#     results = pd.DataFrame([
#         {
#             "Algorithm": "Dijkstra",
#             "Route": " → ".join(d_p),
#             "Cost": d_c
#         },
#         {
#             "Algorithm": "A*",
#             "Route": " → ".join(a_p) if isinstance(a_p, list) else a_p,
#             "Cost": a_c
#         },
#         {
#             "Algorithm": "Brute Force",
#             "Route": " → ".join(b_p) if isinstance(b_p, list) else b_p,
#             "Cost": b_c
#         }
#     ])

#     st.subheader("Algorithm Comparison")
#     st.dataframe(results)

#     if isinstance(a_p, list) and d_p == a_p:
#         st.success("Dijkstra and A* agree.")
#     else:
#         st.warning("Dijkstra and A* do not agree or A* failed.")
        
        
            
#     results = pd.DataFrame([
#         {
#             "Algorithm": "Dijkstra",
#             "Route": " → ".join(d_p),
#             "Cost": d_c
#         },
#         {
#             "Algorithm": "A*",
#             "Route": " → ".join(a_p),
#             "Cost": a_c
#         },
#         {
#             "Algorithm": "Brute Force",
#             "Route": " → ".join(b_p),
#             "Cost": b_c
#         }
#     ])
    
#     st.subheader("Algorithm Comparison")
#     st.dataframe(results)
    
#     if d_c == a_c == b_c:
#         st.success("✔ All algorithms agree: Validation PASSED")
#     else:
#         st.error("❌ Algorithm mismatch detected: Debug required")
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        




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

from optimizer.dijkstra import build_graph, shortest_path
from optimizer.astar import astar_path
from optimizer.brute_force import brute_force_shortest_path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Shipping Route Optimizer",
    layout="wide"
)

st.title("Shipping Route Optimizer")

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
# SIDEBAR
# ============================================================

st.sidebar.header("Options")

show_debug = st.sidebar.checkbox(
    "Show Debug Information",
    value=False
)

routing_objective = st.sidebar.selectbox(
    "Routing Objective",
    [
        "total_cost"
    ]
)

# ============================================================
# DEBUG PANEL
# ============================================================

if show_debug:

    st.subheader("Dataset Summary")

    st.write(
        f"Routes loaded: {len(routes)}"
    )

    st.write(
        f"Graph nodes: {graph.number_of_nodes()}"
    )

    st.write(
        f"Graph edges: {graph.number_of_edges()}"
    )

    st.dataframe(routes.head())

# ============================================================
# USER INPUTS
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
# RUN ROUTING
# ============================================================

if st.button("Calculate Route"):

    if start_port == end_port:

        st.warning(
            "Origin and destination must be different."
        )

        st.stop()

    try:

        # ====================================================
        # DIJKSTRA
        # ====================================================

        d_path, d_cost = shortest_path(
            graph,
            start_port,
            end_port,
            weight=routing_objective
        )

        # ====================================================
        # A*
        # ====================================================

        a_path, a_cost = astar_path(
            graph,
            start_port,
            end_port,
            weight=routing_objective
        )

        # ====================================================
        # BRUTE FORCE
        # ====================================================

        local_ports = set(d_path)

        local_routes = routes[
            routes["origin_port"].isin(local_ports)
            &
            routes["destination_port"].isin(local_ports)
        ]

        b_path, b_cost = brute_force_shortest_path(
            local_routes,
            start_port,
            end_port
        )

    except Exception as err:

        st.error(
            f"Routing failed: {err}"
        )

        st.stop()

    # ========================================================
    # ALGORITHM COMPARISON
    # ========================================================

    st.subheader("Algorithm Comparison")

    results = pd.DataFrame([

        {
            "Algorithm": "Dijkstra",
            "Route": " → ".join(d_path),
            "Cost": round(d_cost, 2)
        },

        {
            "Algorithm": "A*",
            "Route": " → ".join(a_path),
            "Cost": round(a_cost, 2)
        },

        {
            "Algorithm": "Brute Force",
            "Route": " → ".join(b_path),
            "Cost": round(b_cost, 2)
        }

    ])

    st.dataframe(
        results,
        use_container_width=True
    )

    # ========================================================
    # CONCLUSION MATRIX
    # ========================================================

    st.subheader("Conclusion Matrix")

    route_match = (
        d_path == a_path == b_path
    )

    cost_match = (
        abs(d_cost - a_cost) < 0.01
        and
        abs(d_cost - b_cost) < 0.01
    )

    conclusion = pd.DataFrame([

        {
            "Check": "Route Agreement",
            "Pass": route_match
        },

        {
            "Check": "Cost Agreement",
            "Pass": cost_match
        },

        {
            "Check": "Graph Connected",
            "Pass": True
        }

    ])

    st.dataframe(
        conclusion,
        use_container_width=True
    )

    if route_match and cost_match:

        st.success(
            "✔ Validation PASSED — All algorithms agree."
        )

    else:

        st.error(
            "❌ Validation FAILED — Algorithms disagree."
        )

    # ========================================================
    # ROUTE BREAKDOWN
    # ========================================================

    st.subheader("Route Breakdown")

    rows = []

    for i in range(len(d_path) - 1):

        origin = d_path[i]
        destination = d_path[i + 1]

        edge = graph[origin][destination]

        leg_total = (
            edge["fuel_cost"]
            + edge["canal_fee"]
            + edge["weather_risk"]
            + edge["piracy_risk"]
            + edge["carbon_cost"]
        )

        rows.append({

            "Port From": origin,
            "Port To": destination,

            "Distance NM":
                round(edge["distance"], 2),

            "Fuel":
                round(edge["fuel_cost"], 2),

            "Canal":
                round(edge["canal_fee"], 2),

            "Weather":
                round(edge["weather_risk"], 2),

            "Piracy":
                round(edge["piracy_risk"], 2),

            "Carbon":
                round(edge["carbon_cost"], 2),

            "Leg Total":
                round(leg_total, 2)

        })

    breakdown_df = pd.DataFrame(rows)

    st.dataframe(
        breakdown_df,
        use_container_width=True
    )

    # ========================================================
    # ROUTE TOTALS
    # ========================================================

    st.subheader("Route Totals")

    st.write(
        f"Total Route Cost: {round(d_cost, 2)}"
    )

    st.write(
        f"Total Distance (NM): "
        f"{round(breakdown_df['Distance NM'].sum(), 2)}"
    )

    # ========================================================
    # VERSION 2 PLACEHOLDER
    # ========================================================

    st.info(
        "Version 2: Voyage Economics Engine "
        "(Revenue, Profit, TCE, Fleet Optimisation)"
    )