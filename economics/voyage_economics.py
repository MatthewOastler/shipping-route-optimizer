# # economics/voyage_economics.py

# """
# Shipping Route Optimizer
# Voyage Economics Engine

# Version 2

# Accurate results without lying to ourselves.
# """


# # ============================================================
# # REVENUE
# # ============================================================

# def calculate_revenue(
#     cargo_tonnes,
#     freight_rate
# ):
#     """
#     Revenue from transporting cargo.

#     Revenue =
#         Cargo Tonnes
#         ×
#         Freight Rate ($/t)
#     """

#     return (
#         float(cargo_tonnes)
#         *
#         float(freight_rate)
#     )


# # ============================================================
# # SEA DAYS
# # ============================================================

# def calculate_sea_days(
#     distance_nm,
#     vessel_speed_knots
# ):
#     """
#     Sea Days

#     Distance NM
#     ÷
#     Vessel Speed (knots)
#     ÷
#     24
#     """

#     if vessel_speed_knots <= 0:

#         raise ValueError(
#             "Vessel speed must be greater than zero."
#         )

#     return (
#         float(distance_nm)
#         /
#         float(vessel_speed_knots)
#         /
#         24
#     )


# # ============================================================
# # FUEL CONSUMPTION
# # ============================================================

# def calculate_fuel_consumed(
#     sea_days,
#     fuel_burn_tonnes_per_day
# ):
#     """
#     Fuel Consumed

#     Sea Days
#     ×
#     Daily Fuel Burn
#     """

#     return (
#         float(sea_days)
#         *
#         float(fuel_burn_tonnes_per_day)
#     )


# # ============================================================
# # FUEL COST
# # ============================================================

# def calculate_fuel_cost(
#     fuel_consumed,
#     fuel_price
# ):
#     """
#     Fuel Cost

#     Fuel Consumed
#     ×
#     Fuel Price
#     """

#     return (
#         float(fuel_consumed)
#         *
#         float(fuel_price)
#     )


# # ============================================================
# # PORT COSTS
# # ============================================================

# def calculate_port_costs(
#     load_port_cost,
#     discharge_port_cost
# ):
#     """
#     Total Port Costs
#     """

#     return (
#         float(load_port_cost)
#         +
#         float(discharge_port_cost)
#     )


# # ============================================================
# # VOYAGE COST
# # ============================================================

# def calculate_voyage_cost(
#     fuel_cost,
#     port_costs,
#     route_cost
# ):
#     """
#     Total Voyage Cost

#     Fuel
#     +
#     Ports
#     +
#     Routing Costs
#     """

#     return (
#         float(fuel_cost)
#         +
#         float(port_costs)
#         +
#         float(route_cost)
#     )


# # ============================================================
# # VOYAGE PROFIT
# # ============================================================

# def calculate_voyage_profit(
#     revenue,
#     voyage_cost
# ):
#     """
#     Voyage Profit

#     Revenue
#     -
#     Voyage Cost
#     """

#     return (
#         float(revenue)
#         -
#         float(voyage_cost)
#     )


# # ============================================================
# # TCE
# # ============================================================

# def calculate_tce(
#     voyage_profit,
#     voyage_days
# ):
#     """
#     Time Charter Equivalent

#     Voyage Profit
#     ÷
#     Voyage Days
#     """

#     if voyage_days <= 0:

#         return 0

#     return (
#         float(voyage_profit)
#         /
#         float(voyage_days)
#     )


# # ============================================================
# # MASTER CALCULATION
# # ============================================================

# def calculate_voyage_economics(
#     distance_nm,
#     route_cost,
#     cargo_tonnes,
#     freight_rate,
#     vessel_speed_knots,
#     fuel_burn_tonnes_per_day,
#     fuel_price,
#     load_port_cost,
#     discharge_port_cost
# ):
#     """
#     Complete voyage economics calculation.

#     Returns dictionary.
#     """

#     revenue = calculate_revenue(
#         cargo_tonnes,
#         freight_rate
#     )

#     sea_days = calculate_sea_days(
#         distance_nm,
#         vessel_speed_knots
#     )

#     fuel_consumed = calculate_fuel_consumed(
#         sea_days,
#         fuel_burn_tonnes_per_day
#     )

