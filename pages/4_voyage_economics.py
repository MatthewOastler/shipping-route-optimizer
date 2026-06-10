


# pages/4_voyage_economics.py

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

from economics.vessel_profiles import (
    load_vessels,
    get_vessel_profile
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Voyage Economics",
    layout="wide"
)

st.title("Voyage Economics")

st.caption("Accurate results without lying to ourselves")


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
# ROUTE SELECTION
# ============================================================

st.subheader("Voyage Route")

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
# VESSEL ASSUMPTIONS
# ============================================================

st.subheader("Vessel Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    vessel_speed = st.number_input(
        "Vessel Speed (knots)",
        min_value=5.0,
        max_value=30.0,
        value=13.0,
        step=0.5
    )

with col2:
    fuel_burn = st.number_input(
        "Fuel Consumption (tonnes/day)",
        min_value=1.0,
        max_value=200.0,
        value=30.0,
        step=1.0
    )

with col3:
    fuel_price = st.number_input(
        "Fuel Price ($/tonne)",
        min_value=100.0,
        max_value=3000.0,
        value=600.0,
        step=10.0
    )


# ============================================================
# CARGO / FREIGHT ASSUMPTIONS
# ============================================================

st.subheader("Cargo and Freight Assumptions")

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
# PORT COSTS
# ============================================================

st.subheader("Port Costs")

col1, col2, col3 = st.columns(3)

