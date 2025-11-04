import os
import csv
import sys

def find_csv_stats(directory, y):
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        return

    # Collect all CSV files ending with "stats.csv"
    csv_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("stats.csv"):
                csv_files.append(os.path.join(root, file))

    num_csvs = len(csv_files)
    print(f"Number of CSV files ending with 'stats.csv': {num_csvs}")

    if num_csvs == 0:
        print("No CSV files found. Exiting.")
        return

    # Calculate the average of the highest values in column 4
    total_time = 0
    total_lines = 0  # Total number of lines across all stats.csv files
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header if it exists
                max_time = max(float(row[3]) for row in reader if row[3].strip())
                total_time += max_time

                # Count the number of lines in the file (excluding the header)
                f.seek(0)  # Reset file pointer to the beginning
                total_lines += sum(1 for _ in reader) - 1  # Subtract 1 for the header
        except Exception as e:
            print(f"Error processing file {csv_file}: {e}")
            continue

    avg_time = total_time / num_csvs
    avg_lines = total_lines / num_csvs if num_csvs > 0 else 0  # Average number of lines
    print(f"Average of the highest values in column 4 (time): {avg_time:.2f}")
    print(f"Average number of lines in stats.csv files: {avg_lines:.2f}")

    # Find all .sol files and calculate the average cost
    sol_files = []
    total_cost = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sol"):
                sol_files.append(os.path.join(root, file))

    num_sol_files = len(sol_files)
    print(f"Number of .sol files: {num_sol_files}")

    if num_sol_files > 0:
        for sol_file in sol_files:
            try:
                with open(sol_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[::-1]:  # Read lines in reverse to find "Cost X" at the end
                        if line.startswith("Cost"):
                            cost = float(line.split()[1])
                            total_cost += cost
                            break
            except Exception as e:
                print(f"Error processing file {sol_file}: {e}")
                continue

        avg_cost = total_cost / num_sol_files
        print(f"Average cost from .sol files: {avg_cost:.2f}")

        # Calculate percent difference between Y and avg_cost
        percent_diff = ((avg_cost - y) / avg_cost) * 100
        print(f"Percent difference between {y} and average cost: {percent_diff:.2f}%")

    # Find the nearest parent directory starting with "nX"
    current_dir = os.path.abspath(directory)
    while current_dir != "/":
        dir_name = os.path.basename(current_dir)
        if dir_name.startswith("n"):
            try:
                # Extract the number X from "nX"
                X = int(dir_name[1:])  # Get everything after the "n"
                speed_up = (X * 240 / 100) / avg_time
                print(f"Speed-up for directory '{dir_name}': {speed_up:.2f}")
                return
            except (IndexError, ValueError):
                print(f"Skipping directory '{dir_name}' as it doesn't match the expected format.")
        current_dir = os.path.dirname(current_dir)

    print("No valid parent directory starting with 'nX' found.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python find_csv_stats.py <subdirectory> <Y>")
    else:
        try:
            y = float(sys.argv[2])
            find_csv_stats(sys.argv[1], y)
        except ValueError:
            print("Error: Y must be a numeric value.")