#     fuel_cost = calculate_fuel_cost(
#         fuel_consumed,
#         fuel_price
#     )

#     port_costs = calculate_port_costs(
#         load_port_cost,
#         discharge_port_cost
#     )

#     voyage_cost = calculate_voyage_cost(
#         fuel_cost,
#         port_costs,
#         route_cost
#     )

#     voyage_profit = calculate_voyage_profit(
#         revenue,
#         voyage_cost
#     )

#     tce = calculate_tce(
#         voyage_profit,
#         sea_days
#     )

#     return {

#         "distance_nm":
#             round(distance_nm, 2),

#         "sea_days":
#             round(sea_days, 2),

#         "fuel_consumed":
#             round(fuel_consumed, 2),

#         "fuel_cost":
#             round(fuel_cost, 2),

#         "port_costs":
#             round(port_costs, 2),

#         "route_cost":
#             round(route_cost, 2),

#         "voyage_revenue":
#             round(revenue, 2),

#         "voyage_cost":
#             round(voyage_cost, 2),

#         "voyage_profit":
#             round(voyage_profit, 2),

#         "tce":
#             round(tce, 2)

#     }


# # ============================================================
# # EXAMPLE
# # ============================================================

# if __name__ == "__main__":

#     result = calculate_voyage_economics(

#         distance_nm=5000,

#         route_cost=100000,

#         cargo_tonnes=50000,

#         freight_rate=25,

#         vessel_speed_knots=13,

#         fuel_burn_tonnes_per_day=30,

#         fuel_price=600,

#         load_port_cost=25000,

#         discharge_port_cost=25000
#     )

#     print(result)






















# economics/voyage_economics.py

"""
Shipping Route Optimizer
Voyage Economics Engine

Version 2.1

Accurate results without lying to ourselves.
"""


def calculate_revenue(cargo_tonnes, freight_rate, freight_premium_percent=0):
    """
    Revenue = cargo tonnes × freight rate × premium multiplier
    """

    premium_multiplier = 1 + (float(freight_premium_percent) / 100)

    return float(cargo_tonnes) * float(freight_rate) * premium_multiplier


def calculate_sea_days(distance_nm, vessel_speed_knots):
    """
    Sea days = distance nautical miles / speed knots / 24
    """

    if float(vessel_speed_knots) <= 0:
        raise ValueError("Vessel speed must be greater than zero.")

    return float(distance_nm) / float(vessel_speed_knots) / 24


def calculate_total_voyage_days(
    sea_days,
    ballast_days=0,
    waiting_days=0,
    port_days=0
):
    """
    Total voyage days = sea days + ballast days + waiting days + port days
    """

    return (
        float(sea_days)
        + float(ballast_days)
        + float(waiting_days)
        + float(port_days)
    )


def calculate_fuel_consumed(sea_days, fuel_burn_tonnes_per_day):
    """
    Fuel consumed = sea days × fuel burn tonnes/day
    """

    return float(sea_days) * float(fuel_burn_tonnes_per_day)


def calculate_fuel_cost(fuel_consumed, fuel_price):
    """
    Fuel cost = fuel consumed × fuel price
    """

    return float(fuel_consumed) * float(fuel_price)


def calculate_port_costs(load_port_cost, discharge_port_cost):
    """
    Port costs = load port cost + discharge port cost
    """

    return float(load_port_cost) + float(discharge_port_cost)


def calculate_transit_costs(transit_port_count=0, transit_fee_per_port=0):
    """
    Transit costs = number of intermediate transit ports × fee per transit port
    """

    return float(transit_port_count) * float(transit_fee_per_port)


def calculate_adjusted_route_cost(route_cost, route_cost_multiplier=1.0):
    """
    Adjusted route cost = base route cost × route cost multiplier
    """

    return float(route_cost) * float(route_cost_multiplier)


def calculate_voyage_cost(
    fuel_cost,
    port_costs,
    transit_costs,
    adjusted_route_cost
):
    """
    Voyage cost = fuel + port costs + transit costs + adjusted route cost
    """

    return (
        float(fuel_cost)
        + float(port_costs)
        + float(transit_costs)
        + float(adjusted_route_cost)
    )


