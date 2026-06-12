

# pages/11_stowage_planner.py

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

import math
import streamlit as st
import pandas as pd

from economics.vessel_profiles import load_vessels


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Stowage Planner",
    layout="wide"
)

st.title("Stowage Planner")



# ============================================================
# LOAD DATA
# ============================================================

VESSELS_FILE = "data/vessels.csv"
CARGOES_FILE = "data/cargoes.csv"
STOWAGE_FILE = "data/cargo_stowage_factors.csv"

vessels = load_vessels(VESSELS_FILE)
cargoes = pd.read_csv(CARGOES_FILE)
stowage_factors = pd.read_csv(STOWAGE_FILE)


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

for col in ["dwt", "cargo_capacity_tonnes"]:
    vessels[col] = pd.to_numeric(
        vessels[col],
        errors="coerce"
    )

for col in ["cargo_tonnes", "freight_rate"]:
    cargoes[col] = pd.to_numeric(
        cargoes[col],
        errors="coerce"
    )

stowage_factors["stowage_factor_m3_per_tonne"] = pd.to_numeric(
    stowage_factors["stowage_factor_m3_per_tonne"],
    errors="coerce"
)

vessels = vessels.dropna(
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
        "cargo_tonnes"
    ]
)

stowage_factors = stowage_factors.dropna(
    subset=[
        "cargo_name",
        "stowage_factor_m3_per_tonne"
    ]
)


# ============================================================
# INPUTS
# ============================================================

st.subheader("Cargo and Vessel Selection")

col1, col2 = st.columns(2)

with col1:

    # selected_cargo_id = st.selectbox(
    #     "Select Cargo",
    #     cargoes["cargo_id"].tolist()
    # )
    
    
    cargoes["cargo_display"] = (
        cargoes["cargo_name"]
        + " ("
        + cargoes["cargo_tonnes"].astype(str)
        + " t) "
        + cargoes["load_port"]
        + " → "
        + cargoes["discharge_port"]
    )
    
    selected_display = st.selectbox(
        "Select Cargo",
        cargoes["cargo_display"].tolist()
    )
    
    cargo = cargoes[
        cargoes["cargo_display"]
        ==
        selected_display
    ].iloc[0]

with col2:

    selected_vessel_name = st.selectbox(
        "Select Vessel",
        vessels["vessel_name"].tolist()
    )


# cargo = cargoes[
#     cargoes["cargo_id"] == selected_cargo_id
# ].iloc[0]

vessel = vessels[
    vessels["vessel_name"] == selected_vessel_name
].iloc[0]


# ============================================================
# STOWAGE FACTOR LOOKUP
# ============================================================

matching_factor = stowage_factors[
    stowage_factors["cargo_name"] == cargo["cargo_name"]
]

if matching_factor.empty:

    st.error(
        f"No stowage factor found for cargo: {cargo['cargo_name']}"
    )

    st.stop()

factor = matching_factor.iloc[0]


# ============================================================
# USER-EDITABLE ASSUMPTIONS
# ============================================================

st.subheader("Stowage Assumptions")

col1, col2, col3 = st.columns(3)

with col1:

    stowage_factor = st.number_input(
        "Stowage Factor (m³/tonne)",
        min_value=0.10,
        max_value=5.00,
        value=float(factor["stowage_factor_m3_per_tonne"]),
        step=0.05
    )

with col2:

    number_of_holds = st.number_input(
        "Number of Cargo Holds",
        min_value=1,
        max_value=12,
        value=5,
        step=1
    )

with col3:

    hold_volume_m3 = st.number_input(
        "Volume Per Hold (m³)",
        min_value=1000.0,
        max_value=100000.0,
        value=15000.0,
        step=1000.0
    )


col1, col2, col3 = st.columns(3)

with col1:

    max_tonnes_per_hold = st.number_input(
        "Max Tonnes Per Hold",
        min_value=1000.0,
        max_value=100000.0,
        value=25000.0,
        step=1000.0
    )

with col2:

    operational_margin_percent = st.number_input(
        "Operational Margin (%)",
        min_value=0.0,
        max_value=30.0,
        value=5.0,
        step=1.0
    )

with col3:

    cargo_tonnes_override = st.number_input(
        "Cargo Tonnes Override",
        min_value=0.0,
        max_value=500000.0,
        value=float(cargo["cargo_tonnes"]),
        step=1000.0
    )


# ============================================================
# CALCULATE
# ============================================================

