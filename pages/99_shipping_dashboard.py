



# pages/99_shipping_dashboard.py

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
from economics.voyage_economics import calculate_voyage_economics
from economics.speed_fuel_model import estimate_fuel_burn_at_speed


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Shipping Dashboard",
    layout="wide"
)

st.title("Shipping Master Dashboard")



# ============================================================
# LOAD DATA
# ============================================================

ROUTES_FILE = "data/generated_routes.csv"
VESSELS_FILE = "data/vessels.csv"
POSITIONS_FILE = "data/vessel_positions.csv"
CARGOES_FILE = "data/cargoes.csv"
CONGESTION_FILE = "data/port_congestion.csv"
STOWAGE_FILE = "data/cargo_stowage_factors.csv"
OPERATING_COSTS_FILE = "data/vessel_operating_costs.csv"


routes = pd.read_csv(ROUTES_FILE)
vessels = load_vessels(VESSELS_FILE)


positions = pd.read_csv(POSITIONS_FILE)
cargoes = pd.read_csv(CARGOES_FILE)
congestion = pd.read_csv(CONGESTION_FILE)
stowage_factors = pd.read_csv(STOWAGE_FILE)
opex = pd.read_csv(OPERATING_COSTS_FILE)

graph = build_graph(routes)

fleet = vessels.merge(
    positions,
    on="vessel_name",
    how="left"
)


fleet = fleet.merge(
    opex,
    on="vessel_type",
    how="left"
)


# ============================================================
# CLEAN DATA
# ============================================================


for col in [
    "cargo_capacity_tonnes",
    "speed_knots",
    "fuel_burn_tpd",
    "available_days",
    "daily_hire_cost",
    "crew_cost_per_day",
    "insurance_cost_per_day",
    "maintenance_cost_per_day",
    "technical_management_cost_per_day",
    "stores_cost_per_day",
    "admin_overhead_cost_per_day",
    "total_opex_per_day"
]:



    fleet[col] = pd.to_numeric(
        fleet[col],
        errors="coerce"
    )

for col in [
    "cargo_tonnes",
    "freight_rate"
]:
    cargoes[col] = pd.to_numeric(
        cargoes[col],
        errors="coerce"
    )

for col in [
    "delay_days",
    "berth_utilization_pct",
    "waiting_risk_score"
]:
    congestion[col] = pd.to_numeric(
        congestion[col],
        errors="coerce"
    )

stowage_factors["stowage_factor_m3_per_tonne"] = pd.to_numeric(
    stowage_factors["stowage_factor_m3_per_tonne"],
    errors="coerce"
)

