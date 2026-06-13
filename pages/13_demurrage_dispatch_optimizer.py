# pages/13_demurrage_dispatch_optimizer.py

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
from economics.voyage_economics import calculate_voyage_economics
from economics.vessel_profiles import load_vessels


st.set_page_config(
    page_title="Demurrage / Dispatch Optimizer",
    layout="wide"
)

st.title("Demurrage / Dispatch Optimizer")

# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"
CARGOES_FILE = "data/cargoes.csv"
VESSELS_FILE = "data/vessels.csv"
CONGESTION_FILE = "data/port_congestion.csv"

routes = pd.read_csv(ROUTES_FILE)
cargoes = pd.read_csv(CARGOES_FILE)
vessels = load_vessels(VESSELS_FILE)
congestion = pd.read_csv(CONGESTION_FILE)

graph = build_graph(routes)


# ============================================================
# CLEAN DATA
# ============================================================

cargoes["cargo_tonnes"] = pd.to_numeric(
    cargoes["cargo_tonnes"],
    errors="coerce"
)

cargoes["freight_rate"] = pd.to_numeric(
    cargoes["freight_rate"],
    errors="coerce"
)

vessels["speed_knots"] = pd.to_numeric(
    vessels["speed_knots"],
    errors="coerce"
)

vessels["fuel_burn_tpd"] = pd.to_numeric(
    vessels["fuel_burn_tpd"],
    errors="coerce"
)

vessels["cargo_capacity_tonnes"] = pd.to_numeric(
    vessels["cargo_capacity_tonnes"],
    errors="coerce"
)

