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
import matplotlib.pyplot as plt

# Threads used across all instances
THREADS = [2, 4, 8, 16]

# Speedup data per instance
DATA = {
    "X-n106-k14":   [1.9,  3.43, 5.68, 5.48],
    "X-n289-k60":   [1.97, 3.75, 6.74, 7.18],
    "X-n359-k29":   [1.93, 3.74, 7.08, 8.33],
    "X-n491-k59":   [1.91, 3.63, 6.56, 7.16],
    "X-n573-k30":   [1.96, 3.81, 7.15, 8.83],
    "X-n627-k43":   [1.98, 3.79, 6.93, 8.60],
    "X-n783-k48":   [2.35, 4.48, 8.02, 9.78],
    "X-n895-k37":   [2.47, 4.55, 8.16, 9.88],
    "X-n936-k151":  [2.52, 4.51, 7.40, 8.46],
    "X-n1001-k43":  [2.32, 4.50, 7.91, 9.51],
}

def plot_instance(instance: str, speedups: list[float], outdir: str):
    plt.figure(figsize=(6, 4))
    plt.plot(THREADS, speedups, marker="o", linewidth=2, color="#1f77b4")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.title(f"Speedup vs Threads: {instance}")
    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.xticks(THREADS)
    # Optionally add a near-linear scaling reference line passing through 2-thread point
    # linear_ref = [speedups[0] * (t / 2) for t in THREADS]
    # plt.plot(THREADS, linear_ref, linestyle=":", color="#ff7f0e", label="Linear ref")
    # plt.legend()
    fname = f"speedup_{instance}.png".replace("/", "-")
    outpath = os.path.join(outdir, fname)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved {outpath}")

def plot_grid(outdir: str):
    # Combined grid view for quick comparison (optional)
    rows = 2
    cols = 5
    fig, axes = plt.subplots(rows, cols, figsize=(18, 7), sharex=True, sharey=True)
    axes = axes.flatten()
    for ax, (instance, speedups) in zip(axes, DATA.items()):
        ax.plot(THREADS, speedups, marker="o", linewidth=2, color="#1f77b4")
        ax.set_title(instance, fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_xticks(THREADS)
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
    parser.add_argument("--outdir", default="speedup_plots", help="Output directory for PNGs")
    parser.add_argument("--show", action="store_true", help="Show plots after saving")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Save individual plots
    for instance, speedups in DATA.items():
        plot_instance(instance, speedups, args.outdir)

    # Combined grid view
    plot_grid(args.outdir)

    # Single combined plot: all instances overlaid on same axes
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    color_cycle = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    for idx, (instance, speedups) in enumerate(DATA.items()):
        color = color_cycle[idx % len(color_cycle)] if color_cycle else None
        plt.plot(THREADS, speedups, marker="o", linewidth=2, label=instance, color=color)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.title("Speedup vs Threads (All Instances Overlaid)")
    plt.xlabel("Threads")
    plt.ylabel("Speedup")
    plt.xticks(THREADS)
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
        for instance, speedups in DATA.items():
            plt.figure(figsize=(6, 4))
            plt.plot(THREADS, speedups, marker="o", linewidth=2)
            plt.title(f"Speedup vs Threads: {instance}")
            plt.xlabel("Threads")
            plt.ylabel("Speedup")
            plt.xticks(THREADS)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    main()