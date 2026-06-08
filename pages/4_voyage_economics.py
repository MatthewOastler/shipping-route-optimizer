# # pages/4_voyage_economics.py

# import sys
# import os

# sys.path.append(
#     os.path.abspath(
#         os.path.join(
#             os.path.dirname(__file__),
#             ".."
#         )
#     )
# )

# import streamlit as st
# import pandas as pd

# from optimizer.dijkstra import build_graph, shortest_path


# # ============================================================
# # PAGE CONFIG
# # ============================================================

# st.set_page_config(
#     page_title="Voyage Economics",
#     layout="wide"
# )

# st.title("Voyage Economics")

# st.caption(
#     "Accurate results without lying to ourselves"
# )

# # ============================================================
# # LOAD DATA
# # ============================================================

# ROUTES_FILE = "data/generated_routes.csv"

# routes = pd.read_csv(
#     ROUTES_FILE
# )

# graph = build_graph(
#     routes
# )

# ports = sorted(
#     set(routes["origin_port"]).union(
#         set(routes["destination_port"])
#     )
# )

# # ============================================================
# # ROUTE SELECTION
# # ============================================================

# st.subheader(
#     "Voyage Route"
# )

# col1, col2 = st.columns(2)

# with col1:

#     start_port = st.selectbox(
#         "Load Port",
#         ports
#     )

# with col2:

#     end_port = st.selectbox(
#         "Discharge Port",
#         ports
#     )

# # ============================================================
# # VESSEL INPUTS
# # ============================================================

# st.subheader(
#     "Vessel Assumptions"
# )

# col1, col2, col3 = st.columns(3)

# with col1:

#     vessel_speed = st.number_input(
#         "Vessel Speed (knots)",
#         min_value=5.0,
#         max_value=30.0,
#         value=13.0,
#         step=0.5
#     )

# with col2:

#     fuel_burn = st.number_input(
#         "Fuel Consumption (t/day)",
#         min_value=1.0,
#         max_value=200.0,
#         value=30.0,
#         step=1.0
#     )

# with col3:

#     fuel_price = st.number_input(
#         "Fuel Price ($/t)",
#         min_value=100.0,
#         max_value=2000.0,
#         value=600.0,
#         step=10.0
#     )

# # ============================================================
# # CARGO INPUTS
# # ============================================================

# st.subheader(
#     "Cargo Assumptions"
# )

# col1, col2 = st.columns(2)

# with col1:

#     cargo_tonnes = st.number_input(
#         "Cargo Tonnes",
#         min_value=1000,
#         max_value=500000,
#         value=50000,
#         step=1000
#     )

# with col2:

#     freight_rate = st.number_input(
#         "Freight Rate ($/t)",
#         min_value=1.0,
#         max_value=500.0,
#         value=25.0,
#         step=1.0
#     )

# # ============================================================
# # PORT COSTS
# # ============================================================

# st.subheader(
#     "Port Costs"
# )

# col1, col2 = st.columns(2)

# with col1:

#     load_port_cost = st.number_input(
#         "Load Port Cost ($)",
#         value=25000
#     )

# with col2:

#     discharge_port_cost = st.number_input(
#         "Discharge Port Cost ($)",
#         value=25000
#     )

# # ============================================================
# # RUN CALCULATION
# # ============================================================

# if st.button(
#     "Calculate Voyage Economics"
# ):

#     try:

#         path, route_cost = shortest_path(
#             graph,
#             start_port,
#             end_port
#         )

#     except Exception as err:

#         st.error(
#             f"Unable to calculate route: {err}"
#         )

#         st.stop()

#     # ========================================================
#     # DISTANCE
#     # ========================================================

#     total_distance = 0

#     for i in range(len(path) - 1):

#         edge = graph[
#             path[i]
#         ][
#             path[i + 1]
#         ]

#         total_distance += edge["distance"]

#     # ========================================================
#     # SEA DAYS
#     # ========================================================

#     sea_days = (
#         total_distance /
#         vessel_speed /
#         24
#     )

#     # ========================================================
#     # FUEL
#     # ========================================================

#     fuel_consumed = (
#         sea_days *
#         fuel_burn
#     )

#     fuel_cost = (
#         fuel_consumed *
#         fuel_price
#     )

#     # ========================================================
#     # REVENUE
#     # ========================================================

#     voyage_revenue = (
#         cargo_tonnes *
#         freight_rate
#     )

#     # ========================================================
#     # COSTS
#     # ========================================================

#     port_costs = (
#         load_port_cost +
#         discharge_port_cost
#     )

#     voyage_cost = (
#         fuel_cost +
#         port_costs +
#         route_cost
#     )

#     # ========================================================
#     # PROFIT
#     # ========================================================

#     voyage_profit = (
#         voyage_revenue -
#         voyage_cost
#     )

#     # ========================================================
#     # TCE
#     # ========================================================

#     if sea_days > 0:

#         tce = (
#             voyage_profit /
#             sea_days
#         )

#     else:

#         tce = 0

#     # ========================================================
#     # OUTPUT
#     # ========================================================

#     st.subheader(
#         "Selected Route"
#     )

#     st.write(
#         " → ".join(path)
#     )

#     # ========================================================
#     # SUMMARY TABLE
#     # ========================================================

#     summary = pd.DataFrame([{

#         "Distance NM":
#             round(total_distance, 2),