with col1:
    load_port_cost = st.number_input(
        "Load Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

with col2:
    discharge_port_cost = st.number_input(
        "Discharge Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

with col3:
    transit_fee_per_port = st.number_input(
        "Transit Fee Per Intermediate Port ($)",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )


# ============================================================
# VOYAGE TIME ADJUSTMENTS
# ============================================================

st.subheader("Voyage Time Adjustments")

col1, col2, col3 = st.columns(3)

with col1:
    ballast_days = st.number_input(
        "Ballast Days",
        min_value=0.0,
        max_value=365.0,
        value=0.0,
        step=0.5
    )

with col2:
    waiting_days = st.number_input(
        "Waiting Days",
        min_value=0.0,
        max_value=365.0,
        value=0.0,
        step=0.5
    )

with col3:
    port_days = st.number_input(
        "Port Days",
        min_value=0.0,
        max_value=365.0,
        value=0.0,
        step=0.5
    )


# ============================================================
# ROUTE COST ADJUSTMENT
# ============================================================

st.subheader("Route Cost Adjustment")

route_cost_multiplier = st.number_input(
    "Route Cost Multiplier",
    min_value=0.1,
    max_value=10.0,
    value=1.0,
    step=0.1
)

st.caption(
    "Route cost multiplier adjusts the route engine cost without changing the route dataset."
)


# ============================================================
# CALCULATE
# ============================================================

if st.button("Calculate Voyage Economics"):

    if start_port == end_port:
        st.warning("Load Port and Discharge Port must be different.")
        st.stop()

    try:
        path, base_route_cost = shortest_path(
            graph,
            start_port,
            end_port
        )

    except Exception as err:
        st.error(f"Unable to calculate route: {err}")
        st.stop()

    # ========================================================
    # ROUTE DISTANCE AND LEG DETAILS
    # ========================================================

    total_distance = 0.0
    route_rows = []

    for i in range(len(path) - 1):

        origin = path[i]
        destination = path[i + 1]

        edge = graph[origin][destination]

        leg_distance = float(edge["distance"])
        total_distance += leg_distance

        leg_total = (
            float(edge.get("fuel_cost", 0))
            + float(edge.get("canal_fee", 0))
            + float(edge.get("weather_risk", 0))
            + float(edge.get("piracy_risk", 0))
            + float(edge.get("carbon_cost", 0))
        )

        route_rows.append({
            "From": origin,
            "To": destination,
            "Distance NM": round(leg_distance, 2),
            "Fuel Cost": round(float(edge.get("fuel_cost", 0)), 2),
            "Canal Fee": round(float(edge.get("canal_fee", 0)), 2),
            "Weather Risk": round(float(edge.get("weather_risk", 0)), 2),
            "Piracy Risk": round(float(edge.get("piracy_risk", 0)), 2),
            "Carbon Cost": round(float(edge.get("carbon_cost", 0)), 2),
            "Leg Total": round(leg_total, 2)
        })

    # ========================================================
    # AUTO TRANSIT PORT DETECTION
    # ========================================================

    if len(path) > 2:
        transit_ports = path[1:-1]
    else:
        transit_ports = []

    transit_port_count = len(transit_ports)

    # ========================================================
    # VOYAGE ECONOMICS ENGINE
    # ========================================================

    result = calculate_voyage_economics(
        distance_nm=total_distance,
        route_cost=base_route_cost,
        cargo_tonnes=cargo_tonnes,
        freight_rate=freight_rate,
        vessel_speed_knots=vessel_speed,
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

    # ========================================================
    # SELECTED ROUTE
    # ========================================================

    st.subheader("Selected Route")

    st.write(" → ".join(path))

    if transit_ports:
        st.write(
            "Intermediate Transit Ports: "
            + ", ".join(transit_ports)
        )
    else:
        st.write("Intermediate Transit Ports: None")

    # ========================================================
    # VOYAGE SUMMARY
    # ========================================================

    st.subheader("Voyage Summary")

    summary = pd.DataFrame([{
        "Distance NM": result["distance_nm"],
        "Sea Days": result["sea_days"],
        "Ballast Days": result["ballast_days"],
        "Waiting Days": result["waiting_days"],
        "Port Days": result["port_days"],
        "Total Voyage Days": result["total_voyage_days"],
        "Fuel Consumed (t)": result["fuel_consumed"],
        "Fuel Cost ($)": result["fuel_cost"],
        "Load Port Cost ($)": result["load_port_cost"],
        "Discharge Port Cost ($)": result["discharge_port_cost"],
        "Port Costs ($)": result["port_costs"],
        "Transit Port Count": result["transit_port_count"],
        "Transit Fee Per Port ($)": result["transit_fee_per_port"],
        "Transit Costs ($)": result["transit_costs"],
        "Base Route Cost ($)": result["base_route_cost"],
        "Route Cost Multiplier": result["route_cost_multiplier"],
        "Adjusted Route Cost ($)": result["adjusted_route_cost"],
        "Voyage Revenue ($)": result["voyage_revenue"],
        "Voyage Cost ($)": result["voyage_cost"],
        "Voyage Profit ($)": result["voyage_profit"],
        "TCE ($/day)": result["tce"]
    }])

    st.dataframe(
        summary,
        use_container_width=True
    )

    # ========================================================
    # ROUTE LEG BREAKDOWN
    # ========================================================

    st.subheader("Route Leg Breakdown")

    st.dataframe(
        pd.DataFrame(route_rows),
        use_container_width=True
    )

    # ========================================================
    # COST EXPLANATION
    # ========================================================

    st.subheader("Cost Explanation")

    explanation = pd.DataFrame([
        {
            "Component": "Voyage Revenue",
            "Formula": "Cargo Tonnes × Freight Rate × Freight Premium",
            "Amount ($)": result["voyage_revenue"]
        },
        {
            "Component": "Fuel Cost",
            "Formula": "Sea Days × Fuel Burn × Fuel Price",
            "Amount ($)": result["fuel_cost"]
        },
        {
            "Component": "Port Costs",
            "Formula": "Load Port Cost + Discharge Port Cost",
            "Amount ($)": result["port_costs"]
        },
        {
            "Component": "Transit Costs",
            "Formula": "Intermediate Transit Ports × Transit Fee Per Port",
            "Amount ($)": result["transit_costs"]
        },
        {
            "Component": "Adjusted Route Cost",
            "Formula": "Base Route Cost × Route Cost Multiplier",
            "Amount ($)": result["adjusted_route_cost"]
        },
        {
            "Component": "Voyage Cost",
            "Formula": "Fuel + Port + Transit + Adjusted Route Cost",
            "Amount ($)": result["voyage_cost"]
        },
        {
            "Component": "Voyage Profit",
            "Formula": "Voyage Revenue - Voyage Cost",
            "Amount ($)": result["voyage_profit"]
        },
        {
            "Component": "TCE",
            "Formula": "Voyage Profit ÷ Total Voyage Days",
            "Amount ($)": result["tce"]
        }
    ])

    st.dataframe(
        explanation,
        use_container_width=True
    )

    # ========================================================
    # COMMERCIAL INTERPRETATION
    # ========================================================

    st.subheader("Commercial Interpretation")

    if result["voyage_profit"] > 0:
        st.success(
            f"Voyage profitable. Estimated profit = "
            f"${result['voyage_profit']:,.0f}"
        )
    else:
        st.error(
            f"Voyage unprofitable. Estimated loss = "
            f"${abs(result['voyage_profit']):,.0f}"
        )

    st.info(
        f"Estimated TCE = ${result['tce']:,.0f} per day"
    )

    if freight_premium_percent > 0:
        st.info(
            f"Freight premium applied: {freight_premium_percent}% "
            f"to reflect urgency, tight vessel supply, or stronger market conditions."
        )

    if transit_port_count > 0 and transit_fee_per_port > 0:
        st.info(
            f"Transit costs include {transit_port_count} intermediate port(s): "
            f"{', '.join(transit_ports)}"
        )

    # ========================================================
    # VERSION 2 NOTES
    # ========================================================

    st.caption(
        "Future enhancements: vessel availability, speed optimization, "
        "fleet optimization, market-based freight premiums, AIS integration, "
        "port congestion and live bunker prices."
    )


