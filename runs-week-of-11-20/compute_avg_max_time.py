#!/usr/bin/env python3
"""
compute_avg_max_time.py

Traverse the runs-week-of-11-20 directory, locate *_stats.csv files for each
instance/thread subdirectory (ignoring 16-thread runs), and compute the average
of the per-file maximum "Time" values for each subdirectory.

Usage:
    python3 compute_avg_max_time.py [--root runs-week-of-11-20]

Output is a table printed to stdout with columns:
    instance, threads, num_files, avg_max_time
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Column header holding per-iteration time measurements.
TIME_HEADER = "Time"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute average max time per subdirectory")
    parser.add_argument(
        "--root",
        default="runs-week-of-11-20",
        help="Root directory containing instance subdirectories",
    )
    return parser.parse_args()


def collect_stats(root: Path) -> Dict[Tuple[str, str], List[float]]:
    stats: Dict[Tuple[str, str], List[float]] = {}

    thread_dirs: List[Tuple[str, Path]] = []
    for instance_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for thread_dir in sorted(p for p in instance_dir.iterdir() if p.is_dir()):
            if thread_dir.name.startswith("16-threads"):
                continue
            thread_dirs.append((instance_dir.name, thread_dir))

    total = len(thread_dirs)
    for idx, (instance_name, thread_dir) in enumerate(thread_dirs, start=1):
        key = (instance_name, thread_dir.name)
        csv_files = sorted(thread_dir.glob("*_stats.csv"))
        subdir_values: List[float] = []
        for csv_path in csv_files:
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if TIME_HEADER not in reader.fieldnames:
                    raise ValueError(
                        f"Missing '{TIME_HEADER}' column in {csv_path}"
                    )
                max_time = None
                for row in reader:
                    try:
                        value = float(row[TIME_HEADER])
                    except ValueError as exc:
                        raise ValueError(
                            f"Invalid time value '{row[TIME_HEADER]}' in {csv_path}"
                        ) from exc
                    if max_time is None or value > max_time:
                        max_time = value
                if max_time is not None:
                    subdir_values.append(max_time)
        if subdir_values:
            stats[key] = subdir_values
        print(
            f"[{idx}/{total}] {instance_name}/{thread_dir.name}: processed {len(csv_files)} files",
            file=sys.stderr,
            flush=True,
        )
    return stats


def print_report(stats: Dict[Tuple[str, str], List[float]]) -> None:
    header = ["Instance", "Threads", "Num Stats", "Avg Max Time"]
    print("\t".join(header))
    for (instance, threads), values in sorted(stats.items()):
        count = len(values)
        avg = sum(values) / count if count else 0.0
        print(f"{instance}\t{threads}\t{count}\t{avg:.2f}")


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    if not root.is_dir():
        raise FileNotFoundError(f"Root directory not found: {root}")

    stats = collect_stats(root)
    if not stats:
        print("No stats found.")
        return

    print_report(stats)


if __name__ == "__main__":
    main()