#         "Sea Days":
#             round(sea_days, 2),

#         "Fuel Consumed (t)":
#             round(fuel_consumed, 2),

#         "Fuel Cost ($)":
#             round(fuel_cost, 2),

#         "Port Costs ($)":
#             round(port_costs, 2),

#         "Route Costs ($)":
#             round(route_cost, 2),

#         "Voyage Revenue ($)":
#             round(voyage_revenue, 2),

#         "Voyage Cost ($)":
#             round(voyage_cost, 2),

#         "Voyage Profit ($)":
#             round(voyage_profit, 2),

#         "TCE ($/day)":
#             round(tce, 2)

#     }])

#     st.dataframe(
#         summary,
#         use_container_width=True
#     )

#     # ========================================================
#     # COMMERCIAL INTERPRETATION
#     # ========================================================

#     st.subheader(
#         "Commercial Interpretation"
#     )

#     if voyage_profit > 0:

#         st.success(
#             f"Voyage profitable. "
#             f"Estimated profit = "
#             f"${voyage_profit:,.0f}"
#         )

#     else:

#         st.error(
#             f"Voyage unprofitable. "
#             f"Estimated loss = "
#             f"${abs(voyage_profit):,.0f}"
#         )

#     st.info(
#         f"Estimated TCE = "
#         f"${tce:,.0f} per day"
#     )
























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

from optimizer.dijkstra import (
    build_graph,
    shortest_path
)

from economics.voyage_economics import (
    calculate_voyage_economics
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Voyage Economics",
    layout="wide"
)

st.title("Voyage Economics")

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
# ROUTE SELECTION
# ============================================================

st.subheader(
    "Voyage Route"
)

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
# VESSEL INPUTS
# ============================================================

st.subheader(
    "Vessel Assumptions"
)

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
        max_value=2000.0,
        value=600.0,
        step=10.0
    )

# ============================================================
# CARGO INPUTS
# ============================================================

st.subheader(
    "Cargo Assumptions"
)

col1, col2 = st.columns(2)

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

# ============================================================
# PORT COSTS
# ============================================================

st.subheader(
    "Port Costs"
)

col1, col2 = st.columns(2)

with col1:

    load_port_cost = st.number_input(
        "Load Port Cost ($)",
        min_value=0,
        value=25000,
        step=1000
    )

with col2:

    discharge_port_cost = st.number_input(
        "Discharge Port Cost ($)",
        min_value=0,
        value=25000,
        step=1000
    )

# ============================================================
# CALCULATE
# ============================================================

if st.button(
    "Calculate Voyage Economics"
):

    if start_port == end_port:

        st.warning(
            "Load Port and Discharge Port must be different."
        )

        st.stop()

    try:

        path, route_cost = shortest_path(
            graph,
            start_port,
            end_port
        )

    except Exception as err:

        st.error(
            f"Unable to calculate route: {err}"
        )

        st.stop()

    # ========================================================
    # DISTANCE
    # ========================================================

    total_distance = 0

    for i in range(len(path) - 1):

        origin = path[i]
        destination = path[i + 1]

        edge = graph[origin][destination]

        total_distance += edge["distance"]

    # ========================================================
    # VOYAGE ECONOMICS ENGINE
    # ========================================================

    result = calculate_voyage_economics(

        distance_nm=total_distance,

        route_cost=route_cost,

        cargo_tonnes=cargo_tonnes,

        freight_rate=freight_rate,

        vessel_speed_knots=vessel_speed,

        fuel_burn_tonnes_per_day=fuel_burn,

        fuel_price=fuel_price,

        load_port_cost=load_port_cost,

        discharge_port_cost=discharge_port_cost
    )

    # ========================================================
    # ROUTE
    # ========================================================

    st.subheader(
        "Selected Route"
    )

    st.write(
        " → ".join(path)
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader(
        "Voyage Summary"
    )

    summary = pd.DataFrame([{

        "Distance NM":
            result["distance_nm"],

        "Sea Days":
            result["sea_days"],

        "Fuel Consumed (t)":
            result["fuel_consumed"],

        "Fuel Cost ($)":
            result["fuel_cost"],

        "Port Costs ($)":
            result["port_costs"],

        "Route Costs ($)":
            result["route_cost"],

        "Voyage Revenue ($)":
            result["voyage_revenue"],

        "Voyage Cost ($)":
            result["voyage_cost"],

        "Voyage Profit ($)":
            result["voyage_profit"],

        "TCE ($/day)":
            result["tce"]

    }])

    st.dataframe(
        summary,
        use_container_width=True
    )

    # ========================================================
    # COMMERCIAL INTERPRETATION
    # ========================================================

    st.subheader(
        "Commercial Interpretation"
    )

    if result["voyage_profit"] > 0:

        st.success(
            f"Voyage profitable. "
            f"Estimated profit = "
            f"${result['voyage_profit']:,.0f}"
        )

    else:

        st.error(
            f"Voyage unprofitable. "
            f"Estimated loss = "
            f"${abs(result['voyage_profit']):,.0f}"
        )

    st.info(
        f"Estimated TCE = "
        f"${result['tce']:,.0f} per day"
    )

    # ========================================================
    # VERSION 2 NOTES
    # ========================================================

    st.caption(
        "Future enhancements: ballast days, waiting days, "
        "vessel availability, freight premiums, fleet "
        "optimization, speed optimization and market-based TCE."
    )