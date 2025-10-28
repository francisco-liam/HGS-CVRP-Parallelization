import os
import re
import math
from scipy.stats import ttest_ind

def extract_costs(directory):
    costs = []
    file_count = 0

    # Traverse the specified directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sol"):
                file_count += 1
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")  # Debug statement
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:  # Process lines in normal order
                        match = re.search(r"Cost\s+([\d.]+)", line)  # Updated regex to match 'Cost X'
                        if match:
                            cost = float(match.group(1))
                            print(f"Found cost: {cost}")  # Debug statement
                            costs.append(cost)
                            break  # Stop after finding the cost

    return costs, file_count

def calculate_stats(costs):
    if not costs:
        return 0, 0  # Return 0 for both avg and stddev if no costs are found
    avg = sum(costs) / len(costs)
    variance = sum((x - avg) ** 2 for x in costs) / len(costs)
    stddev = math.sqrt(variance)
    return avg, stddev

def analyze_costs(subdir):
    # Paths for "1-thread" and "2-threads"
    one_thread_dir = os.path.join(subdir, "1-thread")
    two_threads_dir = os.path.join(subdir, "2-threads")

    # Extract costs and file counts
    one_thread_costs, one_thread_count = extract_costs(one_thread_dir)
    two_threads_costs, two_threads_count = extract_costs(two_threads_dir)

    # Calculate statistics
    one_thread_avg, one_thread_stddev = calculate_stats(one_thread_costs)
    two_threads_avg, two_threads_stddev = calculate_stats(two_threads_costs)

    # Perform t-test
    if one_thread_costs and two_threads_costs:
        t_stat, p_value = ttest_ind(two_threads_costs, one_thread_costs, equal_var=False)
    else:
        t_stat, p_value = None, None

    # Report results
    print(f"1-thread: {one_thread_count} files")
    print(f"  Average Cost: {one_thread_avg:.2f}")
    print(f"  Standard Deviation: {one_thread_stddev:.2f}")
    print()
    print(f"2-threads: {two_threads_count} files")
    print(f"  Average Cost: {two_threads_avg:.2f}")
    print(f"  Standard Deviation: {two_threads_stddev:.2f}")
    print()

    if t_stat is not None and p_value is not None:
        print(f"T-test Results:")
        print(f"  T-statistic: {t_stat:.2f}")
        print(f"  P-value: {p_value:.4f}")
        if p_value < 0.05:
            print("  The results are statistically significant (p < 0.05).")
        else:
            print("  The results are not statistically significant (p >= 0.05).")
    else:
        print("T-test could not be performed due to insufficient data.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <subdirectory>")
    else:
        subdir = sys.argv[1]
        if os.path.isdir(subdir):
            analyze_costs(subdir)
        else:
            print("Invalid subdirectory. Please provide a valid path.")