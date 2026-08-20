




# pages/19_historical_validation.py

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
import numpy as np

from economics.speed_fuel_model import estimate_fuel_burn_at_speed
from optimizer.dijkstra import build_graph, shortest_path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Historical Validation",
    layout="wide"
)

st.title("Historical Voyage Validation")
st.caption("Real published voyage data only — unavailable outcomes remain blank.")


# ============================================================
# FILES
# ============================================================

HISTORICAL_FILE = "data/historical_voyages.csv"
ROUTES_FILE = "data/generated_routes.csv"


# ============================================================
# HELPERS
# ============================================================

def pct_error(predicted, actual):
    if pd.isna(actual) or float(actual) == 0:
        return np.nan
    return ((float(predicted) - float(actual)) / float(actual)) * 100.0


def abs_pct_error(predicted, actual):
    value = pct_error(predicted, actual)
    return abs(value) if not pd.isna(value) else np.nan


def route_distance(graph, path):
    return sum(
        float(graph[path[i]][path[i + 1]]["distance"])
        for i in range(len(path) - 1)
    )


# ============================================================
# LOAD DATA
# ============================================================

historical = pd.read_csv(HISTORICAL_FILE)

for col in [
    "dwt",
    "reported_distance_nm",
    "reported_speed_knots",
    "calendar_elapsed_days",
    "implied_sea_days_from_reported_distance_speed",
    "reported_cargo_tonnes",
    "reported_pair_hfo_tonnes",
    "reported_pair_do_tonnes",
    "reported_pair_total_fuel_tonnes",
    "reported_pair_distance_nm",
]:
    if col in historical.columns:
        historical[col] = pd.to_numeric(
            historical[col],
            errors="coerce"
        )

historical["departure_date"] = pd.to_datetime(
    historical["departure_date"],
    errors="coerce"
)

historical["arrival_date"] = pd.to_datetime(
    historical["arrival_date"],
    errors="coerce"
)


# ============================================================
# SOURCE / DATASET SUMMARY
# ============================================================

st.subheader("Historical Dataset")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Published Voyage Legs", len(historical))
c2.metric("Vessels", historical["vessel_name"].nunique())
c3.metric("Ballast Legs", int((historical["condition"] == "Ballast").sum()))
c4.metric("Cargo Legs", int((historical["condition"] == "Cargo").sum()))

st.dataframe(
    historical,
    use_container_width=True
)

st.info(
    """
    The primary dataset consists of published operational records for M/V NSU JUSTICE,
    a 250,000 DWT bulk carrier. The route table reports actual voyage-leg dates, ports,
    distances and speeds. A second published table reports aggregate HFO, diesel oil,
    distance and cargo for voyage pairs 16–20.

    No freight rate, port cost, voyage profit or TCE has been invented. Those columns
    are intentionally blank because the cited publications do not report them.
    """
)


# ============================================================
# 1. OBSERVED VOYAGE CONSISTENCY
# ============================================================

st.subheader("1. Published Voyage Consistency")

consistency = historical.copy()

consistency["Calculated Sea Days"] = (
    consistency["reported_distance_nm"]
    /
    consistency["reported_speed_knots"]
    /
    24
)

consistency["Calendar Days"] = (
    consistency["arrival_date"]
    -
    consistency["departure_date"]
).dt.total_seconds() / 86400

consistency["Calendar Minus Calculated Sea Days"] = (
    consistency["Calendar Days"]
    -
    consistency["Calculated Sea Days"]
)

consistency["Distance Reconciliation Difference NM"] = (
    consistency["reported_distance_nm"]
    -
    (
        consistency["reported_speed_knots"]
        *
        consistency["Calculated Sea Days"]
        *
        24
    )
)

display_cols = [
    "record_id",
    "voyage_leg",
    "condition",
    "origin_port",
    "destination_port",
    "reported_distance_nm",
    "reported_speed_knots",
    "Calculated Sea Days",
    "Calendar Days",
    "Calendar Minus Calculated Sea Days",
]

st.dataframe(
    consistency[display_cols],
    use_container_width=True
)

st.caption(
    "Calendar time is not treated as pure steaming time. Positive differences can include "
    "waiting, operational delays, anchorage, manoeuvring and other non-steaming time."
)


# ============================================================
# 2. SPEED / FUEL MODEL VS PUBLISHED ACTUAL FUEL
# ============================================================

st.subheader("2. Speed/Fuel Model vs Published Actual Fuel")

