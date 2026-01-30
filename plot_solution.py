#!/usr/bin/env python3
"""
plot_solution.py

Plot CVRP solution routes for a CVRPLIB instance given a matching .sol file.

Example:
    python3 plot_solution.py \
        --vrp Instances/CVRP/X-n106-k14.vrp \
        --sol runs-week-of-11-20/n106/2-threads/106-2-1.sol \
        --title "X-n106-k14, 2 threads"

The .sol format is expected to omit the depot node (assumed to be 1 in the .vrp
file), so route node indices are incremented by one when mapping to coordinates.
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


def read_vrp_coordinates(vrp_path: Path) -> Dict[int, Tuple[float, float]]:
    coords: Dict[int, Tuple[float, float]] = {}
    in_coord_section = False
    with vrp_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            upper = line.upper()
            if upper.startswith("NODE_COORD_SECTION"):
                in_coord_section = True
                continue
            if upper.startswith("DEMAND_SECTION"):
                break
            if not in_coord_section:
                continue
            parts = line.split()
            if len(parts) < 3:
                raise ValueError(f"Invalid coordinate line: {line}")
            node_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            coords[node_id] = (x, y)
    if not coords:
        raise ValueError(f"No coordinates found in {vrp_path}")
    return coords


def read_solution_routes(sol_path: Path) -> List[List[int]]:
    routes: List[List[int]] = []
    with sol_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or not line.lower().startswith("route"):
                continue
            _, route_data = line.split(":", 1)
            node_tokens = route_data.strip().split()
            if not node_tokens:
                continue
            route = [int(token) + 1 for token in node_tokens]
            routes.append(route)
    if not routes:
        raise ValueError(f"No routes parsed from {sol_path}")
    return routes


def plot_routes(coords: Dict[int, Tuple[float, float]], routes: List[List[int]], out_path: Path, show: bool, title: str) -> None:
    depot_id = 1
    if depot_id not in coords:
        raise ValueError("Depot node 1 not found in coordinates")

    xs = [c[0] for c in coords.values()]
    ys = [c[1] for c in coords.values()]

    plt.figure(figsize=(10, 8))
    plt.scatter(xs, ys, s=30, c="#444444", label="Customers")
    depot_x, depot_y = coords[depot_id]
    plt.scatter([depot_x], [depot_y], s=120, c="#d62728", marker="*", label="Depot")

    color_cycle = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    for idx, route in enumerate(routes, start=1):
        node_ids = [depot_id] + route + [depot_id]
        route_x = [coords[n][0] for n in node_ids]
        route_y = [coords[n][1] for n in node_ids]
        color = color_cycle[(idx - 1) % len(color_cycle)] if color_cycle else None
        plt.plot(route_x, route_y, linewidth=1.8, marker="o", markersize=4, label=f"Route {idx}", color=color)

    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    if show:
        plt.show()
    plt.close()


def infer_output_path(sol_path: Path) -> Path:
    target_dir = Path("solution_plots")
    return target_dir / sol_path.with_suffix(".png").name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot CVRP solution routes from a .sol file")
    parser.add_argument("--vrp", required=True, help="Path to the CVRPLIB .vrp instance file")
    parser.add_argument("--sol", required=True, help="Path to the corresponding solution .sol file")
    parser.add_argument("--out", help="Output PNG path (default: solution_plots/<sol_name>.png)")
    parser.add_argument("--title", default="CVRP Solution Routes", help="Plot title")
    parser.add_argument("--show", action="store_true", help="Display the plot interactively after saving")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    vrp_path = Path(args.vrp)
    sol_path = Path(args.sol)
    if not vrp_path.is_file():
        raise FileNotFoundError(f"Missing VRP file: {vrp_path}")
    if not sol_path.is_file():
        raise FileNotFoundError(f"Missing solution file: {sol_path}")

    coords = read_vrp_coordinates(vrp_path)
    routes = read_solution_routes(sol_path)

    out_path = Path(args.out) if args.out else infer_output_path(sol_path)
    plot_routes(coords, routes, out_path, args.show, args.title)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    main()
