# tests/test_random_routes.py

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

import random
import pandas as pd

from optimizer.dijkstra import build_graph, shortest_path
from optimizer.astar import astar_path
from optimizer.brute_force import brute_force_shortest_path


# ============================================================
# SETTINGS
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"

NUM_RANDOM_TESTS = 25          # Faster for large graphs

RANDOM_SEED = 42

MAX_BRUTEFORCE_PORTS = 12      # Brute force only on small subsets


# ============================================================
# LOAD DATA
# ============================================================

routes = pd.read_csv(ROUTES_FILE)

graph = build_graph(routes)

ports = sorted(
    set(routes["origin_port"]).union(
        set(routes["destination_port"])
    )
)

random.seed(RANDOM_SEED)


# ============================================================
# RESULTS STORAGE
# ============================================================

results = []

passes = 0
failures = 0
no_path = 0
bruteforce_skipped = 0


# ============================================================
# TEST LOOP
# ============================================================

print("\n============================================================")
print("SHIPPING ROUTE OPTIMIZER — RANDOM VALIDATION TESTS")
print("============================================================\n")

for i in range(NUM_RANDOM_TESTS):

    start, end = random.sample(ports, 2)

    print(f"Running test {i+1}/{NUM_RANDOM_TESTS}: {start} -> {end}")

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
        # BRUTE FORCE (ONLY SMALLER SUBSETS)
        # ====================================================

        # Create reduced local subset for brute force speed
        local_ports = set(d_path)

        if len(local_ports) <= MAX_BRUTEFORCE_PORTS:

            local_routes = routes[
                routes["origin_port"].isin(local_ports)
                & routes["destination_port"].isin(local_ports)
            ]

            b_path, b_cost = brute_force_shortest_path(
                local_routes,
                start,
                end
            )

            brute_used = True

        else:
            b_path, b_cost = "SKIPPED", "SKIPPED"
            brute_used = False
            bruteforce_skipped += 1

        # ====================================================
        # AGREEMENT CHECKS
        # ====================================================

        route_match = (d_path == a_path)

        cost_match = (
            abs(d_cost - a_cost) < 0.01
        )

        brute_match = True

        if brute_used:
            brute_match = (
                abs(d_cost - b_cost) < 0.01
            )

        overall_pass = (
            route_match
            and cost_match
            and brute_match
        )

        if overall_pass:
            passes += 1
        else:
            failures += 1

        results.append({
            "Test #": i + 1,
            "Start": start,
            "End": end,
            "Dijkstra Route": " → ".join(d_path),
            "Dijkstra Cost": round(d_cost, 2),
            "A* Route": " → ".join(a_path),
            "A* Cost": round(a_cost, 2),
            "Brute Route": (
                " → ".join(b_path)
                if isinstance(b_path, list)
                else b_path
            ),
            "Brute Cost": b_cost,
            "Dijkstra=A* Route": route_match,
            "Dijkstra=A* Cost": cost_match,
            "Brute Match": brute_match,
            "PASS": overall_pass,
        })

    except Exception as err:

        no_path += 1

        results.append({
            "Test #": i + 1,
            "Start": start,
            "End": end,
            "Dijkstra Route": "N/A",
            "Dijkstra Cost": "N/A",
            "A* Route": "N/A",
            "A* Cost": "N/A",
            "Brute Route": "N/A",
            "Brute Cost": "N/A",
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

print(f"Total tests run: {NUM_RANDOM_TESTS}")
print(f"Passes: {passes}")
print(f"Failures: {failures}")
print(f"No path / exceptions: {no_path}")
print(f"Brute force skipped: {bruteforce_skipped}")

if NUM_RANDOM_TESTS > 0:
    print(
        f"Pass rate: {round((passes / NUM_RANDOM_TESTS) * 100, 2)}%"
    )

print("============================================================\n")

print(results_df.head(25))

# ============================================================
# SAVE REPORT
# ============================================================

output_file = "tests/random_route_test_results.csv"

results_df.to_csv(
    output_file,
    index=False
)

print(f"\nDetailed results saved to:\n{output_file}")