if st.button("Calculate Stowage Plan"):

    cargo_tonnes = float(cargo_tonnes_override)

    cargo_volume_m3 = (
        cargo_tonnes
        *
        stowage_factor
    )

    total_hold_volume_m3 = (
        number_of_holds
        *
        hold_volume_m3
    )

    usable_hold_volume_m3 = (
        total_hold_volume_m3
        *
        (1 - operational_margin_percent / 100)
    )

    total_hold_weight_capacity = (
        number_of_holds
        *
        max_tonnes_per_hold
    )

    usable_weight_capacity = (
        total_hold_weight_capacity
        *
        (1 - operational_margin_percent / 100)
    )

    vessel_capacity_tonnes = float(
        vessel["cargo_capacity_tonnes"]
    )

    vessel_capacity_with_margin = (
        vessel_capacity_tonnes
        *
        (1 - operational_margin_percent / 100)
    )

    volume_utilization = (
        cargo_volume_m3
        /
        usable_hold_volume_m3
        *
        100
        if usable_hold_volume_m3 > 0
        else 0
    )

    hold_weight_utilization = (
        cargo_tonnes
        /
        usable_weight_capacity
        *
        100
        if usable_weight_capacity > 0
        else 0
    )

    vessel_weight_utilization = (
        cargo_tonnes
        /
        vessel_capacity_with_margin
        *
        100
        if vessel_capacity_with_margin > 0
        else 0
    )

    # ========================================================
    # HOLD ALLOCATION
    # ========================================================

    base_tonnes_per_hold = cargo_tonnes / number_of_holds

    hold_rows = []

    remaining_tonnes = cargo_tonnes

    for hold_no in range(1, int(number_of_holds) + 1):

        holds_left = int(number_of_holds) - hold_no + 1

        planned_tonnes = min(
            base_tonnes_per_hold,
            remaining_tonnes
        )

        if hold_no == int(number_of_holds):
            planned_tonnes = remaining_tonnes

        planned_volume = planned_tonnes * stowage_factor

        weight_util = (
            planned_tonnes
            /
            max_tonnes_per_hold
            *
            100
            if max_tonnes_per_hold > 0
            else 0
        )

        volume_util = (
            planned_volume
            /
            hold_volume_m3
            *
            100
            if hold_volume_m3 > 0
            else 0
        )

        hold_rows.append({

            "Hold":
                f"Hold {hold_no}",

            "Planned Tonnes":
                round(planned_tonnes, 2),

            "Required Volume m³":
                round(planned_volume, 2),

            "Hold Weight Utilization %":
                round(weight_util, 2),

            "Hold Volume Utilization %":
                round(volume_util, 2)

        })

        remaining_tonnes -= planned_tonnes

    hold_plan_df = pd.DataFrame(hold_rows)


    # ========================================================
    # OUTPUT: SELECTED CARGO / VESSEL
    # ========================================================

    st.subheader("Selected Cargo and Vessel")

    selected_df = pd.DataFrame([{

        "Cargo ID":
            cargo["cargo_id"],

        "Cargo":
            cargo["cargo_name"],

        "Cargo Type":
            cargo["cargo_type"],

        "Cargo Tonnes":
            round(cargo_tonnes, 2),

        "Vessel":
            vessel["vessel_name"],

        "Vessel Type":
            vessel["vessel_type"],

        "Vessel Cargo Capacity":
            vessel_capacity_tonnes,

        "Stowage Factor m³/t":
            stowage_factor

    }])

    st.dataframe(
        selected_df,
        use_container_width=True
    )


    # ========================================================
    # OUTPUT: SUMMARY
    # ========================================================

    st.subheader("Stowage Summary")

    summary_df = pd.DataFrame([{

        "Cargo Volume Required m³":
            round(cargo_volume_m3, 2),

        "Total Hold Volume m³":
            round(total_hold_volume_m3, 2),

        "Usable Hold Volume m³":
            round(usable_hold_volume_m3, 2),

        "Volume Utilization %":
            round(volume_utilization, 2),

        "Total Hold Weight Capacity":
            round(total_hold_weight_capacity, 2),

        "Usable Hold Weight Capacity":
            round(usable_weight_capacity, 2),

        "Hold Weight Utilization %":
            round(hold_weight_utilization, 2),

        "Vessel Weight Utilization %":
            round(vessel_weight_utilization, 2),

        "Operational Margin %":
            operational_margin_percent

    }])

    st.dataframe(
        summary_df,
        use_container_width=True
    )


    # ========================================================
    # OUTPUT: HOLD PLAN
    # ========================================================

    st.subheader("Hold Allocation Plan")

    st.dataframe(
        hold_plan_df,
        use_container_width=True
    )


    # ========================================================
    # WARNINGS / ASSESSMENT
    # ========================================================

    st.subheader("Assessment")

    warnings = []

    if cargo_tonnes > vessel_capacity_with_margin:

        warnings.append(
            "Cargo exceeds vessel cargo capacity after operational margin."
        )

    if cargo_tonnes > usable_weight_capacity:

        warnings.append(
            "Cargo exceeds total hold weight capacity after operational margin."
        )

    if cargo_volume_m3 > usable_hold_volume_m3:

        warnings.append(
            "Cargo volume exceeds usable hold volume after operational margin."
        )

    overloaded_holds = hold_plan_df[
        (
            hold_plan_df["Hold Weight Utilization %"] > 100
        )
        |
        (
            hold_plan_df["Hold Volume Utilization %"] > 100
        )
    ]

    if not overloaded_holds.empty:

        warnings.append(
            "One or more holds exceed weight or volume limits."
        )

    if not warnings:

        st.success(
            "Basic stowage check passed under current assumptions."
        )

    else:

        for warning in warnings:

            st.error(warning)


    # ========================================================
    # PRACTICAL NOTES
    # ========================================================

    st.subheader("Practical Notes")

    st.info(
        """
        This is a simplified stowage model.

        It checks:
        - cargo weight against vessel capacity
        - cargo volume against available hold volume
        - basic equal allocation across holds
        - hold weight and hold volume utilization

        It does not yet calculate:
        - trim
        - stability
        - shear force
        - bending moments
        - dangerous goods segregation
        - loading/discharge sequence
        - cargo compatibility
        """
    )

st.caption(
    "Future enhancements: trim and stability checks, dangerous goods segregation, "
    "load/discharge sequencing, hold-specific restrictions, draft estimate and "
    "integration with fleet optimization."
)