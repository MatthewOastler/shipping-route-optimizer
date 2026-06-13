# pages/15_market_freight_engine.py

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


st.set_page_config(
    page_title="Market Freight Engine",
    layout="wide"
)

st.title("Market Freight Engine")

# ============================================================
# LOAD DATA
# ============================================================

CARGOES_FILE = "data/cargoes.csv"
VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"
CONGESTION_FILE = "data/port_congestion.csv"

cargoes = pd.read_csv(CARGOES_FILE)
vessels = load_vessels(VESSELS_FILE)
positions = pd.read_csv(POSITIONS_FILE)
congestion = pd.read_csv(CONGESTION_FILE)

fleet = vessels.merge(
    positions,
    on="vessel_name",
    how="left"
)


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

fleet["cargo_capacity_tonnes"] = pd.to_numeric(
    fleet["cargo_capacity_tonnes"],
    errors="coerce"
)

fleet["available_days"] = pd.to_numeric(
    fleet["available_days"],
    errors="coerce"
)

congestion["delay_days"] = pd.to_numeric(
    congestion["delay_days"],
    errors="coerce"
)

cargoes = cargoes.dropna(
    subset=[
        "cargo_name",
        "cargo_type",
        "load_port",
        "discharge_port",
        "cargo_tonnes",
        "freight_rate"
    ]
)

fleet = fleet.dropna(
    subset=[
        "vessel_name",
        "cargo_capacity_tonnes",
        "available_days"
    ]
)


# ============================================================
# INPUTS
# ============================================================

st.subheader("Cargo Market")

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

col1, col2, col3 = st.columns(3)

with col1:
    urgency_level = st.selectbox(
        "Cargo Urgency",
        [
            "Low",
            "Normal",
            "High",
            "Very High"
        ],
        index=1
    )

with col2:
    market_sentiment = st.selectbox(
        "Market Sentiment",
        [
            "Weak",
            "Balanced",
            "Firm",
            "Hot"
        ],
        index=1
    )

with col3:
    manual_adjustment = st.number_input(
        "Manual Premium Adjustment (%)",
        min_value=-50.0,
        max_value=100.0,
        value=0.0,
        step=1.0
    )


# ============================================================
# MARKET LOGIC
# ============================================================

if st.button("Calculate Suggested Freight Rate"):

    capable_vessels = fleet[
        fleet["cargo_capacity_tonnes"] >= cargo["cargo_tonnes"]
    ].copy()

    available_now = capable_vessels[
        capable_vessels["available_days"] <= 2
    ]

    vessel_scarcity_score = 0

    if len(capable_vessels) == 0:
        vessel_scarcity_score = 30

    elif len(available_now) == 0:
        vessel_scarcity_score = 20

    elif len(available_now) <= 2:
        vessel_scarcity_score = 10

    else:
        vessel_scarcity_score = 0

    urgency_score = {
        "Low": -5,
        "Normal": 0,
        "High": 10,
        "Very High": 20
    }[urgency_level]

    sentiment_score = {
        "Weak": -10,
        "Balanced": 0,
        "Firm": 10,
        "Hot": 20
    }[market_sentiment]

    load_congestion = congestion[
        congestion["port"] == cargo["load_port"]
    ]

    discharge_congestion = congestion[
        congestion["port"] == cargo["discharge_port"]
    ]

    congestion_days = (
        (
            float(load_congestion.iloc[0]["delay_days"])
            if not load_congestion.empty
            else 0
        )
        +
        (
            float(discharge_congestion.iloc[0]["delay_days"])
            if not discharge_congestion.empty
            else 0
        )
    )

    congestion_score = min(
        congestion_days * 3,
        20
    )

    suggested_premium_percent = (
        vessel_scarcity_score
        +
        urgency_score
        +
        sentiment_score
        +
        congestion_score
        +
        manual_adjustment
    )

    suggested_premium_percent = max(
        -30,
        suggested_premium_percent
    )

    base_rate = float(cargo["freight_rate"])

    suggested_rate = (
        base_rate
        *
        (
            1
            +
            suggested_premium_percent / 100
        )
    )

    revenue_base = (
        cargo["cargo_tonnes"]
        *
        base_rate
    )

    revenue_suggested = (
        cargo["cargo_tonnes"]
        *
        suggested_rate
    )

    st.subheader("Market Pricing Result")

    result_df = pd.DataFrame([{
        "Cargo": cargo["cargo_name"],
        "Cargo Type": cargo["cargo_type"],
        "Route": f"{cargo['load_port']} → {cargo['discharge_port']}",
        "Cargo Tonnes": cargo["cargo_tonnes"],
        "Base Freight Rate ($/t)": round(base_rate, 2),
        "Suggested Premium %": round(suggested_premium_percent, 2),
        "Suggested Freight Rate ($/t)": round(suggested_rate, 2),
        "Base Revenue ($)": round(revenue_base, 2),
        "Suggested Revenue ($)": round(revenue_suggested, 2),
        "Revenue Difference ($)": round(revenue_suggested - revenue_base, 2),
        "Capable Vessels": len(capable_vessels),
        "Available Now/ Soon": len(available_now),
        "Congestion Days": round(congestion_days, 2)
    }])

    st.dataframe(
        result_df,
        use_container_width=True
    )

    st.subheader("Pricing Explanation")

    explanation_df = pd.DataFrame([
        {
            "Driver": "Vessel Scarcity",
            "Score %": vessel_scarcity_score
        },
        {
            "Driver": "Cargo Urgency",
            "Score %": urgency_score
        },
        {
            "Driver": "Market Sentiment",
            "Score %": sentiment_score
        },
        {
            "Driver": "Port Congestion",
            "Score %": round(congestion_score, 2)
        },
        {
            "Driver": "Manual Adjustment",
            "Score %": manual_adjustment
        }
    ])

    st.dataframe(
        explanation_df,
        use_container_width=True
    )

    if suggested_premium_percent > 15:
        st.success("Market pricing recommendation: charge a strong premium.")

    elif suggested_premium_percent > 0:
        st.info("Market pricing recommendation: moderate premium justified.")

    elif suggested_premium_percent == 0:
        st.info("Market pricing recommendation: base rate appears reasonable.")

    else:
        st.warning("Market pricing recommendation: discount may be required.")

st.caption(
    "This is a transparent rule-based market pricing model. Future upgrades should connect "
    "real freight indexes, bunker prices, vessel supply, port congestion and cargo urgency."
)