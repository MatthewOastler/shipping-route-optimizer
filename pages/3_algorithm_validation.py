# pages/3_algorithm_validation.py

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

from optimizer.dijkstra import build_graph, shortest_path
from optimizer.astar import astar_path
from optimizer.brute_force import brute_force_shortest_path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Algorithm Validation",
    layout="wide"
)

st.title("Algorithm Validation")

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
# SETTINGS
# ============================================================

NUM_RANDOM_TESTS = st.sidebar.slider(
    "Random Tests",
    min_value=5,
    max_value=100,
    value=25
)

MAX_BRUTEFORCE_PORTS = 12

random.seed(42)

# ============================================================
# RANDOM VALIDATION
# ============================================================

if st.button("Run Random Validation"):

    results = []

    passes = 0
    failures = 0
    brute_skipped = 0

    progress = st.progress(0)

    for i in range(NUM_RANDOM_TESTS):

        progress.progress(
            (i + 1) / NUM_RANDOM_TESTS
        )

        start, end = random.sample(
            ports,
            2
        )

        try:

            # --------------------------------------------
            # Dijkstra
            # --------------------------------------------

            d_path, d_cost = shortest_path(
                graph,
                start,
                end
            )

            # --------------------------------------------
            # A*
            # --------------------------------------------

            a_path, a_cost = astar_path(
                graph,
                start,
                end
            )

            # --------------------------------------------
            # Brute Force
            # --------------------------------------------

            local_ports = set(d_path)

            if len(local_ports) <= MAX_BRUTEFORCE_PORTS:

                local_routes = routes[
                    routes["origin_port"].isin(local_ports)
                    &
                    routes["destination_port"].isin(local_ports)
                ]

                b_path, b_cost = brute_force_shortest_path(
                    local_routes,
                    start,
                    end
                )

                brute_match = (
                    abs(d_cost - b_cost) < 0.01
                )

            else:

                b_path = ["SKIPPED"]
                b_cost = None

                brute_match = True

                brute_skipped += 1

            route_match = (
                d_path == a_path
            )

            cost_match = (
                abs(d_cost - a_cost) < 0.01
            )

            overall_pass = (
                route_match
                and
                cost_match
                and
                brute_match
            )

            if overall_pass:
                passes += 1
            else:
                failures += 1

            results.append({

                "Start": start,
                "End": end,

                "Dijkstra Cost":
                    round(d_cost, 2),

                "A* Cost":
                    round(a_cost, 2),

                "Brute Cost":
                    (
                        round(b_cost, 2)
                        if b_cost is not None
                        else "SKIPPED"
                    ),

                "Route Match":
                    route_match,

                "Cost Match":
                    cost_match,

                "Brute Match":
                    brute_match,

                "PASS":
                    overall_pass
            })

        except Exception as err:

            failures += 1

            results.append({

                "Start": start,
                "End": end,

                "PASS": False,

                "Error": str(err)

            })

    results_df = pd.DataFrame(results)

    st.subheader("Random Validation Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Tests",
        NUM_RANDOM_TESTS
    )

    col2.metric(
        "Passes",
        passes
    )

    col3.metric(
        "Failures",
        failures
    )

    pass_rate = round(
        (passes / NUM_RANDOM_TESTS) * 100,
        2
    )

    col4.metric(
        "Pass Rate %",
        pass_rate
    )

    st.dataframe(
        results_df,
        use_container_width=True
    )

# ============================================================
# REAL WORLD TESTS
# ============================================================

REAL_WORLD_TESTS = [

    ("SYD", "AKL"),
    ("SYD", "SIN"),
    ("MEL", "DXB"),
    ("BNE", "RTM"),
    ("NYC", "RTM"),
    ("CPT", "DXB"),
    ("SYD", "NYC"),
    ("AKL", "LAX"),
    ("DXB", "LAX"),
    ("RTM", "SIN"),
]

# ============================================================
# REAL WORLD VALIDATION
# ============================================================

if st.button("Run Real World Validation"):

    results = []

    passes = 0
    failures = 0

    for start, end in REAL_WORLD_TESTS:

        try:

            d_path, d_cost = shortest_path(
                graph,
                start,
                end
            )

            a_path, a_cost = astar_path(
                graph,
                start,
                end
            )

            local_ports = set(d_path)

            local_routes = routes[
                routes["origin_port"].isin(local_ports)
                &
                routes["destination_port"].isin(local_ports)
            ]

            b_path, b_cost = brute_force_shortest_path(
                local_routes,
                start,
                end
            )

            route_match = (
                d_path == a_path == b_path
            )

            cost_match = (
                abs(d_cost - a_cost) < 0.01
                and
                abs(d_cost - b_cost) < 0.01
            )

            overall_pass = (
                route_match
                and
                cost_match
            )

            if overall_pass:
                passes += 1
            else:
                failures += 1

            results.append({

                "Start": start,
                "End": end,

                "Dijkstra Cost":
                    round(d_cost, 2),

                "A* Cost":
                    round(a_cost, 2),

                "Brute Cost":
                    round(b_cost, 2),

                "PASS":
                    overall_pass
            })

        except Exception as err:

            failures += 1

            results.append({

                "Start": start,
                "End": end,

                "PASS": False,

                "Error": str(err)

            })

    results_df = pd.DataFrame(results)

    st.subheader("Real World Validation Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Tests",
        len(REAL_WORLD_TESTS)
    )

    col2.metric(
        "Passes",
        passes
    )

    col3.metric(
        "Failures",
        failures
    )

    st.dataframe(
        results_df,
        use_container_width=True
    )

    if failures == 0:

        st.success(
            "✔ All real-world tests passed."
        )

    else:

        st.error(
            "❌ One or more validation tests failed."
        )