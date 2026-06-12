



# pages/10_fleet_optimizer.py

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

from economics.vessel_profiles import load_vessels


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Fleet Optimizer",
    layout="wide"
)

st.title("Fleet Optimizer")



# ============================================================
# LOAD DATA
# ============================================================

VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"
CARGOES_FILE = "data/cargoes.csv"

vessels = load_vessels(VESSELS_FILE)
positions = pd.read_csv(POSITIONS_FILE)
cargoes = pd.read_csv(CARGOES_FILE)

fleet = vessels.merge(
    positions,
    on="vessel_name",
    how="left"
)


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

fleet_numeric_cols = [
    "dwt",
    "speed_knots",
    "fuel_burn_tpd",
    "cargo_capacity_tonnes",
    "available_days",
    "daily_hire_cost"
]

cargo_numeric_cols = [
    "cargo_tonnes",
    "freight_rate"
]

for col in fleet_numeric_cols:
    fleet[col] = pd.to_numeric(
        fleet[col],
        errors="coerce"
    )

for col in cargo_numeric_cols:
    cargoes[col] = pd.to_numeric(
        cargoes[col],
        errors="coerce"
    )

fleet = fleet.dropna(
    subset=[
        "vessel_name",
        "vessel_type",
        "cargo_capacity_tonnes"
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
# SHOW INPUT DATA
# ============================================================

st.subheader("Available Cargoes")

st.dataframe(
    cargoes,
    use_container_width=True
)

st.subheader("Available Fleet")

st.dataframe(
    fleet,
    use_container_width=True
)


# ============================================================
# RUN OPTIMIZATION
# ============================================================

if st.button("Run Fleet Optimization"):

    assignments = []

    available_fleet = fleet.copy()

    cargoes_sorted = cargoes.sort_values(
        by="cargo_tonnes",
        ascending=False
    )

    for _, cargo in cargoes_sorted.iterrows():

        suitable = available_fleet[
            available_fleet["cargo_capacity_tonnes"]
            >=
            cargo["cargo_tonnes"]
        ].copy()

        if suitable.empty:

            assignments.append({

                "Cargo ID":
                    cargo["cargo_id"],

                "Cargo":
                    cargo["cargo_name"],

                "Cargo Type":
                    cargo["cargo_type"],

                "Load Port":
                    cargo["load_port"],

                "Discharge Port":
                    cargo["discharge_port"],

                "Cargo Tonnes":
                    cargo["cargo_tonnes"],

                "Revenue Per Tonne":
                    cargo["freight_rate"],

                "Assigned Vessel":
                    "NO VESSEL AVAILABLE",

                "Vessel Type":
                    "",

                "Current Port":
                    "",

                "Available Days":
                    "",

                "Daily Hire Cost":
                    "",

                "Capacity":
                    "",

                "Capacity Gap":
                    "",

                "Utilization %":
                    "",

                "Revenue":
                    ""

            })

            continue

        # ====================================================
        # SCORING LOGIC
        # ====================================================

        suitable["capacity_gap"] = (
            suitable["cargo_capacity_tonnes"]
            -
            cargo["cargo_tonnes"]
        )

        suitable["utilization_pct"] = (
            cargo["cargo_tonnes"]
            /
            suitable["cargo_capacity_tonnes"]
            *
            100
        )

        suitable["availability_score"] = suitable[
            "available_days"
        ].fillna(999)

        suitable["hire_score"] = suitable[
            "daily_hire_cost"
        ].fillna(
            suitable["daily_hire_cost"].max()
        )

        # Version 1 transparent ranking:
        # 1. Smallest capacity gap
        # 2. Earliest availability
        # 3. Lowest daily hire cost
        suitable = suitable.sort_values(
            by=[
                "capacity_gap",
                "availability_score",
                "hire_score"
            ],
            ascending=[
                True,
                True,
                True
            ]
        )

        vessel = suitable.iloc[0]

        revenue = (
            cargo["cargo_tonnes"]
            *
            cargo["freight_rate"]
        )

        assignments.append({

            "Cargo ID":
                cargo["cargo_id"],

            "Cargo":
                cargo["cargo_name"],

            "Cargo Type":
                cargo["cargo_type"],

            "Load Port":
                cargo["load_port"],

            "Discharge Port":
                cargo["discharge_port"],

            "Cargo Tonnes":
                cargo["cargo_tonnes"],

            "Revenue Per Tonne":
                cargo["freight_rate"],

            "Assigned Vessel":
                vessel["vessel_name"],

            "Vessel Type":
                vessel["vessel_type"],

            "Current Port":
                vessel.get("current_port", ""),

            "Available Days":
                vessel.get("available_days", ""),

            "Daily Hire Cost":
                vessel.get("daily_hire_cost", ""),

            "Capacity":
                vessel["cargo_capacity_tonnes"],

            "Capacity Gap":
                round(vessel["capacity_gap"], 2),

            "Utilization %":
                round(vessel["utilization_pct"], 2),

            "Revenue":
                round(revenue, 2)

        })

        available_fleet = available_fleet[
            available_fleet["vessel_name"]
            !=
            vessel["vessel_name"]
        ]

    assignments_df = pd.DataFrame(assignments)


    # ========================================================
    # OUTPUT
    # ========================================================

    st.subheader("Fleet Assignments")

    st.dataframe(
        assignments_df,
        use_container_width=True
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    successful = assignments_df[
        assignments_df["Assigned Vessel"]
        !=
        "NO VESSEL AVAILABLE"
    ]

    failed = assignments_df[
        assignments_df["Assigned Vessel"]
        ==
        "NO VESSEL AVAILABLE"
    ]

    total_revenue = pd.to_numeric(
        successful["Revenue"],
        errors="coerce"
    ).sum()

    avg_utilization = pd.to_numeric(
        successful["Utilization %"],
        errors="coerce"
    ).mean()

    total_capacity = pd.to_numeric(
        successful["Capacity"],
        errors="coerce"
    ).sum()

    total_cargo = pd.to_numeric(
        successful["Cargo Tonnes"],
        errors="coerce"
    ).sum()

    fleet_utilization = (
        total_cargo
        /
        total_capacity
        *
        100
        if total_capacity > 0
        else 0
    )

    st.subheader("Fleet Summary")

    summary_df = pd.DataFrame([{

        "Total Cargoes":
            len(cargoes),

        "Successfully Assigned":
            len(successful),

        "Unassigned":
            len(failed),

        "Total Cargo Tonnes Assigned":
            round(total_cargo, 2),

        "Total Revenue":
            round(total_revenue, 2),

        "Average Vessel Utilization %":
            round(avg_utilization, 2),

        "Fleet Utilization %":
            round(fleet_utilization, 2)

    }])

    st.dataframe(
        summary_df,
        use_container_width=True
    )


    # ========================================================
    # UNASSIGNED CARGOES
    # ========================================================

    if not failed.empty:

        st.subheader("Unassigned Cargoes")

        st.dataframe(
            failed,
            use_container_width=True
        )


    # ========================================================
    # IDLE VESSELS
    # ========================================================

    assigned_vessels = set(
        successful["Assigned Vessel"]
    )

    idle_vessels = fleet[
        ~fleet["vessel_name"].isin(
            assigned_vessels
        )
    ]

    st.subheader("Idle Vessels")

    idle_display_cols = [
        "vessel_name",
        "vessel_type",
        "cargo_capacity_tonnes",
        "current_port",
        "available_days",
        "daily_hire_cost"
    ]

    st.dataframe(
        idle_vessels[
            idle_display_cols
        ],
        use_container_width=True
    )


    # ========================================================
    # COMMODITY SUMMARY
    # ========================================================

    st.subheader("Commodity Summary")

    commodity_summary = successful.groupby(
        "Cargo Type"
    ).agg({

        "Cargo Tonnes":
            "sum",

        "Revenue":
            "sum",

        "Assigned Vessel":
            "count"

    }).reset_index()

    commodity_summary = commodity_summary.rename(
        columns={
            "Assigned Vessel": "Assigned Cargo Count"
        }
    )

    st.dataframe(
        commodity_summary,
        use_container_width=True
    )


    # ========================================================
    # EXPLANATION
    # ========================================================

    st.subheader("Optimization Method")

    st.write(
        """
        Cargoes are processed largest first.

        For each cargo:

        1. Find all vessels that can carry it.
        2. Rank suitable vessels by:
           - smallest excess capacity
           - earliest available days
           - lowest daily hire cost
        3. Assign the best-ranked vessel.
        4. Remove that vessel from the available fleet.
        5. Continue until all cargoes are processed.

        This version is transparent and easy to validate.
        It does not yet optimize true profit, TCE, positioning cost,
        bunker fuel, port congestion or laycan windows.
        """
    )

st.caption(
    "Future enhancements: positioning cost, voyage economics, "
    "TCE ranking, fleet profit optimization, cargo laycan windows, "
    "multi-cargo scheduling and stowage planning."
)