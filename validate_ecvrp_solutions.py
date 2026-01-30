#!/usr/bin/env python3
"""
validate_ecvrp_solutions.py

Purpose:
    Traverse an Experiments directory and validate ECVRP solution files (.sol).
    For each nXXX subdirectory, the script finds the matching ECVRP instance file
    in Instances/ECVRP (e.g., *-n147-*.evrp), then checks every route in each .sol
    to ensure energy never drops below zero. Routes may include charging stations
    (node IDs listed in STATIONS_COORD_SECTION). The depot is node 1.

How to run (Python 3):
    python3 validate_ecvrp_solutions.py [experiments_root] [--instances INSTANCES_DIR] [--output OUT_TXT]

    experiments_root : Path to Experiments (default: ./Experiments)
    --instances      : Path to Instances/ECVRP (default: ./Instances/ECVRP)
    --output         : Optional path to write a report. If omitted, prints to stdout only.

Output:
    Summary report with any infeasible routes and per-file validation status.
"""

import argparse
import math
import os
import glob
from typing import Dict, List, Optional, Set, Tuple


def iter_n_dirs(root: str) -> List[str]:
    result: List[str] = []
    try:
        for name in os.listdir(root):
            full = os.path.join(root, name)
            if os.path.isdir(full) and name.startswith("n") and name[1:].isdigit():
                result.append(full)
    except OSError as e:
        print(f"Error reading root directory '{root}': {e}")
    return sorted(result)


def parse_instance_coords(path: str) -> Dict[int, Tuple[float, float]]:
    coords: Dict[int, Tuple[float, float]] = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = f.read().split()

    try:
        idx = tokens.index("NODE_COORD_SECTION") + 1
    except ValueError:
        raise ValueError("NODE_COORD_SECTION not found in instance file")

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


def parse_solution_routes(path: str) -> List[List[int]]:
    routes: List[List[int]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Route #"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    nodes = [int(x) for x in parts[1].strip().split() if x.strip()]
                    routes.append(nodes)
    return routes


def rounded_dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    d = math.hypot(a[0] - b[0], a[1] - b[1])
    return float(math.floor(d + 0.5))


def energy_cost(distance: float, consumption: float, load: float, capacity: float) -> float:
    rate = consumption
    if capacity > 0:
        rate += load / capacity
    return distance * rate


def map_solution_node_to_instance(node: int) -> int:
    """Map a solution node id to an instance node id.

    The solver outputs customer indices 1..nbClients and station indices
    in the same 1-based space *excluding the depot*. Instance files are
    1-based and include the depot as node 1, so we shift by +1.
    """
    return node + 1


def validate_route(
    route: List[int],
    coords: Dict[int, Tuple[float, float]],
    energy_capacity: float,
    energy_consumption: float,
    station_indices: Set[int],
    vehicle_capacity: float,
    demands: Dict[int, float],
) -> Tuple[bool, Optional[str]]:
    if energy_capacity <= 0 or energy_consumption <= 0:
        return False, "Missing or invalid energy parameters"

    soc = energy_capacity
    load_remaining = vehicle_capacity
    depot = 1
    prev = depot

    for raw_node in route:
        node = map_solution_node_to_instance(raw_node)
        if node not in coords:
            return False, f"Invalid node id {raw_node} (instance id {node})"
        dist = rounded_dist(coords[prev], coords[node])
        e = energy_cost(dist, energy_consumption, load_remaining, vehicle_capacity)
        if e > soc + 1e-9:
            return False, f"Energy below zero on arc {prev}->{node} (need {e:.2f}, have {soc:.2f})"
        soc -= e

        if node == depot or node in station_indices:
            soc = energy_capacity
        else:
            load_remaining -= demands.get(node, 0.0)
        prev = node

    # Return to depot
    dist = rounded_dist(coords[prev], coords[depot])
    e = energy_cost(dist, energy_consumption, load_remaining, vehicle_capacity)
    if e > soc + 1e-9:
        return False, f"Energy below zero on arc {prev}->{depot} (need {e:.2f}, have {soc:.2f})"

    return True, None


def find_instance_for_n(instances_root: str, n_name: str) -> Tuple[Optional[str], Optional[str]]:
    pattern = os.path.join(instances_root, f"*-{n_name}-*.evrp")
    matches = sorted(glob.glob(pattern))
    if not matches:
        return None, f"No instance found for {n_name} using pattern {pattern}"
    if len(matches) > 1:
        return None, f"Multiple instances found for {n_name}: {', '.join(os.path.basename(m) for m in matches)}"
    return matches[0], None


def collect_sol_files(root: str) -> List[str]:
    sol_files: List[str] = []
    for current_root, _, files in os.walk(root):
        for f in files:
            if f.endswith(".sol"):
                sol_files.append(os.path.join(current_root, f))
    return sorted(sol_files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ECVRP .sol files under Experiments.")
    parser.add_argument("experiments_root", nargs="?", default="Experiments")
    parser.add_argument("--instances", default=os.path.join("Instances", "ECVRP"))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    experiments_root = args.experiments_root
    instances_root = args.instances

    if not os.path.isdir(experiments_root):
        print(f"Error: '{experiments_root}' is not a directory")
        return 1
    if not os.path.isdir(instances_root):
        print(f"Error: '{instances_root}' is not a directory")
        return 1

    lines: List[str] = []
    total_files = 0
    total_invalid = 0

    for nd in iter_n_dirs(experiments_root):
        n_name = os.path.basename(nd)
        inst_path, inst_err = find_instance_for_n(instances_root, n_name)
        lines.append(f"Directory: {n_name}")
        if inst_err:
            lines.append(f"  Instance: ERROR - {inst_err}")
            lines.append("")
            continue

        coords = parse_instance_coords(inst_path)
        energy_capacity, energy_consumption = parse_energy_params(inst_path)
        station_indices = parse_station_indices(inst_path)
        vehicle_capacity, demands = parse_capacity_and_demands(inst_path)

        if energy_capacity is None or energy_consumption is None or vehicle_capacity is None:
            lines.append("  Instance: ERROR - Missing energy/capacity parameters")
            lines.append("")
            continue

        sol_files = collect_sol_files(nd)
        if not sol_files:
            lines.append("  No .sol files found")
            lines.append("")
            continue

        for sol_path in sol_files:
            total_files += 1
            routes = parse_solution_routes(sol_path)
            if not routes:
                lines.append(f"  {os.path.relpath(sol_path, experiments_root)}: ERROR - No routes found")
                total_invalid += 1
                continue

            file_valid = True
            for idx, route in enumerate(routes, start=1):
                ok, reason = validate_route(
                    route,
                    coords,
                    energy_capacity,
                    energy_consumption,
                    station_indices,
                    vehicle_capacity,
                    demands,
                )
                if not ok:
                    file_valid = False
                    total_invalid += 1
                    lines.append(
                        f"  {os.path.relpath(sol_path, experiments_root)}: INVALID (Route #{idx}) - {reason}"
                    )
                    break

            if file_valid:
                lines.append(f"  {os.path.relpath(sol_path, experiments_root)}: OK")

        lines.append("")

    summary = f"Checked {total_files} solution files. Invalid: {total_invalid}."
    lines.append(summary)

    report = "\n".join(lines)
    print(report)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report + "\n")
            print(f"Report written to {args.output}")
        except OSError as e:
            print(f"Failed to write report '{args.output}': {e}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
