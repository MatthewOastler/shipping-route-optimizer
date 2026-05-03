import math


def brute_force_shortest_path(df, start, end):

    adjacency = {}

    for _, r in df.iterrows():

        cost = (
            float(r["fuel_cost_estimate"])
            + float(r.get("canal_fee", 0))
            + float(r.get("weather_risk", 0))
            + float(r.get("piracy_risk", 0))
            + float(r.get("carbon_cost", 0))
        )

        origin = str(r["origin_port"]).strip()
        dest = str(r["destination_port"]).strip()

        # forward
        adjacency.setdefault(origin, []).append((dest, cost))

        # reverse
        adjacency.setdefault(dest, []).append((origin, cost))

    best_path = None
    best_cost = math.inf

    def dfs(current, visited, cost_so_far, path):

        nonlocal best_path, best_cost

        if cost_so_far >= best_cost:
            return

        if current == end:
            best_path = path[:]
            best_cost = cost_so_far
            return

        for neighbor, edge_cost in adjacency.get(current, []):

            if neighbor in visited:
                continue

            visited.add(neighbor)

            dfs(
                neighbor,
                visited,
                cost_so_far + edge_cost,
                path + [neighbor]
            )

            visited.remove(neighbor)

    dfs(
        start,
        {start},
        0,
        [start]
    )

    if best_path is None:
        raise ValueError(f"No path between {start} and {end}")

    return best_path, best_cost