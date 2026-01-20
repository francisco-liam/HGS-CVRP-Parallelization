#!/usr/bin/env python3
"""
describe_solution.py

Purpose:
    Read a CVRPLIB/ECVRP solution file (Route #k: ... / Cost ...) and the corresponding
    instance file (.vrp/.evrp). Produce a detailed report that includes:
      - Each route with nodes annotated as "id(x,y)"
      - Route length (distance) including depot -> first -> ... -> last -> depot
      - Total length across all routes

Usage (Python 3):
    python3 describe_solution.py <solution.sol> <instance.vrp|instance.evrp> <output.txt>

Example:
    python3 describe_solution.py mySolution.sol ../Instances/ECVRP/X-n147-k7-s4.evrp detailed_solution.txt
"""

import sys
import math
from typing import Dict, List, Optional, Set, Tuple


def parse_instance_coords(path: str) -> Dict[int, Tuple[float, float]]:
    coords: Dict[int, Tuple[float, float]] = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = f.read().split()

    # Find NODE_COORD_SECTION
    try:
        idx = tokens.index("NODE_COORD_SECTION") + 1
    except ValueError:
        raise ValueError("NODE_COORD_SECTION not found in instance file")

    # Read triplets until a section keyword
    i = idx
    while i + 2 < len(tokens):
        if tokens[i] in {"DEMAND_SECTION", "STATION_COORD_SECTION", "STATIONS_COORD_SECTION", "DEPOT_SECTION", "EOF"}:
            break
        node_id = int(tokens[i])
        x = float(tokens[i + 1])
        y = float(tokens[i + 2])
        coords[node_id] = (x, y)
        i += 3

    if 1 not in coords:
        raise ValueError("Depot node 1 not found in coordinates")
    return coords


def parse_energy_params(path: str) -> Tuple[Optional[float], Optional[float]]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [t.rstrip(":") for t in f.read().split()]

    energy_capacity = None
    energy_consumption = None

    for i, token in enumerate(tokens):
        if token == "ENERGY_CAPACITY" and i + 1 < len(tokens):
            energy_capacity = float(tokens[i + 1])
        elif token == "ENERGY_CONSUMPTION" and i + 1 < len(tokens):
            energy_consumption = float(tokens[i + 1])

    return energy_capacity, energy_consumption


def parse_station_indices(path: str) -> Set[int]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = f.read().split()

    station_indices: Set[int] = set()
    for i, token in enumerate(tokens):
        if token in {"STATION_COORD_SECTION", "STATIONS_COORD_SECTION"}:
            j = i + 1
            while j < len(tokens) and tokens[j] != "DEPOT_SECTION":
                try:
                    station_indices.add(int(tokens[j]))
                except ValueError:
                    pass
                j += 1
            break

    return station_indices


def parse_capacity_and_demands(path: str) -> Tuple[Optional[float], Dict[int, float]]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [t.rstrip(":") for t in f.read().split()]

    capacity = None
    demands: Dict[int, float] = {}

    for i, token in enumerate(tokens):
        if token == "CAPACITY" and i + 1 < len(tokens):
            capacity = float(tokens[i + 1])

    try:
        idx = tokens.index("DEMAND_SECTION") + 1
    except ValueError:
        return capacity, demands

    i = idx
    while i + 1 < len(tokens):
        if tokens[i] in {"STATION_COORD_SECTION", "STATIONS_COORD_SECTION", "DEPOT_SECTION", "EOF"}:
            break
        try:
            node_id = int(tokens[i])
            demand = float(tokens[i + 1])
            demands[node_id] = demand
        except ValueError:
            pass
        i += 2

    return capacity, demands


def parse_solution_routes(path: str) -> Tuple[List[List[int]], float]:
    routes: List[List[int]] = []
    total_cost = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Route #"):
                # format: Route #k: a b c
                parts = line.split(":", 1)
                if len(parts) == 2:
                    nodes = [int(x) for x in parts[1].strip().split() if x.strip()]
                    routes.append(nodes)
            elif line.startswith("Cost"):
                try:
                    total_cost = float(line.split()[1])
                except Exception:
                    total_cost = None
    return routes, total_cost


def rounded_dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    d = math.hypot(a[0] - b[0], a[1] - b[1])
    return float(math.floor(d + 0.5))


