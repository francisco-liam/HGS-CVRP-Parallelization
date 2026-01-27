#!/usr/bin/env python3
"""
plot_speedups.py

Purpose:
    Plot Speedup vs Threads for each CVRP instance using provided speedup data.
    Generates one PNG per instance and optionally a combined grid figure.

How to run (Python 3 with matplotlib installed):
    python3 plot_speedups.py [--outdir OUTPUT_DIR] [--show]

    --outdir OUTPUT_DIR : Directory to save PNGs (default: ./speedup_plots)
    --show              : Show plots interactively after saving

Install matplotlib if needed:
    python3 -m pip install matplotlib
"""

import os
import argparse
import csv
import matplotlib.pyplot as plt

def load_speedup_csv(csv_path: str) -> tuple[list[int], dict[str, list[float]]]:
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV is empty: {csv_path}")

    header = [h.strip() for h in rows[0]]
    if len(header) < 2 or header[0].lower() != "subdirectory":
        raise ValueError("CSV header must start with 'Subdirectory'")

    threads: list[int] = []
    for col in header[1:]:
        label = col.strip().lower()
        if label.endswith("-threads"):
            label = label[:-8]
        threads.append(int(label))

    data: dict[str, list[float]] = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        instance = row[0].strip()
        values = [float(x) for x in row[1:1 + len(threads)]]
        if len(values) != len(threads):
            raise ValueError(f"Row for {instance} has {len(values)} values, expected {len(threads)}")
        data[instance] = values

    return threads, data

def plot_instance(instance: str, speedups: list[float], threads: list[int], outdir: str):
    plt.figure(figsize=(6, 4))
    plt.plot(threads, speedups, marker="o", linewidth=2, color="#1f77b4")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.title(f"Speedup vs Threads: {instance}")
    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.xticks(threads)
    # Optionally add a near-linear scaling reference line passing through 2-thread point
    # linear_ref = [speedups[0] * (t / threads[0]) for t in threads]
    # plt.plot(threads, linear_ref, linestyle=":", color="#ff7f0e", label="Linear ref")
    # plt.legend()
    fname = f"speedup_{instance}.png".replace("/", "-")
    outpath = os.path.join(outdir, fname)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved {outpath}")

def plot_grid(threads: list[int], data: dict[str, list[float]], outdir: str):
    # Combined grid view for quick comparison (optional)
    rows = 2
    cols = 5
    fig, axes = plt.subplots(rows, cols, figsize=(18, 7), sharex=True, sharey=True)
    axes = axes.flatten()
    for ax, (instance, speedups) in zip(axes, data.items()):
        ax.plot(threads, speedups, marker="o", linewidth=2, color="#1f77b4")
        ax.set_title(instance, fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_xticks(threads)
    for ax in axes:
        ax.set_xlabel("Threads")
        ax.set_ylabel("Speedup")
    fig.suptitle("Speedup vs Threads (All Instances)", fontsize=12)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    grid_path = os.path.join(outdir, "speedup_all_instances.png")
    fig.savefig(grid_path, dpi=150)
    plt.close(fig)
    print(f"Saved {grid_path}")

def main():
    parser = argparse.ArgumentParser(description="Plot speedup vs threads per instance.")
    parser.add_argument("--csv", default=os.path.join("Experiments", "speedup_results.csv"),
                        help="CSV file with speedup results")
    parser.add_argument("--outdir", default="speedup_plots", help="Output directory for PNGs")
    parser.add_argument("--show", action="store_true", help="Show plots after saving")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    threads, data = load_speedup_csv(args.csv)

    # Save individual plots
    for instance, speedups in data.items():
        plot_instance(instance, speedups, threads, args.outdir)

    # Combined grid view
    plot_grid(threads, data, args.outdir)

    # Single combined plot: all instances overlaid on same axes
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    for idx, (instance, speedups) in enumerate(data.items()):
        color = color_cycle[idx % len(color_cycle)] if color_cycle else None
        plt.plot(threads, speedups, marker="o", linewidth=2, label=instance, color=color)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.title("Speedup vs Threads (All Instances Overlaid)")
    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.xticks(threads)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    combined_path = os.path.join(args.outdir, "speedup_all_overlaid.png")
    plt.savefig(combined_path, dpi=150)
    plt.close()
    print(f"Saved {combined_path}")

    if args.show:
        # If you want interactive display for individual plots, re-plot one example
        # Otherwise rely on saved files.
        import matplotlib.pyplot as plt
        for instance, speedups in data.items():
            plt.figure(figsize=(6, 4))
            plt.plot(threads, speedups, marker="o", linewidth=2)
            plt.title(f"Speedup vs Threads: {instance}")
            plt.xlabel("Threads")
            plt.ylabel("Speedup")
            plt.xticks(threads)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()