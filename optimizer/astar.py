import networkx as nx


def astar_path(G, start, end, weight="total_cost"):

    start = str(start).strip()
    end = str(end).strip()

    if not nx.has_path(G, start, end):
        raise ValueError(f"No path exists between {start} and {end}")

    path = nx.astar_path(
        G,
        start,
        end,
        heuristic=lambda a, b: 0,
        weight=weight
    )

    cost = nx.astar_path_length(
        G,
        start,
        end,
        heuristic=lambda a, b: 0,
        weight=weight
    )

    return path, cost