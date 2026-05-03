# optimizer/route_generator.py

import pandas as pd
from geopy.distance import geodesic


NM_PER_KM = 0.539957

# Major global shipping hubs for guaranteed connectivity
GLOBAL_HUBS = [
    "SYD",
    "SIN",
    "DXB",
    "RTM",
    "NYC",
    "LAX",
    "CPT",
]


def calculate_distance_nm(lat1, lon1, lat2, lon2):
    """
    Calculate nautical miles between two coordinates.
    """
    km = geodesic((lat1, lon1), (lat2, lon2)).km
    return km * NM_PER_KM


def estimate_route_cost(distance_nm, origin_region, destination_region):
    """
    Version 1.5 estimated route cost model.
    Transparent assumptions:
    - Fuel
    - Carbon
    - Weather
    - Piracy
    - Canal
    """

    fuel_cost = distance_nm * 30
    carbon_cost = distance_nm * 0.5

    canal_fee = 0
    weather_risk = 500
    piracy_risk = 0

    risky_regions = ["Africa", "Middle East", "Asia"]

    if origin_region != destination_region:
        weather_risk = 800

    if (
        origin_region in risky_regions
        or destination_region in risky_regions
    ):
        piracy_risk = 200

    # Approximate canal zones
    if (
        ("Europe" in [origin_region, destination_region])
        and ("Asia" in [origin_region, destination_region])
    ):
        canal_fee = 5000

    return {
        "fuel_cost_estimate": round(fuel_cost, 2),
        "canal_fee": round(canal_fee, 2),
        "weather_risk": round(weather_risk, 2),
        "piracy_risk": round(piracy_risk, 2),
        "carbon_cost": round(carbon_cost, 2),
    }


def route_exists(route_set, origin, destination):
    return (origin, destination) in route_set


def generate_routes(
    ports_df,
    max_distance_nm=6000,
    bidirectional=True,
):
    """
    Generate global shipping network with:

    Layer 1:
    - Geographic local routes

    Layer 2:
    - Mandatory hub connectivity

    Layer 3:
    - Bidirectional support
    """

    required_cols = [
        "port_id",
        "port_name",
        "country",
        "lat",
        "lon",
        "region",
        "port_type",
    ]

    for col in required_cols:
        if col not in ports_df.columns:
            raise ValueError(f"Missing required column: {col}")

    routes = []
    route_set = set()

    # ============================================================
    # Layer 1 — Distance-based local routes
    # ============================================================

    for _, origin in ports_df.iterrows():
        for _, destination in ports_df.iterrows():

            origin_id = str(origin["port_id"]).strip()
            destination_id = str(destination["port_id"]).strip()

            if origin_id == destination_id:
                continue

            if route_exists(route_set, origin_id, destination_id):
                continue

            distance_nm = calculate_distance_nm(
                float(origin["lat"]),
                float(origin["lon"]),
                float(destination["lat"]),
                float(destination["lon"]),
            )

            if distance_nm > max_distance_nm:
                continue

            costs = estimate_route_cost(
                distance_nm,
                origin["region"],
                destination["region"],
            )

            routes.append({
                "origin_port": origin_id,
                "destination_port": destination_id,
                "distance_nm": round(distance_nm, 2),
                **costs,
            })

            route_set.add((origin_id, destination_id))

            if bidirectional:
                routes.append({
                    "origin_port": destination_id,
                    "destination_port": origin_id,
                    "distance_nm": round(distance_nm, 2),
                    **costs,
                })

                route_set.add((destination_id, origin_id))

    # ============================================================
    # Layer 2 — Guaranteed global hub network
    # ============================================================

    hubs_df = ports_df[ports_df["port_id"].isin(GLOBAL_HUBS)]

    for _, origin in hubs_df.iterrows():
        for _, destination in hubs_df.iterrows():

            origin_id = str(origin["port_id"]).strip()
            destination_id = str(destination["port_id"]).strip()

            if origin_id == destination_id:
                continue

            if route_exists(route_set, origin_id, destination_id):
                continue

            distance_nm = calculate_distance_nm(
                float(origin["lat"]),
                float(origin["lon"]),
                float(destination["lat"]),
                float(destination["lon"]),
            )

            costs = estimate_route_cost(
                distance_nm,
                origin["region"],
                destination["region"],
            )

            routes.append({
                "origin_port": origin_id,
                "destination_port": destination_id,
                "distance_nm": round(distance_nm, 2),
                **costs,
            })

            route_set.add((origin_id, destination_id))

            if bidirectional:
                routes.append({
                    "origin_port": destination_id,
                    "destination_port": origin_id,
                    "distance_nm": round(distance_nm, 2),
                    **costs,
                })

                route_set.add((destination_id, origin_id))

    routes_df = pd.DataFrame(routes)

    if routes_df.empty:
        raise ValueError(
            "No routes generated. Check global_ports.csv or increase max_distance_nm."
        )

    return routes_df


def save_generated_routes(
    ports_file="data/global_ports.csv",
    output_file="data/generated_routes.csv",
    max_distance_nm=6000,
):
    """
    Load global ports and save generated shipping network.
    """

    ports_df = pd.read_csv(ports_file)

    routes_df = generate_routes(
        ports_df=ports_df,
        max_distance_nm=max_distance_nm,
        bidirectional=True,
    )

    routes_df.to_csv(output_file, index=False)

    return routes_df


if __name__ == "__main__":

    routes = save_generated_routes()

    print(f"Generated {len(routes)} routes")
    print(routes.head())