# pages/14_chartering_desk.py

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
from economics.vessel_profiles import load_vessels
from economics.voyage_economics import calculate_voyage_economics


st.set_page_config(
    page_title="Chartering Desk",
    layout="wide"
)

st.title("Chartering Desk")

# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"
VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"
CARGOES_FILE = "data/cargoes.csv"
CONGESTION_FILE = "data/port_congestion.csv"

routes = pd.read_csv(ROUTES_FILE)
vessels = load_vessels(VESSELS_FILE)
positions = pd.read_csv(POSITIONS_FILE)
cargoes = pd.read_csv(CARGOES_FILE)
congestion = pd.read_csv(CONGESTION_FILE)

graph = build_graph(routes)

fleet = vessels.merge(
    positions,
    on="vessel_name",
    how="left"
)


# ============================================================
# CLEAN DATA
# ============================================================

for col in [
    "cargo_capacity_tonnes",
    "speed_knots",
    "fuel_burn_tpd",
    "available_days",
    "daily_hire_cost"
]:
    fleet[col] = pd.to_numeric(
        fleet[col],
        errors="coerce"
    )

for col in [
    "cargo_tonnes",
    "freight_rate"
]:
    cargoes[col] = pd.to_numeric(
        cargoes[col],
        errors="coerce"
    )

congestion["delay_days"] = pd.to_numeric(
    congestion["delay_days"],
    errors="coerce"
)

fleet = fleet.dropna(
    subset=[
        "vessel_name",
        "vessel_type",
        "cargo_capacity_tonnes",
        "speed_knots",
        "fuel_burn_tpd",
        "current_port",
        "available_days",
        "daily_hire_cost"
    ]
)

cargoes = cargoes.dropna(
    subset=[
        "cargo_id",
        "cargo_name",
        "cargo_type",
        "load_port",
        "discharge_port",
        "cargo_tonnes",
        "freight_rate"
    ]
)


# ============================================================
# INPUTS
# ============================================================

st.subheader("Cargo Opportunity")

cargoes["cargo_display"] = (
    cargoes["cargo_name"]
    + " | "
    + cargoes["cargo_tonnes"].astype(int).astype(str)
    + " t | "
    + cargoes["load_port"]
    + " → "
    + cargoes["discharge_port"]
)

selected_cargo_display = st.selectbox(
    "Select Cargo",
    cargoes["cargo_display"].tolist()
)

cargo = cargoes[
    cargoes["cargo_display"] == selected_cargo_display
].iloc[0]


st.subheader("Commercial Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    fuel_price = st.number_input(
        "Fuel Price ($/tonne)",
        min_value=100.0,
        max_value=3000.0,
        value=600.0,
        step=10.0
    )