fleet = fleet.dropna(
    subset=[
        "vessel_name",
        "vessel_type",
        "cargo_capacity_tonnes",
        "speed_knots",
        "fuel_burn_tpd",
        "current_port",
        "available_days",
        "daily_hire_cost"
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
# HELPER FUNCTIONS
# ============================================================

def get_route_distance_and_risk(path, graph):
    total_distance = 0.0
    fuel_component = 0.0
    canal_component = 0.0
    weather_component = 0.0
    piracy_component = 0.0
    carbon_component = 0.0

    rows = []

    for i in range(len(path) - 1):

        origin = path[i]
        destination = path[i + 1]
        edge = graph[origin][destination]

        distance = float(edge.get("distance", 0))
        fuel = float(edge.get("fuel_cost", 0))
        canal = float(edge.get("canal_fee", 0))
        weather = float(edge.get("weather_risk", 0))
        piracy = float(edge.get("piracy_risk", 0))
        carbon = float(edge.get("carbon_cost", 0))

        total_distance += distance
        fuel_component += fuel
        canal_component += canal
        weather_component += weather
        piracy_component += piracy
        carbon_component += carbon

        rows.append({
            "From": origin,
            "To": destination,
            "Distance NM": round(distance, 2),
            "Fuel Cost": round(fuel, 2),
            "Canal Fee": round(canal, 2),
            "Weather Risk": round(weather, 2),
            "Piracy Risk": round(piracy, 2),
            "Carbon Cost": round(carbon, 2),
            "Leg Total": round(fuel + canal + weather + piracy + carbon, 2)
        })

    return {
        "distance_nm": total_distance,
        "fuel_component": fuel_component,
        "canal_component": canal_component,
        "weather_component": weather_component,
        "piracy_component": piracy_component,
        "carbon_component": carbon_component,
        "rows": rows
    }


def get_congestion_days(port_code, congestion_df):
    row = congestion_df[
        congestion_df["port"] == port_code
    ]

    if row.empty:
        return 0.0, "Unknown", 0.0, 0.0

    return (
        float(row.iloc[0]["delay_days"]),
        row.iloc[0]["congestion_level"],
        float(row.iloc[0]["berth_utilization_pct"]),
        float(row.iloc[0]["waiting_risk_score"])
    )


def get_stowage_factor(cargo_name, stowage_df):
    row = stowage_df[
        stowage_df["cargo_name"] == cargo_name
    ]

    if row.empty:
        return 1.0, "No stowage factor found. Default used."

    return (
        float(row.iloc[0]["stowage_factor_m3_per_tonne"]),
        str(row.iloc[0].get("notes", ""))
    )


def laytime_result(
    allowed_load,
    actual_load,
    allowed_discharge,
    actual_discharge,
    demurrage_rate,
    dispatch_rate
):
    total_diff = (
        actual_load
        -
        allowed_load
        +
        actual_discharge
        -
        allowed_discharge
    )

    demurrage_cost = 0.0
    dispatch_credit = 0.0
    status = "On Time"

    if total_diff > 0:
        status = "Demurrage"
        demurrage_cost = total_diff * demurrage_rate

    elif total_diff < 0:
        status = "Dispatch"
        dispatch_credit = abs(total_diff) * dispatch_rate

    return status, total_diff, demurrage_cost, dispatch_credit


def evaluate_candidate(
    vessel,
    cargo,
    graph,
    congestion_df,
    fuel_price,
    load_port_cost,
    discharge_port_cost,
    transit_fee_per_port,
    freight_premium_percent,
    route_cost_multiplier,
    allowed_load_laytime,
    actual_load_laytime,
    allowed_discharge_laytime,
    actual_discharge_laytime,
    demurrage_rate,
    dispatch_rate,
    selected_speed,
    selected_fuel_burn
):
    load_port = cargo["load_port"]
    discharge_port = cargo["discharge_port"]

    positioning_path, positioning_route_cost = shortest_path(
        graph,
        vessel["current_port"],
        load_port
    )

    voyage_path, voyage_route_cost = shortest_path(
        graph,
        load_port,
        discharge_port
    )

    positioning_data = get_route_distance_and_risk(
        positioning_path,
        graph
    )

    voyage_data = get_route_distance_and_risk(
        voyage_path,
        graph
    )

    positioning_days = (
        positioning_data["distance_nm"]
        /
        selected_speed
        /
        24
    )

    earliest_ready_days = (
        float(vessel["available_days"])
        +
        positioning_days
    )

    positioning_hire_cost = (
        earliest_ready_days
        *
        float(vessel["daily_hire_cost"])
    )

    load_delay, load_cong_level, load_berth, load_risk = get_congestion_days(
        load_port,
        congestion_df
    )

    discharge_delay, discharge_cong_level, discharge_berth, discharge_risk = get_congestion_days(
        discharge_port,
        congestion_df
    )

    congestion_days = load_delay + discharge_delay

    transit_port_count = max(
        0,
        len(voyage_path) - 2
    )

    allowed_port_days = (
        allowed_load_laytime
        +
        allowed_discharge_laytime
    )

    economics = calculate_voyage_economics(
        distance_nm=voyage_data["distance_nm"],
        route_cost=voyage_route_cost,
        cargo_tonnes=cargo["cargo_tonnes"],
        freight_rate=cargo["freight_rate"],
        vessel_speed_knots=selected_speed,
        fuel_burn_tonnes_per_day=selected_fuel_burn,
        fuel_price=fuel_price,
        load_port_cost=load_port_cost,
        discharge_port_cost=discharge_port_cost,
        freight_premium_percent=freight_premium_percent,
        ballast_days=earliest_ready_days,
        waiting_days=congestion_days,
        port_days=allowed_port_days,
        transit_port_count=transit_port_count,
        transit_fee_per_port=transit_fee_per_port,
        route_cost_multiplier=route_cost_multiplier
    )

    lay_status, lay_diff, demurrage_cost, dispatch_credit = laytime_result(
        allowed_load_laytime,
        actual_load_laytime,
        allowed_discharge_laytime,
        actual_discharge_laytime,
        demurrage_rate,
        dispatch_rate
    )

    hire_cost = (
        economics["total_voyage_days"]
        *
        float(vessel["daily_hire_cost"])
    )
    
    opex_cost = (
        economics["total_voyage_days"]
        *
        float(vessel["total_opex_per_day"])
    )
        
    
    



    net_profit = (
        economics["voyage_profit"]
        -
        hire_cost
        -
        opex_cost
        -
        demurrage_cost
        +
        dispatch_credit
    )
        
        
    net_tce = (
        net_profit
        /
        economics["total_voyage_days"]
        if economics["total_voyage_days"] > 0
        else 0
    )
        
     
    
    
    utilization = (
        cargo["cargo_tonnes"]
        /
        vessel["cargo_capacity_tonnes"]
        *
        100
    )

    return {
        "vessel": vessel,
        "positioning_path": positioning_path,
        "voyage_path": voyage_path,
        "positioning_data": positioning_data,
        "voyage_data": voyage_data,
        "positioning_days": positioning_days,
        "earliest_ready_days": earliest_ready_days,
        "positioning_hire_cost": positioning_hire_cost,
        "load_congestion_level": load_cong_level,
        "discharge_congestion_level": discharge_cong_level,
        "congestion_days": congestion_days,
        "transit_port_count": transit_port_count,
        "economics": economics,
        "laytime_status": lay_status,
        "laytime_difference": lay_diff,
        "demurrage_cost": demurrage_cost,
        "dispatch_credit": dispatch_credit,
        "hire_cost": hire_cost,
        "opex_cost": opex_cost,
        "net_profit": net_profit,
        "net_tce": net_tce,
        "utilization": utilization,
        "selected_speed": selected_speed,
        "selected_fuel_burn": selected_fuel_burn
    }


# ============================================================
# INPUTS — CARGO
# ============================================================

st.subheader("1. Cargo Opportunity")

cargoes["cargo_display"] = (
    cargoes["cargo_name"]
    + " | "
    + cargoes["cargo_type"]
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

st.info(
    f"Selected cargo: {cargo['cargo_name']} | "
    f"{cargo['cargo_tonnes']:,.0f} tonnes | "
    f"{cargo['load_port']} → {cargo['discharge_port']}"
)


# ============================================================
# INPUTS — VESSEL
# ============================================================

st.subheader("2. Vessel Selection")

selection_mode = st.radio(
    "Vessel Selection Mode",
    [
        "Auto select best vessel",
        "Manual vessel selection"
    ],
    horizontal=True
)

capable_fleet = fleet[
    fleet["cargo_capacity_tonnes"] >= cargo["cargo_tonnes"]
].copy()

if capable_fleet.empty:
    st.error("No vessel in the fleet can carry this cargo.")
    st.stop()

manual_vessel_name = None

if selection_mode == "Manual vessel selection":

    manual_vessel_name = st.selectbox(
        "Select Vessel",
        capable_fleet["vessel_name"].tolist()
    )

else:

    st.caption(
        "Auto mode evaluates all capable vessels and selects the strongest commercial result."
    )


# ============================================================
# INPUTS — COMMERCIAL
# ============================================================

st.subheader("3. Commercial Assumptions")

col1, col2, col3 = st.columns(3)

with col1:
    fuel_price = st.number_input(
        "Fuel Price ($/tonne)",
        min_value=100.0,
        max_value=3000.0,
        value=600.0,
        step=10.0
    )

with col2:
    load_port_cost = st.number_input(
        "Load Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

with col3:
    discharge_port_cost = st.number_input(
        "Discharge Port Cost ($)",
        min_value=0.0,
        value=25000.0,
        step=1000.0
    )

col1, col2, col3 = st.columns(3)

with col1:
    transit_fee_per_port = st.number_input(
        "Transit Fee Per Intermediate Port ($)",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

with col2:
    freight_premium_percent = st.number_input(
        "Freight Premium (%)",
        min_value=0.0,
        max_value=300.0,
        value=0.0,
        step=1.0
    )

with col3:
    route_cost_multiplier = st.number_input(
        "Route Cost Multiplier",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1
    )


# ============================================================
# INPUTS — SPEED
# ============================================================

st.subheader("4. Speed Assumptions")

use_speed_optimization = st.checkbox(
    "Optimize speed automatically",
    value=True
)

col1, col2, col3 = st.columns(3)

with col1:
    min_speed = st.number_input(
        "Minimum Speed (knots)",
        min_value=5,
        max_value=30,
        value=10
    )

with col2:
    max_speed = st.number_input(
        "Maximum Speed (knots)",
        min_value=5,
        max_value=30,
        value=16
    )

with col3:
    fuel_curve_exponent = st.number_input(
        "Fuel Curve Exponent",
        min_value=2.0,
        max_value=4.0,
        value=3.0,
        step=0.1
    )


# ============================================================
# INPUTS — LAYTIME
# ============================================================

st.subheader("5. Laytime Assumptions")

col1, col2 = st.columns(2)

with col1:
    allowed_load_laytime = st.number_input(
        "Allowed Load Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

with col2:
    actual_load_laytime = st.number_input(
        "Actual Load Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

col1, col2 = st.columns(2)

with col1:
    allowed_discharge_laytime = st.number_input(
        "Allowed Discharge Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

with col2:
    actual_discharge_laytime = st.number_input(
        "Actual Discharge Laytime (days)",
        min_value=0.0,
        value=2.0,
        step=0.5
    )

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


# ============================================================
# INPUTS — STOWAGE
# ============================================================

st.subheader("6. Stowage Assumptions")

default_stowage_factor, stowage_notes = get_stowage_factor(
    cargo["cargo_name"],
    stowage_factors
)

col1, col2, col3 = st.columns(3)

with col1:
    stowage_factor = st.number_input(
        "Stowage Factor (m³/tonne)",
        min_value=0.10,
        max_value=5.00,
        value=float(default_stowage_factor),
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

col1, col2 = st.columns(2)

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


# ============================================================
# INPUTS — DECISION
# ============================================================

st.subheader("7. Decision Thresholds")

minimum_tce = st.number_input(
    "Minimum Acceptable Net TCE ($/day)",
    min_value=0.0,
    value=10000.0,
    step=1000.0
)


# ============================================================
# RUN DASHBOARD
# ============================================================

if st.button("Run Master Voyage Assessment"):

    candidate_rows = []
    candidate_objects = []

    if selection_mode == "Manual vessel selection":

        analysis_fleet = capable_fleet[
            capable_fleet["vessel_name"] == manual_vessel_name
        ].copy()

    else:

        analysis_fleet = capable_fleet.copy()

    for _, vessel in analysis_fleet.iterrows():

        speed_options = []

        if use_speed_optimization:

            for speed in range(
                int(min_speed),
                int(max_speed) + 1
            ):

                fuel_burn_at_speed = estimate_fuel_burn_at_speed(
                    speed_knots=speed,
                    base_speed_knots=vessel["speed_knots"],
                    base_fuel_burn_tpd=vessel["fuel_burn_tpd"],
                    exponent=fuel_curve_exponent
                )

                speed_options.append(
                    (
                        speed,
                        fuel_burn_at_speed
                    )
                )

        else:

            speed_options.append(
                (
                    float(vessel["speed_knots"]),
                    float(vessel["fuel_burn_tpd"])
                )
            )

        for speed, fuel_burn_at_speed in speed_options:

            try:

                candidate = evaluate_candidate(
                    vessel=vessel,
                    cargo=cargo,
                    graph=graph,
                    congestion_df=congestion,
                    fuel_price=fuel_price,
                    load_port_cost=load_port_cost,
                    discharge_port_cost=discharge_port_cost,
                    transit_fee_per_port=transit_fee_per_port,
                    freight_premium_percent=freight_premium_percent,
                    route_cost_multiplier=route_cost_multiplier,
                    allowed_load_laytime=allowed_load_laytime,
                    actual_load_laytime=actual_load_laytime,
                    allowed_discharge_laytime=allowed_discharge_laytime,
                    actual_discharge_laytime=actual_discharge_laytime,
                    demurrage_rate=demurrage_rate,
                    dispatch_rate=dispatch_rate,
                    selected_speed=speed,
                    selected_fuel_burn=fuel_burn_at_speed
                )

            except Exception:

                continue

            candidate_objects.append(candidate)

            candidate_rows.append({
                "Vessel": vessel["vessel_name"],
                "Type": vessel["vessel_type"],
                "Current Port": vessel["current_port"],
                "Speed": round(speed, 2),
                "Fuel Burn (t/day)": round(fuel_burn_at_speed, 2),
                "Utilization %": round(candidate["utilization"], 2),
                "Earliest Ready Days": round(candidate["earliest_ready_days"], 2),
                "Congestion Days": round(candidate["congestion_days"], 2),
                "Voyage Revenue": candidate["economics"]["voyage_revenue"],
                "Voyage Cost": candidate["economics"]["voyage_cost"],
                "Hire Cost": round(candidate["hire_cost"], 2),
                "OPEX Cost": round(candidate["opex_cost"], 2),
                "Demurrage Cost": round(candidate["demurrage_cost"], 2),
                "Dispatch Credit": round(candidate["dispatch_credit"], 2),
                "Net Profit": round(candidate["net_profit"], 2),
                "Net TCE": round(candidate["net_tce"], 2)
            })

    candidates_df = pd.DataFrame(candidate_rows)

    if candidates_df.empty:
        st.error("No valid vessel/route/speed combination found.")
        st.stop()

    candidates_df = candidates_df.sort_values(
        by=[
            "Net Profit",
            "Net TCE",
            "Earliest Ready Days"
        ],
        ascending=[
            False,
            False,
            True
        ]
    )

    best_row = candidates_df.iloc[0]

    best_candidate = None

    for candidate in candidate_objects:
        if (
            candidate["vessel"]["vessel_name"] == best_row["Vessel"]
            and round(candidate["selected_speed"], 2) == round(best_row["Speed"], 2)
        ):
            best_candidate = candidate
            break

    if best_candidate is None:
        st.error("Internal selection error.")
        st.stop()

    economics = best_candidate["economics"]
    vessel = best_candidate["vessel"]

    # ========================================================
    # STOWAGE CHECK
    # ========================================================

    cargo_tonnes = float(cargo["cargo_tonnes"])

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

    vessel_capacity_with_margin = (
        float(vessel["cargo_capacity_tonnes"])
        *
        (1 - operational_margin_percent / 100)
    )

    volume_ok = cargo_volume_m3 <= usable_hold_volume_m3
    hold_weight_ok = cargo_tonnes <= usable_weight_capacity
    vessel_weight_ok = cargo_tonnes <= vessel_capacity_with_margin

    stowage_pass = (
        volume_ok
        and
        hold_weight_ok
        and
        vessel_weight_ok
    )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    high_congestion = (
        best_candidate["load_congestion_level"] == "High"
        or
        best_candidate["discharge_congestion_level"] == "High"
    )

    if (
        best_candidate["net_profit"] > 0
        and
        best_candidate["net_tce"] >= minimum_tce
        and
        stowage_pass
        and
        not high_congestion
    ):

        decision = "FIX / ACCEPT CARGO"
        decision_status = "success"

    elif (
        best_candidate["net_profit"] > 0
        and
        stowage_pass
    ):

        decision = "MARGINAL — REVIEW ASSUMPTIONS"
        decision_status = "warning"

    else:

        decision = "DO NOT FIX"
        decision_status = "error"

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    st.subheader("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Recommended Vessel",
            best_row["Vessel"]
        )

    with col2:
        st.metric(
            "Net Profit",
            f"${best_candidate['net_profit']:,.0f}"
        )

    with col3:
        st.metric(
            "Net TCE",
            f"${best_candidate['net_tce']:,.0f}/day"
        )

    with col4:
        st.metric(
            "Speed",
            f"{best_candidate['selected_speed']} kn"
        )

    if decision_status == "success":

        st.success(
            f"Final Recommendation: {decision}"
        )

    elif decision_status == "warning":

        st.warning(
            f"Final Recommendation: {decision}"
        )

    else:

        st.error(
            f"Final Recommendation: {decision}"
        )

    # ========================================================
    # CHARTERING RESULT
    # ========================================================

    st.subheader("Commercial Assessment")

    commercial_df = pd.DataFrame([{
        "Cargo": cargo["cargo_name"],
        "Cargo Type": cargo["cargo_type"],
        "Route": f"{cargo['load_port']} → {cargo['discharge_port']}",
        "Voyage Route": " → ".join(best_candidate["voyage_path"]),
        "Positioning Route": " → ".join(best_candidate["positioning_path"]),
        "Cargo Tonnes": cargo["cargo_tonnes"],
        "Vessel": best_row["Vessel"],
        "Vessel Type": best_row["Type"],
        "Current Port": best_row["Current Port"],
        "Utilization %": round(best_candidate["utilization"], 2),
        "Earliest Ready Days": round(best_candidate["earliest_ready_days"], 2),
        "Congestion Days": round(best_candidate["congestion_days"], 2),
        "Laytime Status": best_candidate["laytime_status"],
        "Stowage Pass": stowage_pass
    }])

    st.dataframe(
        commercial_df,
        use_container_width=True
    )

    # ========================================================
    # ECONOMICS
    # ========================================================

    st.subheader("Voyage Economics")

    economics_df = pd.DataFrame([{
        "Distance NM": economics["distance_nm"],
        "Sea Days": economics["sea_days"],
        "Ballast / Positioning Days": economics["ballast_days"],
        "Waiting / Congestion Days": economics["waiting_days"],
        "Port Days": economics["port_days"],
        "Total Voyage Days": economics["total_voyage_days"],
        "Revenue": economics["voyage_revenue"],
        "Voyage Cost": economics["voyage_cost"],
        "Hire Cost": round(best_candidate["hire_cost"], 2),
        "OPEX Cost": round(best_candidate["opex_cost"], 2),
        "Demurrage Cost": round(best_candidate["demurrage_cost"], 2),
        "Dispatch Credit": round(best_candidate["dispatch_credit"], 2),
        "Net Profit": round(best_candidate["net_profit"], 2),
        "Net TCE": round(best_candidate["net_tce"], 2)
    }])

    st.dataframe(
        economics_df,
        use_container_width=True
    )

    # ========================================================
    # COST BREAKDOWN
    # ========================================================

    st.subheader("Cost Breakdown")

    cost_df = pd.DataFrame([{
        "Fuel Cost": economics["fuel_cost"],
        "Port Costs": economics["port_costs"],
        "Transit Costs": economics["transit_costs"],
        "Base Route Cost": economics["base_route_cost"],
        "Adjusted Route Cost": economics["adjusted_route_cost"],
        "Hire Cost": round(best_candidate["hire_cost"], 2),
        "OPEX Cost": round(best_candidate["opex_cost"], 2),
        "Demurrage Cost": round(best_candidate["demurrage_cost"], 2),
        "Dispatch Credit": round(best_candidate["dispatch_credit"], 2)
    }])

    st.dataframe(
        cost_df,
        use_container_width=True
    )

    # ========================================================
    # ROUTE LEG BREAKDOWN
    # ========================================================

    st.subheader("Voyage Route Breakdown")

    st.dataframe(
        pd.DataFrame(best_candidate["voyage_data"]["rows"]),
        use_container_width=True
    )

    # ========================================================
    # STOWAGE
    # ========================================================

    st.subheader("Stowage Check")

    stowage_df = pd.DataFrame([{
        "Cargo Volume Required m³": round(cargo_volume_m3, 2),
        "Usable Hold Volume m³": round(usable_hold_volume_m3, 2),
        "Total Hold Weight Capacity": round(total_hold_weight_capacity, 2),
        "Usable Hold Weight Capacity": round(usable_weight_capacity, 2),
        "Vessel Capacity After Margin": round(vessel_capacity_with_margin, 2),
        "Volume OK": volume_ok,
        "Hold Weight OK": hold_weight_ok,
        "Vessel Weight OK": vessel_weight_ok,
        "Stowage Pass": stowage_pass,
        "Stowage Notes": stowage_notes
    }])

    st.dataframe(
        stowage_df,
        use_container_width=True
    )

    if stowage_pass:
        st.success("Basic stowage check passed.")
    else:
        st.error("Stowage warning: cargo may exceed hold/vessel assumptions.")

    # ========================================================
    # CANDIDATE RANKING
    # ========================================================

    st.subheader("Candidate Ranking")

    st.dataframe(
        candidates_df,
        use_container_width=True
    )

    # ========================================================
    # METHOD
    # ========================================================

    st.subheader("Method Summary")

    st.write(
        """
        This dashboard combines the major project components into one workflow:

        1. Select a cargo opportunity.
        2. Filter vessels that can carry the cargo.
        3. Estimate vessel positioning time to the load port.
        4. Calculate the voyage route and distance.
        5. Add port congestion days.
        6. Calculate voyage economics, profit and TCE.
        7. Apply demurrage or dispatch impact.
        8. Check basic stowage feasibility.
        9. Rank vessel/speed combinations.
        10. Produce a final commercial recommendation.

        This is still a transparent decision-support model, not a certified
        naval architecture, charter-party, or live market system.
        """
    )