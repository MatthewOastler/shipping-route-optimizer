



# pages/18_model_validation.py

import sys
import os
import math

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
from economics.voyage_economics import (
    calculate_voyage_economics,
    calculate_revenue,
    calculate_sea_days,
    calculate_total_voyage_days,
    calculate_fuel_consumed,
    calculate_fuel_cost,
    calculate_port_costs,
    calculate_transit_costs,
    calculate_adjusted_route_cost,
    calculate_voyage_cost,
    calculate_voyage_profit,
    calculate_tce,
)
from economics.speed_fuel_model import estimate_fuel_burn_at_speed
from economics.vessel_profiles import load_vessels, calculate_capacity_utilization


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Model Validation",
    layout="wide"
)

st.title("Model Validation & Data Provenance")
st.caption("Accurate results without lying to ourselves")


# ============================================================
# FILES
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"
VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"
CARGOES_FILE = "data/cargoes.csv"
CONGESTION_FILE = "data/port_congestion.csv"
STOWAGE_FILE = "data/cargo_stowage_factors.csv"
OPERATING_COSTS_FILE = "data/vessel_operating_costs.csv"
DATA_SOURCES_FILE = "data/data_sources.csv"


# ============================================================
# HELPERS
# ============================================================

def add_result(results, category, check, status, expected="", actual="", difference="", notes=""):
    results.append({
        "Category": category,
        "Check": check,
        "Status": status,
        "Expected": expected,
        "Actual": actual,
        "Difference": difference,
        "Notes": notes,
    })


def close_enough(a, b, tolerance=0.01):
    return abs(float(a) - float(b)) <= float(tolerance)


def safe_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def file_status(path):
    return os.path.exists(path)


def route_cost_from_graph(graph, path):
    total = 0.0
    for i in range(len(path) - 1):
        total += float(graph[path[i]][path[i + 1]]["total_cost"])
    return total


def route_distance_from_graph(graph, path):
    total = 0.0
    for i in range(len(path) - 1):
        total += float(graph[path[i]][path[i + 1]]["distance"])
    return total


