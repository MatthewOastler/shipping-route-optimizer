

# pages/12_port_congestion.py

import streamlit as st
import pandas as pd

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Port Congestion",
    layout="wide"
)

st.title("Port Congestion Engine")


# ============================================================
# LOAD DATA
# ============================================================

CONGESTION_FILE = "data/port_congestion.csv"

ports = pd.read_csv(
    CONGESTION_FILE
)

# ============================================================
# VIEW DATA
# ============================================================

st.subheader(
    "Current Port Congestion Dataset"
)

st.dataframe(
    ports,
    use_container_width=True
)

# ============================================================
# PORT SELECTION
# ============================================================

st.subheader(
    "Port Analysis"
)

selected_port = st.selectbox(
    "Select Port",
    sorted(
        ports["port"].unique()
    )
)

port_row = ports[
    ports["port"] == selected_port
].iloc[0]

# ============================================================
# PORT SUMMARY
# ============================================================

st.subheader(
    "Port Summary"
)

summary_df = pd.DataFrame([{

    "Port":
        port_row["port"],

    "Congestion Level":
        port_row["congestion_level"],

    "Delay Days":
        port_row["delay_days"],

    "Berth Utilization %":
        port_row["berth_utilization_pct"],

    "Waiting Risk Score":
        port_row["waiting_risk_score"]

}])

st.dataframe(
    summary_df,
    use_container_width=True
)

# ============================================================
# VOYAGE IMPACT
# ============================================================

st.subheader(
    "Voyage Impact Estimator"
)

col1, col2 = st.columns(2)

with col1:

    sea_days = st.number_input(
        "Sea Days",
        min_value=0.1,
        value=20.0,
        step=0.5
    )

with col2:

    base_tce = st.number_input(
        "Base TCE ($/day)",
        min_value=0.0,
        value=20000.0,
        step=1000.0
    )

total_days = (
    sea_days
    +
    float(port_row["delay_days"])
)

adjusted_tce = (
    base_tce
    *
    sea_days
    /
    total_days
)

# ============================================================
# RESULTS
# ============================================================

st.subheader(
    "Congestion Impact"
)

impact_df = pd.DataFrame([{

    "Sea Days":
        round(sea_days, 2),

    "Congestion Days":
        round(
            port_row["delay_days"],
            2
        ),

    "Total Voyage Days":
        round(
            total_days,
            2
        ),

    "Base TCE":
        round(
            base_tce,
            2
        ),

    "Adjusted TCE":
        round(
            adjusted_tce,
            2
        )

}])

st.dataframe(
    impact_df,
    use_container_width=True
)

# ============================================================
# INTERPRETATION
# ============================================================

st.subheader(
    "Commercial Interpretation"
)

if port_row["congestion_level"] == "Low":

    st.success(
        "Low congestion. Minimal operational impact."
    )

elif port_row["congestion_level"] == "Medium":

    st.warning(
        "Moderate congestion. Voyage delays possible."
    )

else:

    st.error(
        "High congestion. Significant delay risk."
    )

st.info(

    f"Estimated waiting delay at "
    f"{selected_port}: "
    f"{port_row['delay_days']} days"

)

st.info(

    f"Estimated adjusted TCE: "
    f"${adjusted_tce:,.0f}/day"

)

# ============================================================
# RANKINGS
# ============================================================

st.subheader(
    "Least Congested Ports"
)

least_congested = ports.sort_values(
    by="delay_days"
).head(5)

st.dataframe(
    least_congested,
    use_container_width=True
)

st.subheader(
    "Most Congested Ports"
)

most_congested = ports.sort_values(
    by="delay_days",
    ascending=False
).head(5)

st.dataframe(
    most_congested,
    use_container_width=True
)

# ============================================================
# FUTURE
# ============================================================

st.caption(
    "Future enhancements: live AIS congestion feeds, "
    "port productivity metrics, weather impacts, "
    "seasonal congestion forecasting and automatic "
    "integration with Voyage Economics."
)