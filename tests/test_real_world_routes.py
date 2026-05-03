# tests/test_real_world_routes.py

import sys
import os

# ============================================================
# FORCE PROJECT ROOT INTO PYTHON PATH
# ============================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

import pandas as pd

from optimizer.dijkstra import build_graph, shortest_path
from optimizer.astar import astar_path
from optimizer.brute_force import brute_force_shortest_path


# ============================================================
# SETTINGS
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"


# ============================================================
# REAL-WORLD TEST CASES
# ============================================================

REAL_WORLD_TESTS = [

    # Australia / Oceania
    ("SYD", "AKL"),
    ("SYD", "SIN"),
    ("MEL", "DXB"),
    ("BNE", "RTM"),

    # North America / Europe
    ("NYC", "RTM"),
    ("LAX", "TOK"),
    ("SEA", "SHA"),

    # Africa / Middle East
    ("CPT", "DXB"),
    ("DAR", "RTM"),

    # Global long-haul
    ("SYD", "NYC"),
    ("AKL", "LAX"),
    ("DXB", "LAX"),
    ("RTM", "SIN"),
]


# ============================================================
# LOAD DATA
# ============================================================

routes = pd.read_csv(ROUTES_FILE)

graph = build_graph(routes)


# ============================================================
# RESULTS STORAGE
# ============================================================

results = []

passes = 0
failures = 0


# ============================================================
# TEST LOOP
# ============================================================

print("\n============================================================")
print("SHIPPING ROUTE OPTIMIZER — REAL WORLD ROUTE VALIDATION")
print("============================================================\n")

for i, (start, end) in enumerate(REAL_WORLD_TESTS, start=1):

    print(f"Running test {i}/{len(REAL_WORLD_TESTS)}: {start} -> {end}")

    try:

        # ====================================================
        # DIJKSTRA
        # ====================================================

        d_path, d_cost = shortest_path(
            graph,
            start,
            end,
            weight="total_cost"
        )

        # ====================================================
        # A*
        # ====================================================

        a_path, a_cost = astar_path(
            graph,
            start,
            end,
            weight="total_cost"
        )

        # ====================================================
        # BRUTE FORCE
        # ====================================================

        local_ports = set(d_path)

        local_routes = routes[
            routes["origin_port"].isin(local_ports)
            & routes["destination_port"].isin(local_ports)
        ]

        b_path, b_cost = brute_force_shortest_path(
            local_routes,
            start,
            end
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        route_match = (
            d_path == a_path == b_path
        )

        cost_match = (
            abs(d_cost - a_cost) < 0.01
            and abs(d_cost - b_cost) < 0.01
        )

        overall_pass = route_match and cost_match

        if overall_pass:
            passes += 1
        else:
            failures += 1

        results.append({
            "Test #": i,
            "Start": start,
            "End": end,
            "Dijkstra Route": " → ".join(d_path),
            "Dijkstra Cost": round(d_cost, 2),
            "A* Route": " → ".join(a_path),
            "A* Cost": round(a_cost, 2),
            "Brute Route": " → ".join(b_path),
            "Brute Cost": round(b_cost, 2),
            "Route Match": route_match,
            "Cost Match": cost_match,
            "PASS": overall_pass,
        })

    except Exception as err:

        failures += 1

        results.append({
            "Test #": i,
            "Start": start,
            "End": end,
            "Dijkstra Route": "N/A",
            "Dijkstra Cost": "N/A",
            "A* Route": "N/A",
            "A* Cost": "N/A",
            "Brute Route": "N/A",
            "Brute Cost": "N/A",
            "Route Match": False,
            "Cost Match": False,
            "PASS": False,
            "Error": str(err),
        })


# ============================================================
# RESULTS OUTPUT
# ============================================================

results_df = pd.DataFrame(results)

print("\n============================================================")
print("FINAL RESULTS")
print("============================================================")

print(f"Total tests run: {len(REAL_WORLD_TESTS)}")
print(f"Passes: {passes}")
print(f"Failures: {failures}")

if len(REAL_WORLD_TESTS) > 0:
    print(
        f"Pass rate: {round((passes / len(REAL_WORLD_TESTS)) * 100, 2)}%"
    )

print("============================================================\n")

print(results_df)

# ============================================================
# SAVE RESULTS
# ============================================================

output_file = "tests/real_world_route_test_results.csv"

results_df.to_csv(
    output_file,
    index=False
)

print(f"\nDetailed results saved to:\n{output_file}")