def calculate_voyage_profit(revenue, voyage_cost):
    """
    Voyage profit = revenue - voyage cost
    """

    return float(revenue) - float(voyage_cost)


def calculate_tce(voyage_profit, total_voyage_days):
    """
    TCE = voyage profit / total voyage days
    """

    if float(total_voyage_days) <= 0:
        return 0

    return float(voyage_profit) / float(total_voyage_days)


def calculate_voyage_economics(
    distance_nm,
    route_cost,
    cargo_tonnes,
    freight_rate,
    vessel_speed_knots,
    fuel_burn_tonnes_per_day,
    fuel_price,
    load_port_cost,
    discharge_port_cost,
    freight_premium_percent=0,
    ballast_days=0,
    waiting_days=0,
    port_days=0,
    transit_port_count=0,
    transit_fee_per_port=0,
    route_cost_multiplier=1.0
):
    """
    Complete voyage economics calculation.
    """

    revenue = calculate_revenue(
        cargo_tonnes=cargo_tonnes,
        freight_rate=freight_rate,
        freight_premium_percent=freight_premium_percent
    )

    sea_days = calculate_sea_days(
        distance_nm=distance_nm,
        vessel_speed_knots=vessel_speed_knots
    )

    total_voyage_days = calculate_total_voyage_days(
        sea_days=sea_days,
        ballast_days=ballast_days,
        waiting_days=waiting_days,
        port_days=port_days
    )

    fuel_consumed = calculate_fuel_consumed(
        sea_days=sea_days,
        fuel_burn_tonnes_per_day=fuel_burn_tonnes_per_day
    )

    fuel_cost = calculate_fuel_cost(
        fuel_consumed=fuel_consumed,
        fuel_price=fuel_price
    )

    port_costs = calculate_port_costs(
        load_port_cost=load_port_cost,
        discharge_port_cost=discharge_port_cost
    )

    transit_costs = calculate_transit_costs(
        transit_port_count=transit_port_count,
        transit_fee_per_port=transit_fee_per_port
    )

    adjusted_route_cost = calculate_adjusted_route_cost(
        route_cost=route_cost,
        route_cost_multiplier=route_cost_multiplier
    )

    voyage_cost = calculate_voyage_cost(
        fuel_cost=fuel_cost,
        port_costs=port_costs,
        transit_costs=transit_costs,
        adjusted_route_cost=adjusted_route_cost
    )

    voyage_profit = calculate_voyage_profit(
        revenue=revenue,
        voyage_cost=voyage_cost
    )

    tce = calculate_tce(
        voyage_profit=voyage_profit,
        total_voyage_days=total_voyage_days
    )

    return {
        "distance_nm": round(float(distance_nm), 2),
        "sea_days": round(sea_days, 2),
        "ballast_days": round(float(ballast_days), 2),
        "waiting_days": round(float(waiting_days), 2),
        "port_days": round(float(port_days), 2),
        "total_voyage_days": round(total_voyage_days, 2),
        "fuel_consumed": round(fuel_consumed, 2),
        "fuel_cost": round(fuel_cost, 2),
        "load_port_cost": round(float(load_port_cost), 2),
        "discharge_port_cost": round(float(discharge_port_cost), 2),
        "port_costs": round(port_costs, 2),
        "transit_port_count": int(transit_port_count),
        "transit_fee_per_port": round(float(transit_fee_per_port), 2),
        "transit_costs": round(transit_costs, 2),
        "base_route_cost": round(float(route_cost), 2),
        "route_cost_multiplier": round(float(route_cost_multiplier), 2),
        "adjusted_route_cost": round(adjusted_route_cost, 2),
        "voyage_revenue": round(revenue, 2),
        "voyage_cost": round(voyage_cost, 2),
        "voyage_profit": round(voyage_profit, 2),
        "tce": round(tce, 2),
    }


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
        discharge_port_cost=25000,
        freight_premium_percent=10,
        ballast_days=2,
        waiting_days=1,
        port_days=3,
        transit_port_count=2,
        transit_fee_per_port=15000,
        route_cost_multiplier=1.0
    )

    print(result)

















