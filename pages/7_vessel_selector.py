

# # pages/7_vessel_selector.py

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

# from economics.vessel_profiles import (
#     load_vessels,
#     get_vessel_profile,
#     calculate_capacity_utilization
# )

# # ============================================================
# # PAGE CONFIG
# # ============================================================

# st.set_page_config(
#     page_title="Vessel Selector",
#     layout="wide"
# )

# st.title(
#     "Vessel Selector"
# )

# st.caption(
#     "Accurate results without lying to ourselves"
# )

# # ============================================================
# # LOAD VESSELS
# # ============================================================

# vessels = load_vessels()

# vessel_names = sorted(
#     vessels["vessel_name"].tolist()
# )

# # ============================================================
# # INPUTS
# # ============================================================

# st.subheader(
#     "Cargo Requirements"
# )

# cargo_tonnes = st.number_input(
#     "Cargo Tonnes",
#     min_value=1000,
#     max_value=500000,
#     value=50000,
#     step=1000
# )


# # ============================================================
# # RECOMMENDED VESSEL CLASS
# # ============================================================

# if cargo_tonnes <= 35000:

#     recommended_type = "Handysize"

# elif cargo_tonnes <= 60000:

#     recommended_type = "Supramax"

# elif cargo_tonnes <= 85000:

#     recommended_type = "Panamax / Kamsarmax"

# elif cargo_tonnes <= 120000:

#     recommended_type = "Post-Panamax"

# elif cargo_tonnes <= 200000:

#     recommended_type = "Capesize"

# else:

#     recommended_type = "VLCC / ULCC"

# st.subheader(
#     "Recommended Vessel Class"
# )

# st.success(
#     f"Recommended vessel class: {recommended_type}"
# )

# selected_vessel = st.selectbox(
#     "Select Vessel",
#     vessel_names
# )

# # ============================================================
# # PROFILE
# # ============================================================

# profile = get_vessel_profile(
#     selected_vessel
# )

# # ============================================================
# # MATCHING VESSELS
# # ============================================================

# matching_vessels = vessels[
#     vessels["cargo_capacity_tonnes"] >= cargo_tonnes
# ].copy()

# matching_vessels = matching_vessels.sort_values(
#     by="cargo_capacity_tonnes"
# )

# st.subheader(
#     "Matching Vessels"
# )

# if matching_vessels.empty:

#     st.error(
#         "No vessel in the fleet can carry this cargo."
#     )

# else:

#     display_cols = [

#         "vessel_name",
#         "vessel_type",
#         "cargo_capacity_tonnes",
#         "dwt",
#         "speed_knots",
#         "fuel_burn_tpd"

#     ]

#     st.dataframe(
#         matching_vessels[
#             display_cols
#         ],
#         use_container_width=True
#     )

# utilization = calculate_capacity_utilization(
#     cargo_tonnes,
#     profile["cargo_capacity_tonnes"]
# )

# # ============================================================
# # VESSEL DETAILS
# # ============================================================

# st.subheader(
#     "Vessel Profile"
# )

# profile_df = pd.DataFrame([{

#     "Vessel":
#         profile["vessel_name"],

#     "Type":
#         profile["vessel_type"],

#     "DWT":
#         profile["dwt"],

#     "Reference Speed":
#         profile["speed_knots"],

#     "Fuel Burn":
#         profile["fuel_burn_tpd"],

#     "Cargo Capacity":
#         profile["cargo_capacity_tonnes"]

# }])

# st.dataframe(
#     profile_df,
#     use_container_width=True
# )

# # ============================================================
# # UTILIZATION
# # ============================================================

# st.subheader(
#     "Cargo Utilization"
# )

# util_df = pd.DataFrame([{

#     "Cargo Tonnes":
#         cargo_tonnes,

#     "Capacity":
#         profile["cargo_capacity_tonnes"],

#     "Utilization %":
#         utilization

# }])

# st.dataframe(
#     util_df,
#     use_container_width=True
# )


# # ============================================================
# # BEST MATCH
# # ============================================================

# best_match = matching_vessels.iloc[0]

# st.subheader(
#     "Best Match"
# )

# st.info(

#     f"{best_match['vessel_name']} "
#     f"({best_match['vessel_type']}) "
#     f"is the smallest vessel capable "
#     f"of carrying this cargo."

# )

# # ============================================================
# # ASSESSMENT
# # ============================================================

# st.subheader(
#     "Assessment"
# )

# if utilization > 100:

#     st.error(
#         "Cargo exceeds vessel capacity."
#     )

# elif utilization > 90:

#     st.success(
#         "Excellent utilization."
#     )

# elif utilization > 70:

#     st.info(
#         "Good utilization."
#     )

# elif utilization > 50:

#     st.warning(
#         "Moderate utilization."
#     )

# else:

#     st.warning(
#         "Low utilization. Consider a smaller vessel."
#     )

# # ============================================================
# # FUTURE
# # ============================================================

# st.caption(
#     "Future enhancements: vessel availability, "
#     "voyage economics integration, fleet optimization, "
#     "stowage planning and draft calculations."
# )















