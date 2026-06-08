# pages/6_speed_optimizer.py

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

from economics.voyage_economics import (
    calculate_voyage_economics
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Speed Optimizer",
    layout="wide"
)

st.title("Speed Optimizer")

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
# ROUTE
# ============================================================

st.subheader("Route")

col1, col2 = st.columns(2)

with col1:

    start_port = st.selectbox(
        "Load Port",
        ports
    )

with col2:

    end_port = st.selectbox(
        "Discharge Port",
        ports
    )

# ============================================================
# COMMERCIAL INPUTS
# ============================================================

st.subheader("Commercial Inputs")

col1, col2, col3 = st.columns(3)

with col1:

    cargo_tonnes = st.number_input(
        "Cargo Tonnes",
        min_value=1000,
        max_value=500000,
        value=50000,
        step=1000
    )

with col2:

    freight_rate = st.number_input(
        "Freight Rate ($/tonne)",
        min_value=1.0,
        max_value=500.0,
        value=25.0,
        step=1.0
    )

with col3:

    freight_premium_percent = st.number_input(
        "Freight Premium (%)",
        min_value=0.0,
        max_value=300.0,
        value=0.0,
        step=1.0
    )

# ============================================================
# FUEL
# ============================================================

st.subheader("Fuel Assumptions")

col1, col2 = st.columns(2)

with col1:

    fuel_burn = st.number_input(
        "Fuel Consumption (tonnes/day)",
        min_value=1.0,
        max_value=200.0,
        value=30.0,
        step=1.0
    )

with col2:

    fuel_price = st.number_input(
        "Fuel Price ($/tonne)",
        min_value=100.0,
        max_value=3000.0,
        value=600.0,
        step=10.0
    )

# ============================================================
# PORT COSTS
# ============================================================

st.subheader("Port Costs")

col1, col2 = st.columns(2)

with col1:

    load_port_cost = st.number_input(
        "Load Port Cost ($)",
        value=25000.0
    )

with col2:

    discharge_port_cost = st.number_input(
        "Discharge Port Cost ($)",
        value=25000.0
    )

# ============================================================
# DELAYS
# ============================================================

st.subheader("Voyage Delays")

col1, col2, col3 = st.columns(3)

with col1:

    ballast_days = st.number_input(
        "Ballast Days",
        value=0.0
    )

with col2:

    waiting_days = st.number_input(
        "Waiting Days",
        value=0.0
    )

with col3:

    port_days = st.number_input(
        "Port Days",
        value=0.0
    )

# ============================================================
# OTHER
# ============================================================

st.subheader("Other Assumptions")

col1, col2 = st.columns(2)

with col1:

    transit_fee_per_port = st.number_input(
        "Transit Fee Per Port ($)",
        value=0.0
    )

with col2:

    route_cost_multiplier = st.number_input(
        "Route Cost Multiplier",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )

# ============================================================
# SPEED RANGE
# ============================================================

st.subheader("Speed Range")

col1, col2 = st.columns(2)

with col1:

    min_speed = st.number_input(
        "Minimum Speed (knots)",
        min_value=5,
        max_value=30,
        value=10
    )

with col2:

    max_speed = st.number_input(
        "Maximum Speed (knots)",
        min_value=5,
        max_value=30,
        value=16
    )

# ============================================================
# RUN
# ============================================================

if st.button("Run Speed Optimization"):

    try:

        path, base_route_cost = shortest_path(
            graph,
            start_port,
            end_port
        )

    except Exception as err:

        st.error(
            f"Route calculation failed: {err}"
        )

        st.stop()

    total_distance = 0

    for i in range(len(path) - 1):

        edge = graph[
            path[i]
        ][
            path[i + 1]
        ]

        total_distance += edge["distance"]

    transit_port_count = max(
        0,
        len(path) - 2
    )

    results = []

    for speed in range(
        int(min_speed),
        int(max_speed) + 1
    ):

        result = calculate_voyage_economics(

            distance_nm=total_distance,

            route_cost=base_route_cost,

            cargo_tonnes=cargo_tonnes,

            freight_rate=freight_rate,

            vessel_speed_knots=speed,

            fuel_burn_tonnes_per_day=fuel_burn,

            fuel_price=fuel_price,

            load_port_cost=load_port_cost,

            discharge_port_cost=discharge_port_cost,

            freight_premium_percent=freight_premium_percent,

            ballast_days=ballast_days,

            waiting_days=waiting_days,

            port_days=port_days,

            transit_port_count=transit_port_count,

            transit_fee_per_port=transit_fee_per_port,

            route_cost_multiplier=route_cost_multiplier
        )

        results.append({

            "Speed (knots)":
                speed,

            "Sea Days":
                result["sea_days"],

            "Total Voyage Days":
                result["total_voyage_days"],

            "Fuel Consumed":
                result["fuel_consumed"],

            "Fuel Cost":
                result["fuel_cost"],

            "Voyage Revenue":
                result["voyage_revenue"],

            "Voyage Cost":
                result["voyage_cost"],

            "Voyage Profit":
                result["voyage_profit"],

            "TCE":
                result["tce"]

        })

    results_df = pd.DataFrame(
        results
    )

    st.subheader(
        "Speed Comparison"
    )

    st.dataframe(
        results_df,
        use_container_width=True
    )

    # ========================================================
    # BEST RESULTS
    # ========================================================

    best_tce = results_df.loc[
        results_df["TCE"].idxmax()
    ]

    best_profit = results_df.loc[
        results_df["Voyage Profit"].idxmax()
    ]

    cheapest_fuel = results_df.loc[
        results_df["Fuel Cost"].idxmin()
    ]

    fastest = results_df.loc[
        results_df["Sea Days"].idxmin()
    ]

    st.subheader(
        "Optimization Results"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.success(

            f"Best TCE Speed: "
            f"{best_tce['Speed (knots)']} knots "
            f"(TCE ${best_tce['TCE']:,.0f}/day)"

        )

        st.success(

            f"Best Profit Speed: "
            f"{best_profit['Speed (knots)']} knots "
            f"(Profit ${best_profit['Voyage Profit']:,.0f})"

        )

    with col2:

        st.info(

            f"Lowest Fuel Cost Speed: "
            f"{cheapest_fuel['Speed (knots)']} knots"

        )

        st.info(

            f"Fastest Arrival Speed: "
            f"{fastest['Speed (knots)']} knots"

        )

    st.subheader(
        "Selected Route"
    )

    st.write(
        " → ".join(path)
    )

    st.write(
        f"Distance: {round(total_distance, 2):,} NM"
    )

    st.caption(
        "Future enhancement: dynamic fuel burn curves. "
        "Currently fuel consumption per day is fixed. "
        "Real ships burn significantly more fuel at higher speeds."
    )