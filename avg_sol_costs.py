#!/usr/bin/env python3
"""
avg_sol_costs.py

Purpose:
    Traverse an Experiments directory containing subdirectories named like 'n106', 'n289', etc.
    For each nXXX directory, iterate its immediate subdirectories (e.g., '1-thread', '2-threads')
    and compute the average cost from any '.sol' files found in that subdirectory.

    Each .sol file is expected to contain a line of the form 'Cost X' (typically the last line).

How to run (Python 3):
    python3 avg_sol_costs.py <experiments_root> [output_txt]

    <experiments_root> : Path to the Experiments directory containing 'nXXX' directories.
    [output_txt]       : Optional path to write a summary text file. If omitted, results are printed only.

Output:
    Prints a readable summary to stdout. If 'output_txt' is supplied, also writes the summary there.

Example:
    python3 avg_sol_costs.py Experiments
    python3 avg_sol_costs.py Experiments /tmp/avg_costs.txt
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
import statistics

def iter_n_dirs(root: str) -> List[str]:
    """Return absolute paths to immediate subdirectories whose names match 'n<digits>'."""
    result: List[str] = []
    try:
        for name in os.listdir(root):
            full = os.path.join(root, name)
            if os.path.isdir(full) and name.startswith('n') and name[1:].isdigit():
                result.append(full)
    except OSError as e:
        print(f"Error reading root directory '{root}': {e}")
    return sorted(result)

def extract_cost_from_sol(sol_path: str) -> Optional[float]:
    """Read a .sol file and parse the last 'Cost X' line as float X.
    Returns None if not found or parsing fails.
    """
    try:
        with open(sol_path, 'r', encoding='utf-8', errors='ignore') as fh:
            lines = fh.readlines()
        for line in reversed(lines):
            s = line.strip()
            if s.startswith('Cost'):
                parts = s.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[1])
                    except ValueError:
                        return None
        return None
    except OSError as e:
        print(f"Could not open '{sol_path}': {e}")
        return None

def list_subdirs(path: str) -> List[str]:
    """Return absolute paths to immediate subdirectories of path."""
    result: List[str] = []
    try:
        for name in os.listdir(path):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                result.append(full)
    except OSError as e:
        print(f"Error reading directory '{path}': {e}")
    return sorted(result)

def list_sol_files(root: str) -> List[str]:
    """Recursively collect all .sol files under root."""
    matches: List[str] = []
    for current_root, _, files in os.walk(root):
        for f in files:
            if f.endswith('.sol'):
                matches.append(os.path.join(current_root, f))
    return matches

def compute_avg_cost(sol_files: List[str]) -> Tuple[int, Optional[float]]:
    """Compute average cost across .sol files. Returns (count, avg_cost_or_None)."""
    costs: List[float] = []
    for path in sol_files:
        cost = extract_cost_from_sol(path)
        if cost is not None:
            costs.append(cost)
    if not costs:
        return (0, None)
    return (len(costs), statistics.mean(costs))

def gather_averages(root: str) -> Dict[str, Dict[str, Tuple[int, Optional[float]]]]:
    """Return mapping: n_dir_name -> subdir_name -> (count, avg_cost)."""
    summary: Dict[str, Dict[str, Tuple[int, Optional[float]]]] = {}
    for nd in iter_n_dirs(root):
        nd_name = os.path.basename(nd)
        summary[nd_name] = {}
        for subdir in list_subdirs(nd):
            subdir_name = os.path.basename(subdir)
            sol_files = list_sol_files(subdir)
            count, avg = compute_avg_cost(sol_files)
            summary[nd_name][subdir_name] = (count, avg)
    return summary

def format_summary(summary: Dict[str, Dict[str, Tuple[int, Optional[float]]]]) -> str:
    lines: List[str] = []
    lines.append("Average Cost per Subdirectory")
    for nd_name in sorted(summary.keys(), key=lambda s: int(s[1:]) if s.startswith('n') and s[1:].isdigit() else s):
        lines.append(f"Directory: {nd_name}")
        for subdir_name in sorted(summary[nd_name].keys()):
            count, avg = summary[nd_name][subdir_name]
            avg_text = "NA" if avg is None else f"{avg:.2f}"
            lines.append(f"  {subdir_name}: files={count}, avg_cost={avg_text}")
        lines.append("")
    return "\n".join(lines)

def write_output(path: str, content: str) -> None:
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(content + "\n")
        print(f"Summary written to {path}")
    except OSError as e:
        print(f"Failed to write output file '{path}': {e}")

def main(argv: List[str]) -> int:
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python3 avg_sol_costs.py <experiments_root> [output_txt]")
        return 1
    root = argv[1]
    out = argv[2] if len(argv) == 3 else None
    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory")
        return 1
    summary = gather_averages(root)
    report = format_summary(summary)
    print(report)
    if out:
        write_output(out, report)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
