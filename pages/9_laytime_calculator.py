

# pages/9_laytime_calculator.py

import streamlit as st
import pandas as pd

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Laytime Calculator",
    layout="wide"
)

st.title("Laytime Calculator")

st.caption("Accurate results without lying to ourselves")

# ============================================================
# INPUTS
# ============================================================

st.subheader("Laytime Inputs")

col1, col2 = st.columns(2)

with col1:
    allowed_laytime_days = st.number_input(
        "Allowed Laytime (days)",
        min_value=0.0,
        value=3.0,
        step=0.5
    )

with col2:
    actual_laytime_days = st.number_input(
        "Actual Laytime Used (days)",
        min_value=0.0,
        value=3.0,
        step=0.5
    )

st.subheader("Rates")

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

st.subheader("Voyage Economics Adjustment")

col1, col2 = st.columns(2)

with col1:
    base_voyage_profit = st.number_input(
        "Base Voyage Profit ($)",
        value=0.0,
        step=10000.0
    )

with col2:
    total_voyage_days = st.number_input(
        "Total Voyage Days",
        min_value=0.1,
        value=20.0,
        step=0.5
    )

# ============================================================
# CALCULATE
# ============================================================

if st.button("Calculate Laytime Result"):

    laytime_difference = actual_laytime_days - allowed_laytime_days

    demurrage_cost = 0.0
    dispatch_credit = 0.0
    status = "On Time"

    if laytime_difference > 0:
        status = "Demurrage"
        demurrage_cost = laytime_difference * demurrage_rate

    elif laytime_difference < 0:
        status = "Dispatch"
        dispatch_credit = abs(laytime_difference) * dispatch_rate

    adjusted_profit = (
        base_voyage_profit
        - demurrage_cost
        + dispatch_credit
    )

    adjusted_tce = (
        adjusted_profit
        / total_voyage_days
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader("Laytime Summary")

    summary = pd.DataFrame([{
        "Allowed Laytime Days": allowed_laytime_days,
        "Actual Laytime Days": actual_laytime_days,
        "Difference Days": round(laytime_difference, 2),
        "Status": status,
        "Demurrage Cost ($)": round(demurrage_cost, 2),
        "Dispatch Credit ($)": round(dispatch_credit, 2),
        "Base Voyage Profit ($)": round(base_voyage_profit, 2),
        "Adjusted Voyage Profit ($)": round(adjusted_profit, 2),
        "Adjusted TCE ($/day)": round(adjusted_tce, 2)
    }])

    st.dataframe(
        summary,
        use_container_width=True
    )

    # ========================================================
    # INTERPRETATION
    # ========================================================

    st.subheader("Commercial Interpretation")

    if status == "Demurrage":
        st.error(
            f"Demurrage applies. Extra time used: "
            f"{laytime_difference:.2f} days. "
            f"Cost = ${demurrage_cost:,.0f}."
        )

    elif status == "Dispatch":
        st.success(
            f"Dispatch applies. Time saved: "
            f"{abs(laytime_difference):.2f} days. "
            f"Credit = ${dispatch_credit:,.0f}."
        )

    else:
        st.info(
            "No demurrage or dispatch applies. "
            "Actual laytime equals allowed laytime."
        )

    st.info(
        f"Adjusted Voyage Profit = ${adjusted_profit:,.0f}"
    )

    st.info(
        f"Adjusted TCE = ${adjusted_tce:,.0f}/day"
    )

# ============================================================
# NOTES
# ============================================================

st.markdown("---")

st.info(
    """
    Demurrage applies when loading or discharge takes longer than the allowed laytime.

    Dispatch applies when loading or discharge finishes faster than the allowed laytime.

    This page currently models laytime as a simple single-port or combined-port calculation.

    Future improvements:
    - separate load-port and discharge-port laytime
    - weather working days
    - notice of readiness
    - reversible laytime
    - demurrage once on demurrage always on demurrage
    - integration with Voyage Economics page
    """
)