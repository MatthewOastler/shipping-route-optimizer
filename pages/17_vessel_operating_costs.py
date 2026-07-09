




# pages/17_vessel_operating_costs.py

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
    page_title="Vessel Operating Costs",
    layout="wide"
)

st.title("Vessel Operating Costs")

st.caption("Accurate results without lying to ourselves")


# ============================================================
# LOAD DATA
# ============================================================

VESSELS_FILE = "data/vessels.csv"
OPERATING_COSTS_FILE = "data/vessel_operating_costs.csv"

vessels = load_vessels(VESSELS_FILE)
opex = pd.read_csv(OPERATING_COSTS_FILE)


# ============================================================
# CLEAN DATA
# ============================================================

cost_cols = [
    "crew_cost_per_day",
    "insurance_cost_per_day",
    "maintenance_cost_per_day",
    "technical_management_cost_per_day",
    "stores_cost_per_day",
    "admin_overhead_cost_per_day",
    "total_opex_per_day"
]

for col in cost_cols:
    opex[col] = pd.to_numeric(
        opex[col],
        errors="coerce"
    )

vessels["cargo_capacity_tonnes"] = pd.to_numeric(
    vessels["cargo_capacity_tonnes"],
    errors="coerce"
)

vessels["dwt"] = pd.to_numeric(
    vessels["dwt"],
    errors="coerce"
)

fleet_costs = vessels.merge(
    opex,
    on="vessel_type",
    how="left"
)


# ============================================================
# INPUTS
# ============================================================

st.subheader("Vessel Selection")

selected_vessel = st.selectbox(
    "Select Vessel",
    sorted(fleet_costs["vessel_name"].dropna().tolist())
)

vessel = fleet_costs[
    fleet_costs["vessel_name"] == selected_vessel
].iloc[0]


# ============================================================
# USER-EDITABLE DAYS
# ============================================================

st.subheader("Voyage / Ownership Period")

col1, col2, col3 = st.columns(3)

with col1:
    voyage_days = st.number_input(
        "Voyage Days",
        min_value=0.0,
        value=20.0,
        step=0.5
    )

with col2:
    idle_days = st.number_input(
        "Idle Days",
        min_value=0.0,
        value=0.0,
        step=0.5
    )

with col3:
    opex_multiplier = st.number_input(
        "OPEX Multiplier",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1
    )

total_days = voyage_days + idle_days


# ============================================================
# CALCULATE
# ============================================================

missing_cost_data = pd.isna(vessel["total_opex_per_day"])

if missing_cost_data:
    st.error(
        f"No operating cost data found for vessel type: {vessel['vessel_type']}"
    )
    st.stop()

crew_cost = float(vessel["crew_cost_per_day"]) * total_days * opex_multiplier
insurance_cost = float(vessel["insurance_cost_per_day"]) * total_days * opex_multiplier
maintenance_cost = float(vessel["maintenance_cost_per_day"]) * total_days * opex_multiplier
technical_management_cost = (
    float(vessel["technical_management_cost_per_day"])
    * total_days
    * opex_multiplier
)
stores_cost = float(vessel["stores_cost_per_day"]) * total_days * opex_multiplier
admin_overhead_cost = (
    float(vessel["admin_overhead_cost_per_day"])
    * total_days
    * opex_multiplier
)

total_opex_per_day = float(vessel["total_opex_per_day"]) * opex_multiplier

total_opex = (
    crew_cost
    + insurance_cost
    + maintenance_cost
    + technical_management_cost
    + stores_cost
    + admin_overhead_cost
)


# ============================================================
# OUTPUT: VESSEL PROFILE
# ============================================================

st.subheader("Vessel Profile")

profile_df = pd.DataFrame([{
    "Vessel": vessel["vessel_name"],
    "Type": vessel["vessel_type"],
    "DWT": vessel["dwt"],
    "Cargo Capacity": vessel["cargo_capacity_tonnes"],
    "Total OPEX / Day": round(total_opex_per_day, 2)
}])

st.dataframe(
    profile_df,
    use_container_width=True
)


# ============================================================
# OUTPUT: DAILY COST BREAKDOWN
# ============================================================

st.subheader("Daily Operating Cost Breakdown")

daily_df = pd.DataFrame([{
    "Crew / Labour": round(float(vessel["crew_cost_per_day"]) * opex_multiplier, 2),
    "Insurance": round(float(vessel["insurance_cost_per_day"]) * opex_multiplier, 2),
    "Maintenance": round(float(vessel["maintenance_cost_per_day"]) * opex_multiplier, 2),
    "Technical Management": round(float(vessel["technical_management_cost_per_day"]) * opex_multiplier, 2),
    "Stores": round(float(vessel["stores_cost_per_day"]) * opex_multiplier, 2),
    "Admin Overhead": round(float(vessel["admin_overhead_cost_per_day"]) * opex_multiplier, 2),
    "Total OPEX / Day": round(total_opex_per_day, 2)
}])

st.dataframe(
    daily_df,
    use_container_width=True
)


# ============================================================
# OUTPUT: TOTAL PERIOD COST
# ============================================================

st.subheader("Total Operating Cost For Period")

period_df = pd.DataFrame([{
    "Voyage Days": voyage_days,
    "Idle Days": idle_days,
    "Total Days": total_days,
    "Crew / Labour": round(crew_cost, 2),
    "Insurance": round(insurance_cost, 2),
    "Maintenance": round(maintenance_cost, 2),
    "Technical Management": round(technical_management_cost, 2),
    "Stores": round(stores_cost, 2),
    "Admin Overhead": round(admin_overhead_cost, 2),
    "Total OPEX": round(total_opex, 2)
}])

st.dataframe(
    period_df,
    use_container_width=True
)


# ============================================================
# COMMERCIAL INTERPRETATION
# ============================================================

st.subheader("Commercial Interpretation")

st.info(
    f"Estimated operating cost for {selected_vessel} over "
    f"{total_days:.1f} days is ${total_opex:,.0f}."
)

st.info(
    f"Estimated daily operating cost is ${total_opex_per_day:,.0f}/day."
)

st.warning(
    "This is OPEX only. It does not include bunker fuel, port costs, "
    "canal costs, financing, depreciation, voyage-specific agency costs, "
    "or charter-party penalties."
)


# ============================================================
# FULL DATASET
# ============================================================

st.subheader("Operating Cost Reference Table")

st.dataframe(
    opex,
    use_container_width=True
)


# ============================================================
# NOTES
# ============================================================

st.markdown("---")

st.info(
    """
    Labour/crew cost is included here as a separate OPEX component.

    In your current app, daily_hire_cost in vessel_positions.csv is a broader
    commercial assumption. It can represent either:

    1. market hire rate, if modelling chartered-in vessels; or
    2. owner-equivalent daily cost, if modelling owned vessels.

    For better accuracy, keep these concepts separate:

    - OPEX = crew, insurance, maintenance, management, stores, admin
    - Hire Rate = what it costs to charter the vessel in the market
    - Voyage Cost = fuel, ports, canal, transit, route penalties
    """
)

st.caption(
    "Future enhancement: integrate OPEX into Voyage Economics, Fleet P&L, "
    "and Master Shipping Dashboard as a separate cost layer."
)