def display_status_summary(results_df):
    passed = int((results_df["Status"] == "PASS").sum())
    failed = int((results_df["Status"] == "FAIL").sum())
    warnings = int((results_df["Status"] == "WARNING").sum())
    skipped = int((results_df["Status"] == "SKIPPED").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PASS", passed)
    c2.metric("FAIL", failed)
    c3.metric("WARNING", warnings)
    c4.metric("SKIPPED", skipped)


# ============================================================
# LOAD DATA WITH CONTROLLED ERRORS
# ============================================================

load_errors = []

def load_csv(path, name):
    try:
        return pd.read_csv(path)
    except Exception as err:
        load_errors.append(f"{name}: {err}")
        return pd.DataFrame()


routes = load_csv(ROUTES_FILE, "generated_routes.csv")
vessels = load_vessels(VESSELS_FILE) if file_status(VESSELS_FILE) else pd.DataFrame()
positions = load_csv(POSITIONS_FILE, "vessel_positions.csv")
cargoes = load_csv(CARGOES_FILE, "cargoes.csv")
congestion = load_csv(CONGESTION_FILE, "port_congestion.csv")
stowage = load_csv(STOWAGE_FILE, "cargo_stowage_factors.csv")
opex = load_csv(OPERATING_COSTS_FILE, "vessel_operating_costs.csv")
sources = load_csv(DATA_SOURCES_FILE, "data_sources.csv")

if load_errors:
    st.error("One or more project datasets failed to load.")
    for err in load_errors:
        st.write(err)


# ============================================================
# DATASET PROVENANCE
# ============================================================

st.subheader("Data Provenance Register")

if sources.empty:
    st.warning(
        "data/data_sources.csv is missing or empty. "
        "The model can still run, but provenance cannot be audited."
    )
else:
    st.dataframe(
        sources,
        use_container_width=True
    )

    status_counts = (
        sources["validation_status"]
        .fillna("UNKNOWN")
        .value_counts()
        .rename_axis("Validation Status")
        .reset_index(name="Count")
    )

    st.dataframe(
        status_counts,
        use_container_width=True
    )


# ============================================================
# VALIDATION SETTINGS
# ============================================================

st.sidebar.header("Validation Settings")

route_tests = st.sidebar.slider(
    "Route Pair Tests",
    min_value=3,
    max_value=50,
    value=10
)

numeric_tolerance = st.sidebar.number_input(
    "Numeric Tolerance",
    min_value=0.0001,
    max_value=10.0,
    value=0.01,
    step=0.01,
    format="%.4f"
)

run_brute_force = st.sidebar.checkbox(
    "Run Brute Force Where Practical",
    value=True
)

max_bruteforce_path_nodes = st.sidebar.slider(
    "Max Path Nodes for Brute Force",
    min_value=3,
    max_value=15,
    value=10
)


# ============================================================
# RUN VALIDATION
# ============================================================

if st.button("Run Full Model Validation"):

    results = []

    # ========================================================
    # 1. FILE / SCHEMA VALIDATION
    # ========================================================

    required_files = {
        "generated_routes.csv": ROUTES_FILE,
        "vessels.csv": VESSELS_FILE,
        "vessel_positions.csv": POSITIONS_FILE,
        "cargoes.csv": CARGOES_FILE,
        "port_congestion.csv": CONGESTION_FILE,
        "cargo_stowage_factors.csv": STOWAGE_FILE,
        "vessel_operating_costs.csv": OPERATING_COSTS_FILE,
        "data_sources.csv": DATA_SOURCES_FILE,
    }

    for name, path in required_files.items():
        exists = file_status(path)
        add_result(
            results,
            "Data Files",
            f"{name} exists",
            "PASS" if exists else "FAIL",
            expected="File exists",
            actual="Exists" if exists else "Missing",
            notes=path
        )

    route_required = [
        "origin_port",
        "destination_port",
        "distance_nm",
        "fuel_cost_estimate",
        "canal_fee",
        "weather_risk",
        "piracy_risk",
        "carbon_cost",
    ]

    for col in route_required:
        add_result(
            results,
            "Route Schema",
            f"Route column: {col}",
            "PASS" if col in routes.columns else "FAIL",
            expected="Present",
            actual="Present" if col in routes.columns else "Missing"
        )

    vessel_required = [
        "vessel_name",
        "vessel_type",
        "dwt",
        "speed_knots",
        "fuel_burn_tpd",
        "cargo_capacity_tonnes",
    ]

    for col in vessel_required:
        add_result(
            results,
            "Vessel Schema",
            f"Vessel column: {col}",
            "PASS" if col in vessels.columns else "FAIL",
            expected="Present",
            actual="Present" if col in vessels.columns else "Missing"
        )

    position_required = [
        "vessel_name",
        "current_port",
        "available_days",
        "market_hire_rate_per_day",
    ]

    for col in position_required:
        status = "PASS" if col in positions.columns else "FAIL"
        note = ""
        if col == "market_hire_rate_per_day" and "daily_hire_cost" in positions.columns:
            status = "WARNING"
            note = "Old column daily_hire_cost still exists; rename it."
        add_result(
            results,
            "Vessel Position Schema",
            f"Position column: {col}",
            status,
            expected="Present",
            actual="Present" if col in positions.columns else "Missing",
            notes=note
        )

    # ========================================================
    # 2. ROUTE DATA QUALITY
    # ========================================================

    if not routes.empty and all(c in routes.columns for c in route_required):
        routes_test = routes.copy()
        routes_test = safe_numeric(
            routes_test,
            [
                "distance_nm",
                "fuel_cost_estimate",
                "canal_fee",
                "weather_risk",
                "piracy_risk",
                "carbon_cost",
            ]
        )

        invalid_distances = int((routes_test["distance_nm"] <= 0).sum())
        add_result(
            results,
            "Route Data",
            "All route distances > 0",
            "PASS" if invalid_distances == 0 else "FAIL",
            expected=0,
            actual=invalid_distances,
            difference=invalid_distances
        )

        negative_cost_rows = int(
            (
                (routes_test["fuel_cost_estimate"] < 0)
                | (routes_test["canal_fee"] < 0)
                | (routes_test["weather_risk"] < 0)
                | (routes_test["piracy_risk"] < 0)
                | (routes_test["carbon_cost"] < 0)
            ).sum()
        )

        add_result(
            results,
            "Route Data",
            "No negative route cost components",
            "PASS" if negative_cost_rows == 0 else "FAIL",
            expected=0,
            actual=negative_cost_rows,
            difference=negative_cost_rows
        )

        self_loops = int(
            (
                routes_test["origin_port"].astype(str).str.strip()
                ==
                routes_test["destination_port"].astype(str).str.strip()
            ).sum()
        )

        add_result(
            results,
            "Route Data",
            "No self-loop routes",
            "PASS" if self_loops == 0 else "WARNING",
            expected=0,
            actual=self_loops,
            difference=self_loops,
            notes="build_graph skips self-loops, but source data should ideally contain none."
        )

    # ========================================================
    # 3. ROUTING ENGINE VALIDATION
    # ========================================================

    if not routes.empty:
        try:
            graph = build_graph(routes)
            ports = sorted(graph.nodes())

            add_result(
                results,
                "Routing",
                "Graph contains nodes",
                "PASS" if graph.number_of_nodes() > 0 else "FAIL",
                expected="> 0",
                actual=graph.number_of_nodes()
            )

            add_result(
                results,
                "Routing",
                "Graph contains edges",
                "PASS" if graph.number_of_edges() > 0 else "FAIL",
                expected="> 0",
                actual=graph.number_of_edges()
            )

            tested = 0

            for start in ports:
                if tested >= route_tests:
                    break

                for end in reversed(ports):
                    if tested >= route_tests:
                        break

                    if start == end:
                        continue

                    try:
                        d_path, d_cost = shortest_path(graph, start, end)
                    except Exception:
                        continue

                    tested += 1

                    # Dijkstra cost equals explicit path sum
                    explicit_cost = route_cost_from_graph(graph, d_path)

                    add_result(
                        results,
                        "Routing",
                        f"Dijkstra path cost reconciliation: {start} → {end}",
                        "PASS" if close_enough(d_cost, explicit_cost, numeric_tolerance) else "FAIL",
                        expected=round(explicit_cost, 4),
                        actual=round(d_cost, 4),
                        difference=round(d_cost - explicit_cost, 6)
                    )

                    # A*
                    try:
                        a_path, a_cost = astar_path(graph, start, end)

                        add_result(
                            results,
                            "Routing",
                            f"Dijkstra = A* cost: {start} → {end}",
                            "PASS" if close_enough(d_cost, a_cost, numeric_tolerance) else "FAIL",
                            expected=round(d_cost, 4),
                            actual=round(a_cost, 4),
                            difference=round(a_cost - d_cost, 6),
                            notes="A* currently uses zero heuristic, so cost should agree with Dijkstra."
                        )

                    except Exception as err:
                        add_result(
                            results,
                            "Routing",
                            f"Dijkstra = A* cost: {start} → {end}",
                            "FAIL",
                            expected="Successful A* result",
                            actual=str(err)
                        )

                    # Brute force only on small local path
                    if run_brute_force and len(set(d_path)) <= max_bruteforce_path_nodes:
                        try:
                            local_ports = set(d_path)

                            local_routes = routes[
                                routes["origin_port"].astype(str).str.strip().isin(local_ports)
                                &
                                routes["destination_port"].astype(str).str.strip().isin(local_ports)
                            ]

                            b_path, b_cost = brute_force_shortest_path(
                                local_routes,
                                start,
                                end
                            )

                            add_result(
                                results,
                                "Routing",
                                f"Dijkstra = Brute Force cost: {start} → {end}",
                                "PASS" if close_enough(d_cost, b_cost, numeric_tolerance) else "FAIL",
                                expected=round(d_cost, 4),
                                actual=round(b_cost, 4),
                                difference=round(b_cost - d_cost, 6)
                            )

                        except Exception as err:
                            add_result(
                                results,
                                "Routing",
                                f"Dijkstra = Brute Force cost: {start} → {end}",
                                "FAIL",
                                expected="Successful brute-force result",
                                actual=str(err)
                            )
                    else:
                        add_result(
                            results,
                            "Routing",
                            f"Brute Force test: {start} → {end}",
                            "SKIPPED",
                            notes="Skipped due to path size or user setting."
                        )

        except Exception as err:
            add_result(
                results,
                "Routing",
                "Build routing graph",
                "FAIL",
                actual=str(err)
            )

    # ========================================================
    # 4. ECONOMICS UNIT TESTS
    # ========================================================

    try:
        revenue = calculate_revenue(
            cargo_tonnes=50000,
            freight_rate=25,
            freight_premium_percent=10
        )
        expected_revenue = 50000 * 25 * 1.10

        add_result(
            results,
            "Economics",
            "Revenue formula",
            "PASS" if close_enough(revenue, expected_revenue, numeric_tolerance) else "FAIL",
            expected=expected_revenue,
            actual=revenue,
            difference=revenue - expected_revenue
        )

        sea_days = calculate_sea_days(5000, 13)
        expected_sea_days = 5000 / 13 / 24

        add_result(
            results,
            "Economics",
            "Sea days formula",
            "PASS" if close_enough(sea_days, expected_sea_days, numeric_tolerance) else "FAIL",
            expected=expected_sea_days,
            actual=sea_days,
            difference=sea_days - expected_sea_days
        )

        total_days = calculate_total_voyage_days(
            sea_days=sea_days,
            ballast_days=2,
            waiting_days=1,
            port_days=3
        )
        expected_total_days = sea_days + 2 + 1 + 3

        add_result(
            results,
            "Economics",
            "Total voyage days formula",
            "PASS" if close_enough(total_days, expected_total_days, numeric_tolerance) else "FAIL",
            expected=expected_total_days,
            actual=total_days,
            difference=total_days - expected_total_days
        )

        fuel_consumed = calculate_fuel_consumed(
            sea_days=sea_days,
            fuel_burn_tonnes_per_day=30
        )
        expected_fuel = sea_days * 30

        add_result(
            results,
            "Economics",
            "Fuel consumption formula",
            "PASS" if close_enough(fuel_consumed, expected_fuel, numeric_tolerance) else "FAIL",
            expected=expected_fuel,
            actual=fuel_consumed,
            difference=fuel_consumed - expected_fuel
        )

        fuel_cost = calculate_fuel_cost(fuel_consumed, 600)
        expected_fuel_cost = fuel_consumed * 600

        add_result(
            results,
            "Economics",
            "Fuel cost formula",
            "PASS" if close_enough(fuel_cost, expected_fuel_cost, numeric_tolerance) else "FAIL",
            expected=expected_fuel_cost,
            actual=fuel_cost,
            difference=fuel_cost - expected_fuel_cost
        )

        port_costs = calculate_port_costs(25000, 25000)

        add_result(
            results,
            "Economics",
            "Port cost formula",
            "PASS" if close_enough(port_costs, 50000, numeric_tolerance) else "FAIL",
            expected=50000,
            actual=port_costs,
            difference=port_costs - 50000
        )

        transit_costs = calculate_transit_costs(2, 15000)

        add_result(
            results,
            "Economics",
            "Transit cost formula",
            "PASS" if close_enough(transit_costs, 30000, numeric_tolerance) else "FAIL",
            expected=30000,
            actual=transit_costs,
            difference=transit_costs - 30000
        )

        adjusted_route_cost = calculate_adjusted_route_cost(100000, 1.25)

        add_result(
            results,
            "Economics",
            "Route cost multiplier",
            "PASS" if close_enough(adjusted_route_cost, 125000, numeric_tolerance) else "FAIL",
            expected=125000,
            actual=adjusted_route_cost,
            difference=adjusted_route_cost - 125000
        )

        voyage_cost = calculate_voyage_cost(
            fuel_cost=100000,
            port_costs=50000,
            transit_costs=30000,
            adjusted_route_cost=125000
        )

        add_result(
            results,
            "Economics",
            "Voyage cost formula",
            "PASS" if close_enough(voyage_cost, 305000, numeric_tolerance) else "FAIL",
            expected=305000,
            actual=voyage_cost,
            difference=voyage_cost - 305000
        )

        voyage_profit = calculate_voyage_profit(500000, 305000)

        add_result(
            results,
            "Economics",
            "Voyage profit formula",
            "PASS" if close_enough(voyage_profit, 195000, numeric_tolerance) else "FAIL",
            expected=195000,
            actual=voyage_profit,
            difference=voyage_profit - 195000
        )

        tce = calculate_tce(195000, 15)

        add_result(
            results,
            "Economics",
            "TCE formula",
            "PASS" if close_enough(tce, 13000, numeric_tolerance) else "FAIL",
            expected=13000,
            actual=tce,
            difference=tce - 13000
        )

        master = calculate_voyage_economics(
            distance_nm=5000,
            route_cost=100000,
            cargo_tonnes=50000,
            freight_rate=25,
            vessel_speed_knots=13,
            fuel_burn_tonnes_per_day=30,
            fuel_price=600,
            load_port_cost=25000,
            discharge_port_cost=25000,
            freight_premium_percent=10,
            ballast_days=2,
            waiting_days=1,
            port_days=3,
            transit_port_count=2,
            transit_fee_per_port=15000,
            route_cost_multiplier=1.0
        )

        master_recon = (
            master["fuel_cost"]
            + master["port_costs"]
            + master["transit_costs"]
            + master["adjusted_route_cost"]
        )

        add_result(
            results,
            "Economics",
            "Master voyage cost reconciliation",
            "PASS" if close_enough(master["voyage_cost"], master_recon, numeric_tolerance) else "FAIL",
            expected=master_recon,
            actual=master["voyage_cost"],
            difference=master["voyage_cost"] - master_recon
        )

    except Exception as err:
        add_result(
            results,
            "Economics",
            "Economics unit test suite",
            "FAIL",
            actual=str(err)
        )

    # ========================================================
    # 5. SPEED / FUEL VALIDATION
    # ========================================================

    try:
        base_burn = 30.0

        burn_at_base = estimate_fuel_burn_at_speed(
            speed_knots=13,
            base_speed_knots=13,
            base_fuel_burn_tpd=base_burn,
            exponent=3.0
        )

        add_result(
            results,
            "Speed/Fuel",
            "Fuel burn at reference speed equals reference burn",
            "PASS" if close_enough(burn_at_base, base_burn, numeric_tolerance) else "FAIL",
            expected=base_burn,
            actual=burn_at_base,
            difference=burn_at_base - base_burn
        )

        slow_burn = estimate_fuel_burn_at_speed(
            speed_knots=10,
            base_speed_knots=13,
            base_fuel_burn_tpd=30,
            exponent=3.0
        )

        fast_burn = estimate_fuel_burn_at_speed(
            speed_knots=16,
            base_speed_knots=13,
            base_fuel_burn_tpd=30,
            exponent=3.0
        )

        add_result(
            results,
            "Speed/Fuel",
            "Higher speed increases daily fuel burn",
            "PASS" if fast_burn > slow_burn else "FAIL",
            expected="16 kn burn > 10 kn burn",
            actual=f"{fast_burn:.2f} > {slow_burn:.2f}"
        )

    except Exception as err:
        add_result(
            results,
            "Speed/Fuel",
            "Speed/fuel tests",
            "FAIL",
            actual=str(err)
        )

    # ========================================================
    # 6. VESSEL / CAPACITY VALIDATION
    # ========================================================

    if not vessels.empty:
        vessels_test = vessels.copy()
        vessels_test = safe_numeric(
            vessels_test,
            [
                "dwt",
                "speed_knots",
                "fuel_burn_tpd",
                "cargo_capacity_tonnes"
            ]
        )

        invalid_capacity = int(
            (
                (vessels_test["cargo_capacity_tonnes"] <= 0)
                | (vessels_test["dwt"] <= 0)
                | (vessels_test["speed_knots"] <= 0)
                | (vessels_test["fuel_burn_tpd"] < 0)
            ).sum()
        )

        add_result(
            results,
            "Vessels",
            "Positive vessel characteristics",
            "PASS" if invalid_capacity == 0 else "FAIL",
            expected=0,
            actual=invalid_capacity
        )

        over_dwt = int(
            (
                vessels_test["cargo_capacity_tonnes"]
                >
                vessels_test["dwt"]
            ).sum()
        )

        add_result(
            results,
            "Vessels",
            "Cargo capacity does not exceed DWT",
            "PASS" if over_dwt == 0 else "WARNING",
            expected=0,
            actual=over_dwt,
            notes="Cargo capacity > DWT should be investigated."
        )

        sample = vessels_test.iloc[0]
        util = calculate_capacity_utilization(
            sample["cargo_capacity_tonnes"] * 0.8,
            sample["cargo_capacity_tonnes"]
        )

        add_result(
            results,
            "Vessels",
            "Capacity utilization formula",
            "PASS" if close_enough(util, 80.0, numeric_tolerance) else "FAIL",
            expected=80.0,
            actual=util,
            difference=util - 80.0
        )

    # ========================================================
    # 7. OPEX VALIDATION
    # ========================================================

    if not opex.empty:
        opex_test = opex.copy()

        opex_components = [
            "crew_cost_per_day",
            "insurance_cost_per_day",
            "maintenance_cost_per_day",
            "technical_management_cost_per_day",
            "stores_cost_per_day",
            "admin_overhead_cost_per_day",
        ]

        opex_test = safe_numeric(
            opex_test,
            opex_components + ["total_opex_per_day"]
        )

        if all(col in opex_test.columns for col in opex_components + ["total_opex_per_day"]):

            opex_test["calculated_total"] = opex_test[opex_components].sum(axis=1)
            opex_test["difference"] = (
                opex_test["total_opex_per_day"]
                -
                opex_test["calculated_total"]
            )

            bad_opex = int(
                (
                    opex_test["difference"].abs()
                    >
                    numeric_tolerance
                ).sum()
            )

            add_result(
                results,
                "OPEX",
                "OPEX components sum to total OPEX/day",
                "PASS" if bad_opex == 0 else "FAIL",
                expected=0,
                actual=bad_opex,
                difference=bad_opex,
                notes="Each row should reconcile exactly within tolerance."
            )

        else:
            add_result(
                results,
                "OPEX",
                "Required OPEX columns present",
                "FAIL",
                expected="All OPEX component columns",
                actual="Missing one or more columns"
            )

    # ========================================================
    # 8. CARGO / STOWAGE VALIDATION
    # ========================================================

    if not cargoes.empty and not stowage.empty:

        missing_stowage = sorted(
            set(cargoes["cargo_name"].dropna().astype(str))
            -
            set(stowage["cargo_name"].dropna().astype(str))
        )

        add_result(
            results,
            "Stowage",
            "Every cargo has a stowage factor",
            "PASS" if len(missing_stowage) == 0 else "FAIL",
            expected="No missing cargoes",
            actual=", ".join(missing_stowage) if missing_stowage else "None",
            notes="Missing factors cause the dashboard to fall back or stop depending on page."
        )

        stowage_test = stowage.copy()
        stowage_test = safe_numeric(
            stowage_test,
            ["stowage_factor_m3_per_tonne"]
        )

        invalid_stowage = int(
            (
                stowage_test["stowage_factor_m3_per_tonne"] <= 0
            ).sum()
        )

        add_result(
            results,
            "Stowage",
            "All stowage factors > 0",
            "PASS" if invalid_stowage == 0 else "FAIL",
            expected=0,
            actual=invalid_stowage
        )

    # ========================================================
    # 9. CONGESTION VALIDATION
    # ========================================================

    if not congestion.empty:
        congestion_test = congestion.copy()
        congestion_test = safe_numeric(
            congestion_test,
            [
                "delay_days",
                "berth_utilization_pct",
                "waiting_risk_score"
            ]
        )

        negative_delay = int((congestion_test["delay_days"] < 0).sum())
        bad_berth = int(
            (
                (congestion_test["berth_utilization_pct"] < 0)
                |
                (congestion_test["berth_utilization_pct"] > 100)
            ).sum()
        )

        add_result(
            results,
            "Congestion",
            "No negative congestion delays",
            "PASS" if negative_delay == 0 else "FAIL",
            expected=0,
            actual=negative_delay
        )

        add_result(
            results,
            "Congestion",
            "Berth utilization between 0% and 100%",
            "PASS" if bad_berth == 0 else "FAIL",
            expected=0,
            actual=bad_berth
        )

    # ========================================================
    # 10. MARKET HIRE VS OPEX SEPARATION
    # ========================================================

    if not positions.empty:
        has_market_hire = "market_hire_rate_per_day" in positions.columns
        has_old_hire = "daily_hire_cost" in positions.columns

        if has_market_hire and not has_old_hire:
            status = "PASS"
            actual = "market_hire_rate_per_day"
            note = "Hire rate is clearly separated from vessel OPEX."
        elif has_market_hire and has_old_hire:
            status = "WARNING"
            actual = "Both columns exist"
            note = "Remove or migrate daily_hire_cost to avoid ambiguity."
        elif has_old_hire:
            status = "WARNING"
            actual = "daily_hire_cost"
            note = "Rename to market_hire_rate_per_day."
        else:
            status = "FAIL"
            actual = "No hire-rate column"
            note = "Required for chartered-in vessel economics."

        add_result(
            results,
            "Commercial Model",
            "Market hire rate separated from OPEX",
            status,
            expected="market_hire_rate_per_day",
            actual=actual,
            notes=note
        )

    # ========================================================
    # 11. PROVENANCE QUALITY
    # ========================================================

    if not sources.empty:
                
        required_source_cols = [
            "data_item",
            "file_or_module",
            "field_or_metric",
            "source_type",
            "source_name",
            "source_url",
            "source_data_date",
            "last_reviewed",
            "validation_status",
            "confidence",
            "notes",
        ]
        
        

        missing_source_cols = [
            c for c in required_source_cols
            if c not in sources.columns
        ]

        add_result(
            results,
            "Provenance",
            "Provenance registry schema complete",
            "PASS" if not missing_source_cols else "FAIL",
            expected="All required provenance columns",
            actual="Complete" if not missing_source_cols else ", ".join(missing_source_cols)
        )

        if "source_type" in sources.columns:
            synthetic_count = int(
                sources["source_type"]
                .astype(str)
                .str.upper()
                .isin(["SYNTHETIC", "MODELLED", "DEMO"])
                .sum()
            )

            add_result(
                results,
                "Provenance",
                "Synthetic/modelled inputs explicitly identified",
                "PASS",
                expected="Clearly labelled",
                actual=f"{synthetic_count} row(s) labelled synthetic/modelled/demo",
                notes="This is not a failure; it is a transparency check."
            )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    results_df = pd.DataFrame(results)

    st.subheader("Validation Summary")

    display_status_summary(results_df)

    st.dataframe(
        results_df,
        use_container_width=True
    )

    failures = results_df[
        results_df["Status"] == "FAIL"
    ]

    warnings = results_df[
        results_df["Status"] == "WARNING"
    ]

    st.subheader("Final Verdict")

    if len(failures) == 0 and len(warnings) == 0:
        st.success(
            "VALIDATION PASSED — no failures or warnings detected in the checks run."
        )

    elif len(failures) == 0:
        st.warning(
            f"VALIDATION PASSED WITH {len(warnings)} WARNING(S). "
            "Review warnings before treating the model as production-ready."
        )

    else:
        st.error(
            f"VALIDATION FAILED — {len(failures)} failure(s) detected. "
            "Do not treat the affected model components as validated until resolved."
        )

    if not failures.empty:
        st.subheader("Failures Requiring Attention")
        st.dataframe(
            failures,
            use_container_width=True
        )

    if not warnings.empty:
        st.subheader("Warnings Requiring Review")
        st.dataframe(
            warnings,
            use_container_width=True
        )

    # ========================================================
    # IMPORTANT INTERPRETATION
    # ========================================================

    st.markdown("---")

    st.info(
        """
        Passing these checks proves internal consistency, not real-world accuracy.

        Internal validation can show that:
        - formulas reconcile,
        - routing algorithms agree,
        - datasets are structurally valid,
        - OPEX totals reconcile,
        - vessel/cargo constraints are applied consistently.

        It does NOT prove that synthetic route costs, congestion assumptions,
        vessel fuel curves, freight rates, port charges or risk penalties match
        the real market.

        The next validation layer should compare model outputs against completed
        historical voyages and independently sourced real-world data.
        """
    )