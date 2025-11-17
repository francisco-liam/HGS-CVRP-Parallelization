#!/usr/bin/env python3
"""
collect_stats_summary.py

Purpose:
    Scan a root directory for subdirectories whose names match the pattern n<digits>
    (e.g. n106, n289, n359, ...) and, inside each of those, look for a subdirectory
    named '1-thread'. Within each '1-thread' directory, recursively find every file
    whose name ends with 'stats.csv'. For each top-level n<digits> directory:
        - Count how many such stats.csv files were found.
        - For every stats.csv file found, count the number of data lines (excluding
          the header line). A header is assumed to be the first line; it's excluded
          from the line count regardless of content.

Output:
    A plain-text summary file listing, for each n<digits> directory:
        Directory: nXXX
          Files found: <count>
          <file_rel_path_1>: <num_data_lines>
          <file_rel_path_2>: <num_data_lines>
          ...
    If a directory has zero stats.csv files, it will still appear with Files found: 0.

How to run:
    python3 collect_stats_summary.py <root_path> [output_txt]

    <root_path>  : Path that contains directories like n106, n289, etc.
    [output_txt] : Optional path/name for the output summary text file.
                   Defaults to 'stats_summary.txt' in the current working directory.

Examples:
    python3 collect_stats_summary.py /path/to/HGS-CVRP-Parallelization
    python3 collect_stats_summary.py /path/to/HGS-CVRP-Parallelization /tmp/summary.txt

Notes:
    - The script is read-only; it does not modify any CSV files.
    - Lines are counted robustly; empty lines at end of file are ignored automatically.
    - If a CSV is empty or only has a header, its data line count will be 0.
"""

import os
import sys
from typing import Dict, List, Tuple

def find_n_directories(root: str) -> List[str]:
    """Return absolute paths to subdirectories of root matching pattern n<digits>."""
    result = []
    try:
        for name in os.listdir(root):
            full = os.path.join(root, name)
            if os.path.isdir(full) and name.startswith('n') and name[1:].isdigit():
                result.append(full)
    except OSError as e:
        print(f"Error reading root directory '{root}': {e}")
    return sorted(result)

def list_stats_files(one_thread_dir: str) -> List[str]:
    """Recursively collect all files ending with stats.csv under one_thread_dir."""
    matches: List[str] = []
    for current_root, _, files in os.walk(one_thread_dir):
        for f in files:
            if f.endswith('stats.csv'):
                matches.append(os.path.join(current_root, f))
    return matches

def count_data_lines(csv_path: str) -> int:
    """Return number of data lines (excluding header) in csv_path.
    Treat the first line as header if present, regardless of content.
    """
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as fh:
            lines = fh.readlines()
        if not lines:
            return 0
        # Exclude the first line (header) and count remaining non-empty lines
        data_lines = [ln for ln in lines[1:] if ln.strip()]
        return len(data_lines)
    except OSError as e:
        print(f"Could not open '{csv_path}': {e}")
        return 0

def gather_stats(root: str) -> Dict[str, List[Tuple[str, int]]]:
    """For each n<digits> directory: gather (file_path, data_line_count)."""
    summary: Dict[str, List[Tuple[str, int]]] = {}
    n_dirs = find_n_directories(root)
    for nd in n_dirs:
        one_thread = os.path.join(nd, '1-thread')
        file_info: List[Tuple[str, int]] = []
        if os.path.isdir(one_thread):
            stats_files = list_stats_files(one_thread)
            for f in stats_files:
                count = count_data_lines(f)
                # Store path relative to the n<digits> directory for readability
                rel_path = os.path.relpath(f, nd)
                file_info.append((rel_path, count))
        summary[nd] = file_info
    return summary

def write_summary(summary: Dict[str, List[Tuple[str, int]]], output_path: str) -> None:
    """Write the summary to a text file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write("Stats CSV Summary\n")
            out.write(f"Root scanned: {os.path.abspath(os.path.dirname(list(summary.keys())[0])) if summary else 'N/A'}\n\n")
            for nd, files in summary.items():
                dir_name = os.path.basename(nd)
                out.write(f"Directory: {dir_name}\n")
                out.write(f"  Files found: {len(files)}\n")
                for rel_path, line_count in files:
                    out.write(f"  {rel_path}: {line_count} data lines\n")
                out.write("\n")
        print(f"Summary written to {output_path}")
    except OSError as e:
        print(f"Failed to write summary file '{output_path}': {e}")

def main(argv: List[str]) -> int:
    if len(argv) < 2 or len(argv) > 3:
        print("Usage: python3 collect_stats_summary.py <root_path> [output_txt]")
        return 1

    root = argv[1]
    output_path = argv[2] if len(argv) == 3 else 'stats_summary.txt'

    if not os.path.isdir(root):
        print(f"Error: root path '{root}' is not a directory.")
        return 1

    summary = gather_stats(root)
    write_summary(summary, output_path)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