def rounded_energy(distance: float, consumption: float, load: float, capacity: float) -> float:
    return float(math.floor(distance * (consumption + load / capacity) + 0.5))


def route_length(route: List[int], coords: Dict[int, Tuple[float, float]]) -> float:
    if not route:
        return 0.0
    # Route nodes are 0-based relative to customers; add 1 for coordinate lookup
    length = 0.0
    depot = 1
    first_node = route[0] + 1
    length += rounded_dist(coords[depot], coords[first_node])
    for i in range(1, len(route)):
        prev_node = route[i - 1] + 1
        curr_node = route[i] + 1
        length += rounded_dist(coords[prev_node], coords[curr_node])
    last_node = route[-1] + 1
    length += rounded_dist(coords[last_node], coords[depot])
    return length


def annotate_route(
    route: List[int],
    coords: Dict[int, Tuple[float, float]],
    energy_capacity: Optional[float],
    energy_consumption: Optional[float],
    station_indices: Set[int],
    vehicle_capacity: Optional[float],
    demands: Dict[int, float],
) -> str:
    parts = []
    depot = 1
    depot_x, depot_y = coords.get(depot, (float("nan"), float("nan")))
    soc = energy_capacity
    load = 0.0
    if demands:
        for node in route:
            node_id = node + 1
            load += demands.get(node_id, 0.0)
    if energy_capacity is None or energy_consumption is None:
        parts.append(f"{depot}({depot_x:.2f},{depot_y:.2f})[NA]")
    else:
        parts.append(f"{depot}({depot_x:.2f},{depot_y:.2f})[{soc:.2f}]")

    for idx, node in enumerate(route):
        node_id = node + 1
        x, y = coords.get(node_id, (float("nan"), float("nan")))
        if energy_capacity is None or energy_consumption is None or vehicle_capacity is None:
            parts.append(f"{node_id}({x:.2f},{y:.2f})[NA]")
        else:
            prev_id = depot if idx == 0 else route[idx - 1] + 1
            distance = rounded_dist(coords[prev_id], coords[node_id])
            soc = soc - rounded_energy(distance, energy_consumption, load, vehicle_capacity)
            if node_id == depot or node_id in station_indices:
                soc = energy_capacity
            parts.append(f"{node_id}({x:.2f},{y:.2f})[{soc:.2f}]")
            if node_id in demands:
                load -= demands[node_id]

    if energy_capacity is None or energy_consumption is None or vehicle_capacity is None:
        parts.append(f"{depot}({depot_x:.2f},{depot_y:.2f})[NA]")
    else:
        if route:
            last_node = route[-1] + 1
            distance = rounded_dist(coords[last_node], coords[depot])
            soc = soc - rounded_energy(distance, energy_consumption, load, vehicle_capacity)
        soc = energy_capacity
        parts.append(f"{depot}({depot_x:.2f},{depot_y:.2f})[{soc:.2f}]")

    return " ".join(parts)


def main(argv: List[str]) -> int:
    if len(argv) != 4:
        print("Usage: python3 describe_solution.py <solution.sol> <instance.vrp|instance.evrp> <output.txt>")
        return 1
    sol_path, inst_path, out_path = argv[1], argv[2], argv[3]

    coords = parse_instance_coords(inst_path)
    energy_capacity, energy_consumption = parse_energy_params(inst_path)
    station_indices = parse_station_indices(inst_path)
    vehicle_capacity, demands = parse_capacity_and_demands(inst_path)
    routes, reported_cost = parse_solution_routes(sol_path)

    total_len = 0.0
    lines: List[str] = []
    lines.append(f"Solution file: {sol_path}")
    lines.append(f"Instance file: {inst_path}")
    if reported_cost is not None:
        lines.append(f"Reported Cost: {reported_cost:.2f}")
    lines.append("")

    for idx, r in enumerate(routes, start=1):
        length = route_length(r, coords)
        total_len += length
        lines.append(f"Route #{idx} length: {length:.2f}")
        lines.append(
            annotate_route(
                r,
                coords,
                energy_capacity,
                energy_consumption,
                station_indices,
                vehicle_capacity,
                demands,
            )
        )
        lines.append("")

    lines.append(f"Total length (computed): {total_len:.2f}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote detailed solution to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