with col2:
    load_port_cost = st.number_input(
        "Load Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

with col3:
    discharge_port_cost = st.number_input(
        "Discharge Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

col1, col2, col3 = st.columns(3)

with col1:
    transit_fee_per_port = st.number_input(
        "Transit Fee Per Intermediate Port ($)",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

with col2:
    freight_premium_percent = st.number_input(
        "Freight Premium (%)",
        min_value=0.0,
        max_value=300.0,
        value=0.0,
        step=1.0
    )

with col3:
    route_cost_multiplier = st.number_input(
        "Route Cost Multiplier",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )


# ============================================================
# RUN
# ============================================================

if st.button("Run Chartering Desk Analysis"):

    load_port = cargo["load_port"]
    discharge_port = cargo["discharge_port"]

    capable_fleet = fleet[
        fleet["cargo_capacity_tonnes"] >= cargo["cargo_tonnes"]
    ].copy()

    if capable_fleet.empty:
        st.error("No capable vessels available.")
        st.stop()

    load_delay = congestion[
        congestion["port"] == load_port
    ]

    discharge_delay = congestion[
        congestion["port"] == discharge_port
    ]

    congestion_days = (
        (
            float(load_delay.iloc[0]["delay_days"])
            if not load_delay.empty
            else 0.0
        )
        +
        (
            float(discharge_delay.iloc[0]["delay_days"])
            if not discharge_delay.empty
            else 0.0
        )
    )

    results = []

    for _, vessel in capable_fleet.iterrows():

        try:
            positioning_path, positioning_route_cost = shortest_path(
                graph,
                vessel["current_port"],
                load_port
            )

            voyage_path, voyage_route_cost = shortest_path(
                graph,
                load_port,
                discharge_port
            )

        except Exception:
            continue

        positioning_distance = 0.0

        for i in range(len(positioning_path) - 1):
            edge = graph[positioning_path[i]][positioning_path[i + 1]]
            positioning_distance += float(edge["distance"])

        voyage_distance = 0.0

        for i in range(len(voyage_path) - 1):
            edge = graph[voyage_path[i]][voyage_path[i + 1]]
            voyage_distance += float(edge["distance"])

        positioning_days = (
            positioning_distance
            /
            vessel["speed_knots"]
            /
            24
        )

        earliest_ready_days = (
            vessel["available_days"]
            +
            positioning_days
        )

        positioning_hire_cost = (
            earliest_ready_days
            *
            vessel["daily_hire_cost"]
        )

        transit_port_count = max(0, len(voyage_path) - 2)

        economics = calculate_voyage_economics(
            distance_nm=voyage_distance,
            route_cost=voyage_route_cost,
            cargo_tonnes=cargo["cargo_tonnes"],
            freight_rate=cargo["freight_rate"],
            vessel_speed_knots=vessel["speed_knots"],
            fuel_burn_tonnes_per_day=vessel["fuel_burn_tpd"],
            fuel_price=fuel_price,
            load_port_cost=load_port_cost,
            discharge_port_cost=discharge_port_cost,
            freight_premium_percent=freight_premium_percent,
            ballast_days=earliest_ready_days,
            waiting_days=congestion_days,
            port_days=0,
            transit_port_count=transit_port_count,
            transit_fee_per_port=transit_fee_per_port,
            route_cost_multiplier=route_cost_multiplier
        )

        net_profit = (
            economics["voyage_profit"]
            -
            positioning_hire_cost
        )

        total_days = (
            economics["total_voyage_days"]
            if economics["total_voyage_days"] > 0
            else 1
        )

        net_tce = net_profit / total_days

        utilization = (
            cargo["cargo_tonnes"]
            /
            vessel["cargo_capacity_tonnes"]
            *
            100
        )

        results.append({
            "Vessel": vessel["vessel_name"],
            "Type": vessel["vessel_type"],
            "Current Port": vessel["current_port"],
            "Cargo": cargo["cargo_name"],
            "Cargo Tonnes": cargo["cargo_tonnes"],
            "Utilization %": round(utilization, 2),
            "Positioning Route": " → ".join(positioning_path),
            "Voyage Route": " → ".join(voyage_path),
            "Earliest Ready Days": round(earliest_ready_days, 2),
            "Congestion Days": round(congestion_days, 2),
            "Voyage Revenue": economics["voyage_revenue"],
            "Voyage Cost": economics["voyage_cost"],
            "Positioning Hire Cost": round(positioning_hire_cost, 2),
            "Net Profit": round(net_profit, 2),
            "Net TCE": round(net_tce, 2),
            "Speed": vessel["speed_knots"],
            "Fuel Burn": vessel["fuel_burn_tpd"]
        })

    results_df = pd.DataFrame(results)

    if results_df.empty:
        st.error("No commercially usable vessels found.")
        st.stop()

    results_df = results_df.sort_values(
        by=[
            "Net Profit",
            "Net TCE",
            "Earliest Ready Days"
        ],
        ascending=[
            False,
            False,
            True
        ]
    )

    st.subheader("Chartering Ranking")

    st.dataframe(
        results_df,
        use_container_width=True
    )

    best = results_df.iloc[0]

    st.subheader("Recommended Fixture")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(
            f"Best Vessel: {best['Vessel']}"
        )

    with col2:
        st.info(
            f"Net Profit: ${best['Net Profit']:,.0f}"
        )

    with col3:
        st.info(
            f"Net TCE: ${best['Net TCE']:,.0f}/day"
        )

    st.subheader("Commercial Decision")

    if best["Net Profit"] > 0 and best["Net TCE"] > 10000:
        st.success("Recommendation: FIX / ACCEPT CARGO")

    elif best["Net Profit"] > 0:
        st.warning("Recommendation: MARGINAL — Review assumptions")

    else:
        st.error("Recommendation: DO NOT FIX")

st.caption(
    "Future enhancement: market freight premium engine, laycan windows, true fleet assignment, "
    "weather risk, cargo compatibility and stowage feasibility."
)