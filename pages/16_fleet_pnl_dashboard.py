# pages/16_fleet_pnl_dashboard.py

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
    page_title="Fleet P&L Dashboard",
    layout="wide"
)

st.title("Fleet P&L Dashboard")

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

st.subheader("Fleet P&L Assumptions")

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
    port_cost_per_call = st.number_input(
        "Port Cost Per Call ($)",
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

col1, col2 = st.columns(2)

with col1:
    include_congestion = st.checkbox(
        "Include Port Congestion Days",
        value=True
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
# RUN
# ============================================================

if st.button("Run Fleet P&L Dashboard"):

    available_fleet = fleet.copy()

    cargoes_sorted = cargoes.sort_values(
        by="cargo_tonnes",
        ascending=False
    )

    rows = []

    for _, cargo in cargoes_sorted.iterrows():

        suitable = available_fleet[
            available_fleet["cargo_capacity_tonnes"]
            >=
            cargo["cargo_tonnes"]
        ].copy()

        if suitable.empty:
            rows.append({
                "Cargo ID": cargo["cargo_id"],
                "Cargo": cargo["cargo_name"],
                "Cargo Type": cargo["cargo_type"],
                "Assigned Vessel": "NO VESSEL",
                "Revenue": 0,
                "Cost": 0,
                "Profit": 0,
                "TCE": 0
            })

            continue

        suitable["capacity_gap"] = (
            suitable["cargo_capacity_tonnes"]
            -
            cargo["cargo_tonnes"]
        )

        suitable = suitable.sort_values(
            by=[
                "capacity_gap",
                "available_days",
                "daily_hire_cost"
            ],
            ascending=[
                True,
                True,
                True
            ]
        )

        vessel = suitable.iloc[0]

        try:
            path, route_cost = shortest_path(
                graph,
                cargo["load_port"],
                cargo["discharge_port"]
            )

        except Exception:
            rows.append({
                "Cargo ID": cargo["cargo_id"],
                "Cargo": cargo["cargo_name"],
                "Cargo Type": cargo["cargo_type"],
                "Assigned Vessel": "NO ROUTE",
                "Revenue": 0,
                "Cost": 0,
                "Profit": 0,
                "TCE": 0
            })

            continue

        distance_nm = 0.0

        for i in range(len(path) - 1):
            edge = graph[path[i]][path[i + 1]]
            distance_nm += float(edge["distance"])

        transit_port_count = max(0, len(path) - 2)

        congestion_days = 0.0

        if include_congestion:
            load_row = congestion[
                congestion["port"] == cargo["load_port"]
            ]

            discharge_row = congestion[
                congestion["port"] == cargo["discharge_port"]
            ]

            congestion_days = (
                (
                    float(load_row.iloc[0]["delay_days"])
                    if not load_row.empty
                    else 0.0
                )
                +
                (
                    float(discharge_row.iloc[0]["delay_days"])
                    if not discharge_row.empty
                    else 0.0
                )
            )

        economics = calculate_voyage_economics(
            distance_nm=distance_nm,
            route_cost=route_cost,
            cargo_tonnes=cargo["cargo_tonnes"],
            freight_rate=cargo["freight_rate"],
            vessel_speed_knots=vessel["speed_knots"],
            fuel_burn_tonnes_per_day=vessel["fuel_burn_tpd"],
            fuel_price=fuel_price,
            load_port_cost=port_cost_per_call,
            discharge_port_cost=port_cost_per_call,
            freight_premium_percent=0,
            ballast_days=vessel["available_days"],
            waiting_days=congestion_days,
            port_days=0,
            transit_port_count=transit_port_count,
            transit_fee_per_port=transit_fee_per_port,
            route_cost_multiplier=route_cost_multiplier
        )

        hire_cost = (
            economics["total_voyage_days"]
            *
            vessel["daily_hire_cost"]
        )

        net_profit = (
            economics["voyage_profit"]
            -
            hire_cost
        )

        net_tce = (
            net_profit
            /
            economics["total_voyage_days"]
            if economics["total_voyage_days"] > 0
            else 0
        )

        utilization = (
            cargo["cargo_tonnes"]
            /
            vessel["cargo_capacity_tonnes"]
            *
            100
        )

        rows.append({
            "Cargo ID": cargo["cargo_id"],
            "Cargo": cargo["cargo_name"],
            "Cargo Type": cargo["cargo_type"],
            "Load Port": cargo["load_port"],
            "Discharge Port": cargo["discharge_port"],
            "Assigned Vessel": vessel["vessel_name"],
            "Vessel Type": vessel["vessel_type"],
            "Cargo Tonnes": cargo["cargo_tonnes"],
            "Utilization %": round(utilization, 2),
            "Route": " → ".join(path),
            "Distance NM": economics["distance_nm"],
            "Voyage Days": economics["total_voyage_days"],
            "Revenue": economics["voyage_revenue"],
            "Voyage Cost": economics["voyage_cost"],
            "Hire Cost": round(hire_cost, 2),
            "Net Profit": round(net_profit, 2),
            "Net TCE": round(net_tce, 2)
        })

        available_fleet = available_fleet[
            available_fleet["vessel_name"]
            !=
            vessel["vessel_name"]
        ]

    pnl_df = pd.DataFrame(rows)

    st.subheader("Fleet P&L")

    st.dataframe(
        pnl_df,
        use_container_width=True
    )

    successful = pnl_df[
        ~pnl_df["Assigned Vessel"].isin(
            [
                "NO VESSEL",
                "NO ROUTE"
            ]
        )
    ]

    total_revenue = pd.to_numeric(
        successful["Revenue"],
        errors="coerce"
    ).sum()

    total_cost = (
        pd.to_numeric(
            successful["Voyage Cost"],
            errors="coerce"
        ).sum()
        +
        pd.to_numeric(
            successful["Hire Cost"],
            errors="coerce"
        ).sum()
    )

    total_profit = pd.to_numeric(
        successful["Net Profit"],
        errors="coerce"
    ).sum()

    total_days = pd.to_numeric(
        successful["Voyage Days"],
        errors="coerce"
    ).sum()

    fleet_tce = (
        total_profit
        /
        total_days
        if total_days > 0
        else 0
    )

    st.subheader("Fleet Summary")

    summary_df = pd.DataFrame([{
        "Assigned Cargoes": len(successful),
        "Total Revenue": round(total_revenue, 2),
        "Total Cost": round(total_cost, 2),
        "Total Profit": round(total_profit, 2),
        "Total Voyage Days": round(total_days, 2),
        "Fleet TCE": round(fleet_tce, 2)
    }])

    st.dataframe(
        summary_df,
        use_container_width=True
    )

    if total_profit > 0:
        st.success(
            f"Fleet plan profitable. Estimated total profit: ${total_profit:,.0f}"
        )

    else:
        st.error(
            f"Fleet plan unprofitable. Estimated loss: ${abs(total_profit):,.0f}"
        )

st.caption(
    "Future enhancement: true mathematical optimization, cargo laycan windows, "
    "positioning fuel cost, multiple voyages per vessel and market rate scenarios."
)