st.write(
    "This comparison uses the current cubic speed/fuel model against the five published "
    "voyage-pair fuel totals. The reference speed and burn are deliberately editable."
)

col1, col2, col3 = st.columns(3)

with col1:
    reference_speed = st.number_input(
        "Reference Speed (knots)",
        min_value=5.0,
        max_value=25.0,
        value=12.5,
        step=0.1
    )

with col2:
    reference_fuel_burn = st.number_input(
        "Reference Fuel Burn (t/day)",
        min_value=1.0,
        max_value=200.0,
        value=61.9,
        step=0.5
    )

with col3:
    exponent = st.number_input(
        "Fuel Curve Exponent",
        min_value=2.0,
        max_value=4.0,
        value=3.0,
        step=0.1
    )

st.caption(
    "Defaults are a broad >200,000 DWT bulk-carrier benchmark, not a calibrated "
    "NSU JUSTICE performance curve. Change these assumptions rather than fitting them "
    "to the validation results."
)

pair_rows = []

fuel_actual_rows = historical[
    historical["reported_pair_total_fuel_tonnes"].notna()
].copy()

for _, pair_row in fuel_actual_rows.iterrows():

    group = str(int(pair_row["voyage_group"])) if not pd.isna(pair_row["voyage_group"]) else str(pair_row["voyage_group"])

    group_legs = historical[
        historical["voyage_group"].astype(str).str.replace(".0", "", regex=False)
        ==
        group
    ].copy()

    predicted_pair_fuel = 0.0

    for _, leg in group_legs.iterrows():

        burn_at_speed = estimate_fuel_burn_at_speed(
            speed_knots=leg["reported_speed_knots"],
            base_speed_knots=reference_speed,
            base_fuel_burn_tpd=reference_fuel_burn,
            exponent=exponent
        )

        sailing_days = (
            leg["reported_distance_nm"]
            /
            leg["reported_speed_knots"]
            /
            24
        )

        predicted_pair_fuel += (
            burn_at_speed
            *
            sailing_days
        )

    actual_fuel = float(
        pair_row["reported_pair_total_fuel_tonnes"]
    )

    pair_rows.append({
        "Voyage Pair": group,
        "Actual HFO (t)": pair_row["reported_pair_hfo_tonnes"],
        "Actual DO (t)": pair_row["reported_pair_do_tonnes"],
        "Actual Total Fuel (t)": actual_fuel,
        "Model Sailing Fuel (t)": round(predicted_pair_fuel, 2),
        "Error (t)": round(predicted_pair_fuel - actual_fuel, 2),
        "Error %": round(pct_error(predicted_pair_fuel, actual_fuel), 2),
        "Absolute Error %": round(abs_pct_error(predicted_pair_fuel, actual_fuel), 2),
        "Published Pair Distance NM": pair_row["reported_pair_distance_nm"],
        "Published Cargo Tonnes": pair_row["reported_cargo_tonnes"],
    })

pair_df = pd.DataFrame(pair_rows)

