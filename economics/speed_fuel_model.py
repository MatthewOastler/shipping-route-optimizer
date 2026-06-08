# economics/speed_fuel_model.py

"""
Shipping Route Optimizer
Speed Fuel Model

Version 1

Accurate results without lying to ourselves.
"""


# ============================================================
# SPEED / FUEL RELATIONSHIP
# ============================================================

def estimate_fuel_burn_at_speed(
    speed_knots,
    base_speed_knots,
    base_fuel_burn_tpd,
    exponent=3.0
):
    """
    Estimate daily fuel burn at a given speed.

    Approximation:

        Fuel Burn
        =
        Base Fuel Burn
        ×
        (Speed / Base Speed)^Exponent

    Typical exponents:

        2.5 = efficient vessel
        3.0 = industry approximation
        3.5 = less efficient vessel

    Example:

        Base:
            13 knots
            30 tonnes/day

        At 16 knots:

            30 × (16/13)^3

            ≈ 55.9 tonnes/day
    """

    speed_knots = float(speed_knots)
    base_speed_knots = float(base_speed_knots)
    base_fuel_burn_tpd = float(base_fuel_burn_tpd)
    exponent = float(exponent)

    if speed_knots <= 0:
        raise ValueError(
            "Speed must be greater than zero."
        )

    if base_speed_knots <= 0:
        raise ValueError(
            "Base speed must be greater than zero."
        )

    if base_fuel_burn_tpd < 0:
        raise ValueError(
            "Base fuel burn cannot be negative."
        )

    return (

        base_fuel_burn_tpd

        *

        (

            speed_knots

            /

            base_speed_knots

        ) ** exponent

    )


# ============================================================
# SPEED TABLE
# ============================================================

def build_speed_fuel_table(
    base_speed_knots,
    base_fuel_burn_tpd,
    min_speed=8,
    max_speed=20,
    exponent=3.0
):
    """
    Create a speed/fuel lookup table.

    Useful for:
        speed optimizer
        debugging
        charts
    """

    rows = []

    for speed in range(
        int(min_speed),
        int(max_speed) + 1
    ):

        fuel_burn = estimate_fuel_burn_at_speed(

            speed_knots=speed,

            base_speed_knots=base_speed_knots,

            base_fuel_burn_tpd=base_fuel_burn_tpd,

            exponent=exponent

        )

        rows.append({

            "speed_knots":
                speed,

            "fuel_burn_tpd":
                round(
                    fuel_burn,
                    2
                )

        })

    return rows


# ============================================================
# ECONOMIC SPEED
# ============================================================

def estimate_economic_speed(
    fuel_price
):
    """
    Simple heuristic.

    Higher fuel prices generally
    encourage slower steaming.

    Returns suggested speed.
    """

    fuel_price = float(
        fuel_price
    )

    if fuel_price >= 1200:

        return 11

    elif fuel_price >= 900:

        return 12

    elif fuel_price >= 700:

        return 13

    elif fuel_price >= 500:

        return 14

    else:

        return 15


# ============================================================
# EXAMPLE
# ============================================================

if __name__ == "__main__":

    print(
        "Speed/Fuel Example"
    )

    table = build_speed_fuel_table(

        base_speed_knots=13,

        base_fuel_burn_tpd=30,

        min_speed=10,

        max_speed=18,

        exponent=3.0

    )

    for row in table:

        print(row)

    print()

    print(

        "Suggested Economic Speed:",

        estimate_economic_speed(
            fuel_price=900
        )

    )