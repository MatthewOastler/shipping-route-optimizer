# economics/voyage_economics.py

"""
Shipping Route Optimizer
Voyage Economics Engine

Version 2

Accurate results without lying to ourselves.
"""


# ============================================================
# REVENUE
# ============================================================

def calculate_revenue(
    cargo_tonnes,
    freight_rate
):
    """
    Revenue from transporting cargo.

    Revenue =
        Cargo Tonnes
        ×
        Freight Rate ($/t)
    """

    return (
        float(cargo_tonnes)
        *
        float(freight_rate)
    )


# ============================================================
# SEA DAYS
# ============================================================

def calculate_sea_days(
    distance_nm,
    vessel_speed_knots
):
    """
    Sea Days

    Distance NM
    ÷
    Vessel Speed (knots)
    ÷
    24
    """

    if vessel_speed_knots <= 0:

        raise ValueError(
            "Vessel speed must be greater than zero."
        )

    return (
        float(distance_nm)
        /
        float(vessel_speed_knots)
        /
        24
    )


# ============================================================
# FUEL CONSUMPTION
# ============================================================

def calculate_fuel_consumed(
    sea_days,
    fuel_burn_tonnes_per_day
):
    """
    Fuel Consumed

    Sea Days
    ×
    Daily Fuel Burn
    """

    return (
        float(sea_days)
        *
        float(fuel_burn_tonnes_per_day)
    )


# ============================================================
# FUEL COST
# ============================================================

def calculate_fuel_cost(
    fuel_consumed,
    fuel_price
):
    """
    Fuel Cost

    Fuel Consumed
    ×
    Fuel Price
    """

    return (
        float(fuel_consumed)
        *
        float(fuel_price)
    )


# ============================================================
# PORT COSTS
# ============================================================

def calculate_port_costs(
    load_port_cost,
    discharge_port_cost
):
    """
    Total Port Costs
    """

    return (
        float(load_port_cost)
        +
        float(discharge_port_cost)
    )


# ============================================================
# VOYAGE COST
# ============================================================

def calculate_voyage_cost(
    fuel_cost,
    port_costs,
    route_cost
):
    """
    Total Voyage Cost

    Fuel
    +
    Ports
    +
    Routing Costs
    """

    return (
        float(fuel_cost)
        +
        float(port_costs)
        +
        float(route_cost)
    )


# ============================================================
# VOYAGE PROFIT
# ============================================================

def calculate_voyage_profit(
    revenue,
    voyage_cost
):
    """
    Voyage Profit

    Revenue
    -
    Voyage Cost
    """

    return (
        float(revenue)
        -
        float(voyage_cost)
    )


# ============================================================
# TCE
# ============================================================

def calculate_tce(
    voyage_profit,
    voyage_days
):
    """
    Time Charter Equivalent

    Voyage Profit
    ÷
    Voyage Days
    """

    if voyage_days <= 0:

        return 0

    return (
        float(voyage_profit)
        /
        float(voyage_days)
    )


# ============================================================
# MASTER CALCULATION
# ============================================================

def calculate_voyage_economics(
    distance_nm,
    route_cost,
    cargo_tonnes,
    freight_rate,
    vessel_speed_knots,
    fuel_burn_tonnes_per_day,
    fuel_price,
    load_port_cost,
    discharge_port_cost
):
    """
    Complete voyage economics calculation.

    Returns dictionary.
    """

    revenue = calculate_revenue(
        cargo_tonnes,
        freight_rate
    )

    sea_days = calculate_sea_days(
        distance_nm,
        vessel_speed_knots
    )

    fuel_consumed = calculate_fuel_consumed(
        sea_days,
        fuel_burn_tonnes_per_day
    )

    fuel_cost = calculate_fuel_cost(
        fuel_consumed,
        fuel_price
    )

    port_costs = calculate_port_costs(
        load_port_cost,
        discharge_port_cost
    )

    voyage_cost = calculate_voyage_cost(
        fuel_cost,
        port_costs,
        route_cost
    )

    voyage_profit = calculate_voyage_profit(
        revenue,
        voyage_cost
    )

    tce = calculate_tce(
        voyage_profit,
        sea_days
    )

    return {

        "distance_nm":
            round(distance_nm, 2),

        "sea_days":
            round(sea_days, 2),

        "fuel_consumed":
            round(fuel_consumed, 2),

        "fuel_cost":
            round(fuel_cost, 2),

        "port_costs":
            round(port_costs, 2),

        "route_cost":
            round(route_cost, 2),

        "voyage_revenue":
            round(revenue, 2),

        "voyage_cost":
            round(voyage_cost, 2),

        "voyage_profit":
            round(voyage_profit, 2),

        "tce":
            round(tce, 2)

    }


# ============================================================
# EXAMPLE
# ============================================================

if __name__ == "__main__":

    result = calculate_voyage_economics(

        distance_nm=5000,

        route_cost=100000,

        cargo_tonnes=50000,

        freight_rate=25,

        vessel_speed_knots=13,

        fuel_burn_tonnes_per_day=30,

        fuel_price=600,

        load_port_cost=25000,

        discharge_port_cost=25000
    )

    print(result)