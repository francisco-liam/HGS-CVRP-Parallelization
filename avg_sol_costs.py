#!/usr/bin/env python3
"""
avg_sol_costs.py

Purpose:
    Traverse a runs directory (e.g., 'runs-week-of-11-20') that contains subdirectories
    named like 'n106', 'n289', etc. Inside each of those, there are thread subdirectories:
    '2-threads', '4-threads', '8-threads', '16-threads'. Each thread subdirectory contains
    one or more '.sol' files whose last line is of the form 'Cost X'.

    Instead of reporting average costs, this script computes, for each thread subdirectory,
    the average percent difference between the reported Cost X and a provided baseline
    value for that 'nXXX' directory:

        percent_diff = ((reported_cost - baseline_cost) / baseline_cost) * 100

How to run (Python 3):
    python3 avg_sol_costs.py <runs_root> [output_txt]

    <runs_root>  : Path to the root containing 'nXXX' directories (e.g., './runs-week-of-11-20').
    [output_txt] : Optional path to write a summary text file. If omitted, results are printed only.

Output:
    Prints a readable summary to stdout. If 'output_txt' is supplied, also writes the summary there.

Example:
    python3 avg_sol_costs.py runs-week-of-11-20
    python3 avg_sol_costs.py runs-week-of-11-20 /tmp/avg_percent_diff.txt
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
import math
import statistics
try:
    from scipy import stats as scipy_stats  # Optional: used for precise t-test p-values
except Exception:
    scipy_stats = None

# Baseline actual costs per n-directory (commas removed)
BASELINES: Dict[str, float] = {
    'n106': 26362.00,
    'n289': 95151.00,
    'n359': 51505.00,
    'n491': 66483.00,
    'n573': 50673.00,
    'n627': 62164.00,
    'n783': 72386.00,
    'n895': 53860.00,
    'n936': 132715.00,
    'n1001': 72355.00,
}

# Optional: 1-thread mean results per n-directory for significance testing (one-sample t-test)
ONE_THREAD_MEANS: Dict[str, float] = {
    'n106': 26377.3,
    'n289': 95270.5,
    'n359': 51616.9,
    'n491': 66606.8,
    'n573': 50775.3,
    'n627': 62332.6,
    'n783': 72782.5,
    'n895': 54084.0,
    'n936': 133373.5,
    'n1001': 72679.1,
}

THREAD_DIRS = ["2-threads", "4-threads", "8-threads", "16-threads"]

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

def compute_thread_avg_percent_diff(thread_dir: str, baseline: float) -> Tuple[int, Optional[float]]:
    """Compute average percent difference across all .sol files in thread_dir.
    percent_diff = ((reported_cost - baseline) / baseline) * 100
    Returns (count, avg_percent_diff_or_None).
    """
    diffs: List[float] = []
    try:
        for fname in os.listdir(thread_dir):
            if fname.endswith('.sol'):
                cost = extract_cost_from_sol(os.path.join(thread_dir, fname))
                if cost is not None:
                    # reported value is higher than actual; compute percent difference
                    diffs.append(((cost - baseline) / baseline) * 100.0)
    except OSError as e:
        print(f"Error listing '{thread_dir}': {e}")
    if not diffs:
        return (0, None)
    return (len(diffs), sum(diffs) / len(diffs))

def one_sample_t_test_less(sample: List[float], mu0: float) -> Optional[Tuple[float, float]]:
    """One-sample t-test (H1: mean < mu0). Returns (t_stat, p_value). None if sample too small.
    Uses scipy if available; otherwise computes t-stat and approximates p via survival function
    fallback (not as precise). Requires n >= 2 for variance.
    """
    n = len(sample)
    if n < 2:
        return None
    mean = statistics.mean(sample)
    stdev = statistics.pstdev(sample) if n == 1 else statistics.stdev(sample)
    if stdev == 0:
        # If no variance, t is undefined; if mean < mu0, p ~ 0, else p ~ 1
        t_stat = float('-inf') if mean < mu0 else float('inf')
        p_val = 0.0 if mean < mu0 else 1.0
        return (t_stat, p_val)
    t_stat = (mean - mu0) / (stdev / math.sqrt(n))
    # One-sided: P(T <= t_stat) with df = n-1
    df = n - 1
    if scipy_stats is not None:
        p_val = scipy_stats.t.cdf(t_stat, df)
        return (t_stat, float(p_val))
    # Fallback: approximate using standard normal for large df
    z = t_stat
    # Normal CDF approximation
    p_val = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return (t_stat, p_val)

def gather_averages(root: str) -> Dict[str, Dict[str, Tuple[int, Optional[float], Optional[float]]]]:
    """Return mapping: n_dir_name -> thread_dir_name -> (count, avg_percent_diff, p_value_improvement).
    p_value_improvement is from a one-sample t-test H1: mean_cost < one_thread_mean.
    """
    summary: Dict[str, Dict[str, Tuple[int, Optional[float], Optional[float]]]] = {}
    for nd in iter_n_dirs(root):
        nd_name = os.path.basename(nd)
        summary[nd_name] = {}
        baseline = BASELINES.get(nd_name)
        mu0 = ONE_THREAD_MEANS.get(nd_name)
        if baseline is None:
            # Unknown baseline; mark all threads as NA
            for tname in THREAD_DIRS:
                summary[nd_name][tname] = (0, None, None)
            continue
        for tname in THREAD_DIRS:
            tdir = os.path.join(nd, tname)
            if os.path.isdir(tdir):
                count, avg = compute_thread_avg_percent_diff(tdir, baseline)
                # Also collect raw costs for t-test vs 1-thread mean
                costs: List[float] = []
                try:
                    for fname in os.listdir(tdir):
                        if fname.endswith('.sol'):
                            c = extract_cost_from_sol(os.path.join(tdir, fname))
                            if c is not None:
                                costs.append(c)
                except OSError:
                    pass
                p_val: Optional[float] = None
                if mu0 is not None and len(costs) >= 2:
                    res = one_sample_t_test_less(costs, mu0)
                    if res is not None:
                        _, p_val = res
                summary[nd_name][tname] = (count, avg, p_val)
            else:
                summary[nd_name][tname] = (0, None, None)
    return summary

def format_summary(summary: Dict[str, Dict[str, Tuple[int, Optional[float], Optional[float]]]]) -> str:
    lines: List[str] = []
    lines.append("Average Percent Difference per Thread Directory + One-sample t-test vs 1-thread mean (improvement)")
    for nd_name in sorted(summary.keys(), key=lambda s: int(s[1:]) if s.startswith('n') and s[1:].isdigit() else s):
        # Also report 1-thread percent diff vs baseline for this directory
        baseline = BASELINES.get(nd_name)
        one_thread_mean = ONE_THREAD_MEANS.get(nd_name)
        if baseline is not None and one_thread_mean is not None and baseline != 0:
            one_thread_pct = ((one_thread_mean - baseline) / baseline) * 100.0
            header_extra = f" (1-thread percent diff: {one_thread_pct:.2f}%)"
        else:
            header_extra = ""
        lines.append(f"Directory: {nd_name}{header_extra}")
        for tname in THREAD_DIRS:
            count, avg, pval = summary[nd_name].get(tname, (0, None, None))
            avg_text = "NA" if avg is None else f"{avg:.2f}%"
            if pval is None:
                sig_text = "p=NA"
            else:
                sig_text = f"p={pval:.4f} {'(significant)' if pval < 0.05 else '(ns)'}"
            lines.append(f"  {tname}: files={count}, avg_percent_diff={avg_text}, t-test {sig_text}")
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
        print("Usage: python3 avg_sol_costs.py <runs_root> [output_txt]")
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
