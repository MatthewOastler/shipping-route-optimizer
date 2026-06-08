# pages/5_conclusion_matrix.py

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

import random
import pandas as pd
import streamlit as st

from optimizer.dijkstra import (
    build_graph,
    shortest_path
)

from optimizer.astar import (
    astar_path
)

from optimizer.brute_force import (
    brute_force_shortest_path
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Conclusion Matrix",
    layout="wide"
)

st.title(
    "Conclusion Matrix"
)

st.caption(
    "Accurate results without lying to ourselves"
)

# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"

routes = pd.read_csv(
    ROUTES_FILE
)

graph = build_graph(
    routes
)

ports = sorted(
    set(routes["origin_port"]).union(
        set(routes["destination_port"])
    )
)

# ============================================================
# SETTINGS
# ============================================================

st.sidebar.header(
    "Validation Settings"
)

num_tests = st.sidebar.slider(
    "Random Validation Tests",
    min_value=5,
    max_value=100,
    value=25
)

random.seed(42)

# ============================================================
# RUN MATRIX
# ============================================================

if st.button(
    "Run Conclusion Matrix"
):

    total_tests = 0

    dijkstra_astar_passes = 0

    dijkstra_bruteforce_passes = 0

    route_cost_passes = 0

    graph_connectivity_passes = 0

    failures = []

    progress = st.progress(0)

    for i in range(num_tests):

        progress.progress(
            (i + 1) / num_tests
        )

        try:

            start_port, end_port = random.sample(
                ports,
                2
            )

            total_tests += 1

            # ====================================================
            # DIJKSTRA
            # ====================================================

            d_path, d_cost = shortest_path(
                graph,
                start_port,
                end_port
            )

            # ====================================================
            # A*
            # ====================================================

            a_path, a_cost = astar_path(
                graph,
                start_port,
                end_port
            )

            # ====================================================
            # CHECK 1
            # ====================================================

            if abs(d_cost - a_cost) < 0.01:

                dijkstra_astar_passes += 1

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

            # ====================================================
            # CHECK 2
            # ====================================================

            if abs(d_cost - b_cost) < 0.01:

                dijkstra_bruteforce_passes += 1

            # ====================================================
            # CHECK 3
            # ====================================================

            calculated_cost = 0

            for j in range(len(d_path) - 1):

                edge = graph[
                    d_path[j]
                ][
                    d_path[j + 1]
                ]

                calculated_cost += edge["total_cost"]

            if abs(calculated_cost - d_cost) < 0.01:

                route_cost_passes += 1

            # ====================================================
            # CHECK 4
            # ====================================================

            graph_connectivity_passes += 1

        except Exception as err:

            failures.append({

                "Error":
                    str(err)

            })

    # ========================================================
    # METRICS
    # ========================================================

    st.subheader(
        "Validation Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Tests",
        total_tests
    )

    col2.metric(
        "Dijkstra=A*",
        f"{dijkstra_astar_passes}/{total_tests}"
    )

    col3.metric(
        "Dijkstra=Brute",
        f"{dijkstra_bruteforce_passes}/{total_tests}"
    )

    col4.metric(
        "Cost Verified",
        f"{route_cost_passes}/{total_tests}"
    )

    # ========================================================
    # MATRIX
    # ========================================================

    st.subheader(
        "Conclusion Matrix"
    )

    matrix = pd.DataFrame([

        {
            "Check":
                "Dijkstra equals A*",

            "Passes":
                dijkstra_astar_passes,

            "Tests":
                total_tests,

            "Pass %":
                round(
                    (
                        dijkstra_astar_passes
                        /
                        total_tests
                    ) * 100,
                    2
                )
        },

        {
            "Check":
                "Dijkstra equals Brute Force",

            "Passes":
                dijkstra_bruteforce_passes,

            "Tests":
                total_tests,

            "Pass %":
                round(
                    (
                        dijkstra_bruteforce_passes
                        /
                        total_tests
                    ) * 100,
                    2
                )
        },

        {
            "Check":
                "Route Cost Verified",

            "Passes":
                route_cost_passes,

            "Tests":
                total_tests,

            "Pass %":
                round(
                    (
                        route_cost_passes
                        /
                        total_tests
                    ) * 100,
                    2
                )
        },

        {
            "Check":
                "Graph Connectivity",

            "Passes":
                graph_connectivity_passes,

            "Tests":
                total_tests,

            "Pass %":
                round(
                    (
                        graph_connectivity_passes
                        /
                        total_tests
                    ) * 100,
                    2
                )
        }

    ])

    st.dataframe(
        matrix,
        use_container_width=True
    )

    # ========================================================
    # FINAL VERDICT
    # ========================================================

    overall_pass = (

        dijkstra_astar_passes
        ==
        total_tests

        and

        dijkstra_bruteforce_passes
        ==
        total_tests

        and

        route_cost_passes
        ==
        total_tests
    )

    st.subheader(
        "Final Verdict"
    )

    if overall_pass:

        st.success(
            """
            VALIDATED

            All routing engines agree.

            Route costs verified.

            No inconsistencies detected.
            """
        )

    else:

        st.error(
            """
            WARNING

            One or more validation checks failed.

            Debugging required.
            """
        )

    # ========================================================
    # FAILURE DETAILS
    # ========================================================

    if failures:

        st.subheader(
            "Failure Details"
        )

        st.dataframe(
            pd.DataFrame(failures),
            use_container_width=True
        )

    else:

        st.success(
            "No failures detected."
        )

# ============================================================
# PROJECT PHILOSOPHY
# ============================================================

st.markdown("---")

st.info(
    """
    This page exists to challenge the optimizer.

    The objective is not to prove the system is correct.

    The objective is to actively look for evidence that it is wrong.

    If we cannot find evidence that it is wrong,
    confidence increases.

    Accurate results without lying to ourselves.
    """
)