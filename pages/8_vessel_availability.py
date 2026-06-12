

# pages/8_vessel_availability.py

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


st.set_page_config(
    page_title="Vessel Availability",
    layout="wide"
)

st.title("Vessel Availability")

st.caption("Accurate results without lying to ourselves")


# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"
VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"

routes = pd.read_csv(ROUTES_FILE)
vessels = load_vessels(VESSELS_FILE)
positions = pd.read_csv(POSITIONS_FILE)

graph = build_graph(routes)

ports = sorted(
    set(routes["origin_port"]).union(
        set(routes["destination_port"])
    )
)

fleet = vessels.merge(
    positions,
    on="vessel_name",
    how="left"
)

numeric_cols = [
    "dwt",
    "speed_knots",
    "fuel_burn_tpd",
    "cargo_capacity_tonnes",
    "available_days",
    "daily_hire_cost"
]

for col in numeric_cols:
    fleet[col] = pd.to_numeric(
        fleet[col],
        errors="coerce"
    )

fleet = fleet.dropna(
    subset=numeric_cols
)


# ============================================================
# INPUTS
# ============================================================

st.subheader("Cargo and Load Port")

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
    load_port = st.selectbox(
        "Load Port",
        ports
    )

# ============================================================
# FILTER CAPABLE VESSELS
# ============================================================

capable_vessels = fleet[
    fleet["cargo_capacity_tonnes"] >= cargo_tonnes
].copy()

st.subheader("Capable Vessels")

if capable_vessels.empty:

    st.error("No vessel in the fleet can carry this cargo.")
    st.stop()

st.dataframe(
    capable_vessels[
        [
            "vessel_name",
            "vessel_type",
            "cargo_capacity_tonnes",
            "current_port",
            "available_days",
            "daily_hire_cost",
            "speed_knots",
            "fuel_burn_tpd"
        ]
    ].sort_values(
        by="cargo_capacity_tonnes"
    ),
    use_container_width=True
)


# ============================================================
# CALCULATE POSITIONING TIME
# ============================================================

results = []

for _, vessel in capable_vessels.iterrows():

    current_port = vessel["current_port"]

    try:

        path, route_cost = shortest_path(
            graph,
            current_port,
            load_port
        )

        distance_nm = 0

        for i in range(len(path) - 1):

            edge = graph[
                path[i]
            ][
                path[i + 1]
            ]

            distance_nm += edge["distance"]

        positioning_days = (
            distance_nm
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

        utilization = (
            cargo_tonnes
            /
            vessel["cargo_capacity_tonnes"]
            *
            100
        )

        results.append({

            "Vessel":
                vessel["vessel_name"],

            "Type":
                vessel["vessel_type"],

            "Current Port":
                current_port,

            "Route to Load Port":
                " → ".join(path),

            "Cargo Capacity":
                vessel["cargo_capacity_tonnes"],

            "Utilization %":
                round(utilization, 2),

            "Available Days":
                round(vessel["available_days"], 2),

            "Positioning Distance NM":
                round(distance_nm, 2),

            "Positioning Days":
                round(positioning_days, 2),

            "Earliest Ready Days":
                round(earliest_ready_days, 2),

            "Daily Hire Cost":
                round(vessel["daily_hire_cost"], 2),

            "Positioning Hire Cost":
                round(positioning_hire_cost, 2),

            "Speed":
                vessel["speed_knots"],

            "Fuel Burn":
                vessel["fuel_burn_tpd"]

        })

    except Exception as err:

        results.append({

            "Vessel":
                vessel["vessel_name"],

            "Type":
                vessel["vessel_type"],

            "Current Port":
                current_port,

            "Route to Load Port":
                "NO ROUTE",

            "Cargo Capacity":
                vessel["cargo_capacity_tonnes"],

            "Utilization %":
                round(
                    cargo_tonnes
                    /
                    vessel["cargo_capacity_tonnes"]
                    *
                    100,
                    2
                ),

            "Available Days":
                vessel["available_days"],

            "Positioning Distance NM":
                None,

            "Positioning Days":
                None,

            "Earliest Ready Days":
                None,

            "Daily Hire Cost":
                vessel["daily_hire_cost"],

            "Positioning Hire Cost":
                None,

            "Speed":
                vessel["speed_knots"],

            "Fuel Burn":
                vessel["fuel_burn_tpd"],

            "Error":
                str(err)

        })


results_df = pd.DataFrame(results)

valid_results = results_df[
    results_df["Earliest Ready Days"].notna()
].copy()


# ============================================================
# OUTPUT
# ============================================================

st.subheader("Availability Ranking")

if valid_results.empty:

    st.error("No capable vessel has a route to the selected load port.")
    st.stop()

valid_results = valid_results.sort_values(
    by=[
        "Earliest Ready Days",
        "Positioning Hire Cost"
    ]
)

st.dataframe(
    valid_results,
    use_container_width=True
)


# ============================================================
# BEST VESSELS
# ============================================================

soonest = valid_results.loc[
    valid_results["Earliest Ready Days"].idxmin()
]

cheapest_positioning = valid_results.loc[
    valid_results["Positioning Hire Cost"].idxmin()
]

best_utilization = valid_results.iloc[
    (
        valid_results["Utilization %"] - 85
    ).abs().argsort()
].iloc[0]

st.subheader("Recommendations")

col1, col2, col3 = st.columns(3)

with col1:
    st.success(
        f"Soonest Ready: {soonest['Vessel']} "
        f"({soonest['Earliest Ready Days']:.1f} days)"
    )

with col2:
    st.info(
        f"Lowest Positioning Cost: {cheapest_positioning['Vessel']} "
        f"(${cheapest_positioning['Positioning Hire Cost']:,.0f})"
    )

with col3:
    st.warning(
        f"Best Utilization Fit: {best_utilization['Vessel']} "
        f"({best_utilization['Utilization %']:.1f}%)"
    )


# ============================================================
# EXPLANATION
# ============================================================

st.subheader("Method Explanation")

st.write(
    """
    This page checks which vessels can carry the cargo, then estimates how long
    each vessel would take to reach the load port.

    Earliest Ready Days =
    Vessel Available Days + Positioning Sailing Days

    Positioning Sailing Days =
    Distance from Current Port to Load Port ÷ Vessel Speed ÷ 24

    Positioning Hire Cost =
    Earliest Ready Days × Daily Hire Cost
    """
)

st.caption(
    "Future enhancement: include positioning fuel cost, ballast economics, "
    "actual laycan windows, port congestion and freight premium effects."
)