# pages/7_vessel_selector.py

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

from economics.vessel_profiles import (
    load_vessels,
    get_vessel_profile,
    calculate_capacity_utilization
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Vessel Selector",
    layout="wide"
)

st.title("Vessel Selector")

st.caption("Accurate results without lying to ourselves")

# ============================================================
# LOAD VESSELS
# ============================================================

vessels = load_vessels()

# Make sure numeric columns are numeric
numeric_cols = [
    "dwt",
    "speed_knots",
    "fuel_burn_tpd",
    "cargo_capacity_tonnes"
]

for col in numeric_cols:
    vessels[col] = pd.to_numeric(
        vessels[col],
        errors="coerce"
    )

vessels = vessels.dropna(
    subset=numeric_cols
)

vessel_names = sorted(
    vessels["vessel_name"].tolist()
)

# ============================================================
# INPUTS
# ============================================================

st.subheader("Cargo Requirements")

cargo_tonnes = st.number_input(
    "Cargo Tonnes",
    min_value=1000,
    max_value=500000,
    value=50000,
    step=1000
)

# ============================================================
# MATCHING VESSELS
# ============================================================

matching_vessels = vessels[
    vessels["cargo_capacity_tonnes"] >= cargo_tonnes
].copy()

matching_vessels = matching_vessels.sort_values(
    by="cargo_capacity_tonnes",
    ascending=True
)

# ============================================================
# RECOMMENDED VESSEL CLASS
# ============================================================

st.subheader("Recommended Vessel Class")

if matching_vessels.empty:

    best_match = None

    st.error(
        "No vessel in the fleet can carry this cargo."
    )

else:

    best_match = matching_vessels.iloc[0]

    st.success(
        f"Recommended vessel class: {best_match['vessel_type']}"
    )

    st.info(
        f"Best fleet match: {best_match['vessel_name']} "
        f"with capacity {best_match['cargo_capacity_tonnes']:,.0f} tonnes."
    )

# ============================================================
# MATCHING VESSELS TABLE
# ============================================================

st.subheader("Matching Vessels")

if matching_vessels.empty:

    st.warning(
        "No matching vessels available in vessels.csv."
    )

else:

    display_cols = [
        "vessel_name",
        "vessel_type",
        "cargo_capacity_tonnes",
        "dwt",
        "speed_knots",
        "fuel_burn_tpd"
    ]

    st.dataframe(
        matching_vessels[display_cols],
        use_container_width=True
    )

# ============================================================
# SELECT VESSEL
# ============================================================

st.subheader("Manual Vessel Selection")

selected_vessel = st.selectbox(
    "Select Vessel",
    vessel_names
)

profile = get_vessel_profile(
    selected_vessel
)

# Convert profile numeric values safely
profile_capacity = float(profile["cargo_capacity_tonnes"])
profile_dwt = float(profile["dwt"])
profile_speed = float(profile["speed_knots"])
profile_fuel_burn = float(profile["fuel_burn_tpd"])

utilization = calculate_capacity_utilization(
    cargo_tonnes,
    profile_capacity
)

# ============================================================
# SELECTED VESSEL PROFILE
# ============================================================

st.subheader("Selected Vessel Profile")

profile_df = pd.DataFrame([{
    "Vessel": profile["vessel_name"],
    "Type": profile["vessel_type"],
    "DWT": profile_dwt,
    "Reference Speed": profile_speed,
    "Fuel Burn (t/day)": profile_fuel_burn,
    "Cargo Capacity": profile_capacity
}])

st.dataframe(
    profile_df,
    use_container_width=True
)

# ============================================================
# UTILIZATION
# ============================================================

st.subheader("Selected Vessel Cargo Utilization")

util_df = pd.DataFrame([{
    "Cargo Tonnes": cargo_tonnes,
    "Selected Vessel Capacity": profile_capacity,
    "Utilization %": utilization
}])

st.dataframe(
    util_df,
    use_container_width=True
)

# ============================================================
# BEST MATCH
# ============================================================

if best_match is not None:

    st.subheader("Best Match From Fleet")

    st.info(
        f"{best_match['vessel_name']} "
        f"({best_match['vessel_type']}) "
        f"is the smallest vessel in your CSV capable of carrying "
        f"{cargo_tonnes:,.0f} tonnes."
    )

# ============================================================
# ASSESSMENT
# ============================================================

st.subheader("Selected Vessel Assessment")

if utilization > 100:

    st.error(
        "Selected vessel cannot carry this cargo."
    )

elif utilization > 95:

    st.success(
        "Excellent utilization, but check operational margin."
    )

elif utilization > 80:

    st.success(
        "Very efficient utilization."
    )

elif utilization > 65:

    st.info(
        "Good utilization."
    )

elif utilization > 50:

    st.warning(
        "Moderate utilization."
    )

else:

    st.warning(
        "Low utilization. Consider a smaller vessel."
    )

# ============================================================
# FUTURE
# ============================================================

st.caption(
    "Future enhancements: vessel availability, voyage economics integration, "
    "fleet optimization, stowage planning, draft calculations, demurrage "
    "and dispatch modelling."
)