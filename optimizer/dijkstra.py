# optimizer/dijkstra.py

import networkx as nx
from optimizer.cost_model import calculate_edge_cost


def build_graph(df):

    G = nx.DiGraph()

    for _, r in df.iterrows():

        # ---- Validate row ----
        if r["origin_port"] == r["destination_port"]:
            continue  # skip invalid self-loop

        # ---- Build edge ----
        edge = {
            "distance": float(r["distance_nm"]),
            "fuel_cost": float(r["fuel_cost_estimate"]),
            "canal_fee": float(r.get("canal_fee", 0)),
            "weather_risk": float(r.get("weather_risk", 0)),
            "piracy_risk": float(r.get("piracy_risk", 0)),
            "carbon_cost": float(r.get("carbon_cost", 0))
        }

        edge["total_cost"] = calculate_edge_cost(edge)

        origin = str(r["origin_port"]).strip()
        dest = str(r["destination_port"]).strip()

        # ---- Add nodes explicitly (important for debugging) ----
        G.add_node(origin)
        G.add_node(dest)

        # ---- Add forward edge ----
        G.add_edge(origin, dest, **edge)

        # ---- Add reverse edge ----
        G.add_edge(dest, origin, **edge)

    return G


def shortest_path(G, start, end, weight="total_cost"):

    # ---- Clean inputs ----
    start = str(start).strip()
    end = str(end).strip()

    # ---- Check nodes exist ----
    if start not in G.nodes:
        raise ValueError(f"Start node '{start}' not in graph")

    if end not in G.nodes:
        raise ValueError(f"End node '{end}' not in graph")

    # ---- Check connectivity BEFORE running Dijkstra ----
    if not nx.has_path(G, start, end):
        raise ValueError(f"No path exists between {start} and {end}")

    # ---- Run Dijkstra ----
    path = nx.dijkstra_path(G, start, end, weight=weight)
    cost = nx.dijkstra_path_length(G, start, end, weight=weight)

    return path, cost