congestion["delay_days"] = pd.to_numeric(
    congestion["delay_days"],
    errors="coerce"
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

vessels = vessels.dropna(
    subset=[
        "vessel_name",
        "vessel_type",
        "speed_knots",
        "fuel_burn_tpd",
        "cargo_capacity_tonnes"
    ]
)


# ============================================================
# SELECT CARGO / VESSEL
# ============================================================

st.subheader("Cargo and Vessel")

cargoes["cargo_display"] = (
    cargoes["cargo_name"]
    + " | "
    + cargoes["cargo_tonnes"].astype(int).astype(str)
    + " t | "
    + cargoes["load_port"]
    + " → "
    + cargoes["discharge_port"]
)

col1, col2 = st.columns(2)

with col1:
    selected_cargo_display = st.selectbox(
        "Select Cargo",
        cargoes["cargo_display"].tolist()
    )

cargo = cargoes[
    cargoes["cargo_display"] == selected_cargo_display
].iloc[0]

capable_vessels = vessels[
    vessels["cargo_capacity_tonnes"] >= cargo["cargo_tonnes"]
].copy()

if capable_vessels.empty:
    st.error("No vessel can carry this cargo.")
    st.stop()

with col2:
    selected_vessel = st.selectbox(
        "Select Vessel",
        capable_vessels["vessel_name"].tolist()
    )

vessel = capable_vessels[
    capable_vessels["vessel_name"] == selected_vessel
].iloc[0]


# ============================================================
# COMMERCIAL INPUTS
# ============================================================

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
# LAYTIME INPUTS
# ============================================================

st.subheader("Laytime Inputs")

col1, col2 = st.columns(2)

with col1:
    allowed_load_laytime = st.number_input(
        "Allowed Load Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

with col2:
    actual_load_laytime = st.number_input(
        "Actual Load Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

col1, col2 = st.columns(2)

with col1:
    allowed_discharge_laytime = st.number_input(
        "Allowed Discharge Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

with col2:
    actual_discharge_laytime = st.number_input(
        "Actual Discharge Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

col1, col2 = st.columns(2)

with col1:
    demurrage_rate = st.number_input(
        "Demurrage Rate ($/day)",
        min_value=0.0,
        value=15000.0,
        step=1000.0
    )

with col2:
    dispatch_rate = st.number_input(
        "Dispatch Rate ($/day)",
        min_value=0.0,
        value=7500.0,
        step=500.0
    )


# ============================================================
# CALCULATE
# ============================================================

if st.button("Calculate Demurrage / Dispatch Impact"):

    load_port = cargo["load_port"]
    discharge_port = cargo["discharge_port"]

    try:
        path, base_route_cost = shortest_path(
            graph,
            load_port,
            discharge_port
        )

    except Exception as err:
        st.error(f"Route failed: {err}")
        st.stop()

    total_distance = 0.0

    for i in range(len(path) - 1):
        edge = graph[path[i]][path[i + 1]]
        total_distance += float(edge["distance"])

    transit_port_count = max(0, len(path) - 2)

    load_congestion = congestion[
        congestion["port"] == load_port
    ]

    discharge_congestion = congestion[
        congestion["port"] == discharge_port
    ]

    load_congestion_days = (
        float(load_congestion.iloc[0]["delay_days"])
        if not load_congestion.empty
        else 0.0
    )

    discharge_congestion_days = (
        float(discharge_congestion.iloc[0]["delay_days"])
        if not discharge_congestion.empty
        else 0.0
    )

    congestion_days = (
        load_congestion_days
        +
        discharge_congestion_days
    )

    result = calculate_voyage_economics(
        distance_nm=total_distance,
        route_cost=base_route_cost,
        cargo_tonnes=cargo["cargo_tonnes"],
        freight_rate=cargo["freight_rate"],
        vessel_speed_knots=vessel["speed_knots"],
        fuel_burn_tonnes_per_day=vessel["fuel_burn_tpd"],
        fuel_price=fuel_price,
        load_port_cost=load_port_cost,
        discharge_port_cost=discharge_port_cost,
        freight_premium_percent=freight_premium_percent,
        ballast_days=0,
        waiting_days=congestion_days,
        port_days=allowed_load_laytime + allowed_discharge_laytime,
        transit_port_count=transit_port_count,
        transit_fee_per_port=transit_fee_per_port,
        route_cost_multiplier=route_cost_multiplier
    )

    load_diff = actual_load_laytime - allowed_load_laytime
    discharge_diff = actual_discharge_laytime - allowed_discharge_laytime

    total_laytime_diff = load_diff + discharge_diff

    demurrage_cost = 0.0
    dispatch_credit = 0.0

    if total_laytime_diff > 0:
        demurrage_cost = total_laytime_diff * demurrage_rate

    elif total_laytime_diff < 0:
        dispatch_credit = abs(total_laytime_diff) * dispatch_rate

    adjusted_profit = (
        result["voyage_profit"]
        -
        demurrage_cost
        +
        dispatch_credit
    )

    adjusted_tce = (
        adjusted_profit
        /
        result["total_voyage_days"]
        if result["total_voyage_days"] > 0
        else 0
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    st.subheader("Voyage and Laytime Summary")

    summary = pd.DataFrame([{
        "Cargo": cargo["cargo_name"],
        "Cargo Type": cargo["cargo_type"],
        "Vessel": vessel["vessel_name"],
        "Route": " → ".join(path),
        "Distance NM": result["distance_nm"],
        "Sea Days": result["sea_days"],
        "Congestion Days": round(congestion_days, 2),
        "Base Voyage Profit ($)": result["voyage_profit"],
        "Base TCE ($/day)": result["tce"],
        "Laytime Difference Days": round(total_laytime_diff, 2),
        "Demurrage Cost ($)": round(demurrage_cost, 2),
        "Dispatch Credit ($)": round(dispatch_credit, 2),
        "Adjusted Profit ($)": round(adjusted_profit, 2),
        "Adjusted TCE ($/day)": round(adjusted_tce, 2)
    }])

    st.dataframe(
        summary,
        use_container_width=True
    )

    st.subheader("Commercial Interpretation")

    if demurrage_cost > 0:
        st.error(
            f"Demurrage applies: ${demurrage_cost:,.0f}"
        )

    elif dispatch_credit > 0:
        st.success(
            f"Dispatch credit applies: ${dispatch_credit:,.0f}"
        )

    else:
        st.info("No demurrage or dispatch applies.")

    if adjusted_profit > 0:
        st.success(
            f"Adjusted voyage remains profitable: ${adjusted_profit:,.0f}"
        )
    else:
        st.error(
            f"Adjusted voyage is unprofitable: ${adjusted_profit:,.0f}"
        )

    st.info(
        f"Adjusted TCE: ${adjusted_tce:,.0f}/day"
    )

st.caption(
    "Future enhancement: weather working days, reversible laytime, notice of readiness, "
    "once on demurrage always on demurrage and charter-party specific rules."
)