if not pair_df.empty:

    st.dataframe(
        pair_df,
        use_container_width=True
    )

    mae = (
        pair_df["Model Sailing Fuel (t)"]
        -
        pair_df["Actual Total Fuel (t)"]
    ).abs().mean()

    mape = pair_df["Absolute Error %"].mean()
    bias = pair_df["Error %"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Fuel MAE (t)", f"{mae:,.1f}")
    c2.metric("Fuel MAPE", f"{mape:,.1f}%")
    c3.metric("Mean Bias", f"{bias:,.1f}%")

    st.warning(
        "Interpret this carefully: published actual fuel is for the entire A+B voyage pair "
        "and includes HFO + diesel oil. The model estimate above is sailing fuel based on a "
        "generic speed/fuel curve. This is useful as a benchmark challenge, but is not yet "
        "an apples-to-apples calibrated vessel model."
    )

else:
    st.warning("No published pair-level fuel observations are available.")


# ============================================================
# 3. ROUTE ENGINE HISTORICAL VALIDATION
# ============================================================

st.subheader("3. Route Engine vs Historical Sailed Distance")

st.write(
    """
    This is the strongest route test: compare the optimizer's route distance with the
    independently published sailed distance.

    Historical records include `model_origin_port` and `model_destination_port` fields.
    They are intentionally blank until the corresponding ports are added and verified in
    your own `global_ports.csv` / `generated_routes.csv`.
    """
)

try:
    routes = pd.read_csv(ROUTES_FILE)
    graph = build_graph(routes)

    mapped = historical[
        historical["model_origin_port"].notna()
        &
        historical["model_destination_port"].notna()
        &
        (historical["model_origin_port"].astype(str).str.strip() != "")
        &
        (historical["model_destination_port"].astype(str).str.strip() != "")
    ].copy()

    route_results = []

    for _, row in mapped.iterrows():

        start = str(row["model_origin_port"]).strip()
        end = str(row["model_destination_port"]).strip()

        try:
            path, route_cost = shortest_path(
                graph,
                start,
                end
            )

            predicted_distance = route_distance(
                graph,
                path
            )

            actual_distance = float(
                row["reported_distance_nm"]
            )

            route_results.append({
                "Record": row["record_id"],
                "Historical Route": f"{row['origin_port']} → {row['destination_port']}",
                "Model Route": " → ".join(path),
                "Published Distance NM": actual_distance,
                "Model Distance NM": round(predicted_distance, 2),
                "Error NM": round(predicted_distance - actual_distance, 2),
                "Error %": round(pct_error(predicted_distance, actual_distance), 2),
                "Absolute Error %": round(abs_pct_error(predicted_distance, actual_distance), 2),
            })

        except Exception as err:
            route_results.append({
                "Record": row["record_id"],
                "Historical Route": f"{row['origin_port']} → {row['destination_port']}",
                "Model Route": "FAILED",
                "Published Distance NM": row["reported_distance_nm"],
                "Model Distance NM": np.nan,
                "Error NM": np.nan,
                "Error %": np.nan,
                "Absolute Error %": np.nan,
                "Error": str(err)
            })

    route_df = pd.DataFrame(route_results)

    if route_df.empty:

        st.info(
            "Route-engine historical validation is PENDING. "
            "No historical source ports have yet been mapped to verified nodes in your route network."
        )

    else:

        st.dataframe(
            route_df,
            use_container_width=True
        )

        valid_route_results = route_df[
            route_df["Absolute Error %"].notna()
        ]

        if not valid_route_results.empty:

            route_mape = valid_route_results[
                "Absolute Error %"
            ].mean()

            st.metric(
                "Historical Route Distance MAPE",
                f"{route_mape:,.2f}%"
            )

except Exception as err:
    st.error(f"Unable to test route engine: {err}")


# ============================================================
# 4. WHAT IS / IS NOT VALIDATED
# ============================================================

st.subheader("4. Validation Coverage")

coverage = pd.DataFrame([
    {
        "Model Component": "Historical voyage dates / ports / distance / speed",
        "Status": "OBSERVED / PUBLISHED",
        "Reason": "Directly transcribed from open-access published operational data."
    },
    {
        "Model Component": "Fuel benchmark for voyage pairs 16–20",
        "Status": "OBSERVED / PUBLISHED",
        "Reason": "Published HFO + diesel oil totals from actual noon-log based voyages."
    },
    {
        "Model Component": "Speed/fuel model",
        "Status": "BENCHMARKED, NOT CALIBRATED",
        "Reason": "Can now be compared against actual fuel, but generic curve parameters are not vessel-specific."
    },
    {
        "Model Component": "Route distance engine",
        "Status": "PENDING PORT MAPPING",
        "Reason": "Historical ports must first be added and independently verified in your route network."
    },
    {
        "Model Component": "Freight rate / revenue",
        "Status": "NOT VALIDATED",
        "Reason": "The source does not report historical fixture rates."
    },
    {
        "Model Component": "Port costs",
        "Status": "NOT VALIDATED",
        "Reason": "The source does not report actual port charges."
    },
    {
        "Model Component": "Voyage profit / TCE",
        "Status": "NOT VALIDATED",
        "Reason": "Cannot be reconstructed accurately without historical commercial inputs."
    },
])

st.dataframe(
    coverage,
    use_container_width=True
)

st.success(
    "The historical file deliberately contains blanks instead of invented values. "
    "That is the correct behaviour for validation data."
)

st.markdown("---")

st.info(
    """
    Next recommended validation step:
    add the historical ports (Nagoya, Kisarazu, Muroran, Tobata, Port Walcott and
    Ponta da Madeira) to a verified port dataset, regenerate the route network, and
    then compare optimizer distance directly with these 22 published sailed distances.

    After that, add additional independent historical vessels rather than repeatedly
    tuning the model to NSU JUSTICE.
    """
)