import os
import csv

# Function to calculate the average max time for each subdirectory
def calculate_avg_max_time(base_dir, directories):
    results = {}

    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"Processing directory: {directory}")  # Report progress

            results[directory] = {"2-threads": None, "4-threads": None, "8-threads": None, "16-threads-1-24": None}

            for subdir in os.listdir(dir_path):
                subdir_path = os.path.join(dir_path, subdir)

                if os.path.isdir(subdir_path) and subdir in results[directory]:
                    print(f"  Scanning subdirectory: {subdir}")  # Report progress

                    max_times = []  # Store max time from each stats.csv file

                    for file_name in os.listdir(subdir_path):
                        if file_name.endswith("stats.csv"):
                            file_path = os.path.join(subdir_path, file_name)
                            print(f"    Reading file: {file_name}")  # Report progress

                            with open(file_path, "r") as csv_file:
                                reader = csv.reader(csv_file)
                                
                                # Skip the header row
                                header = next(reader, None)

                                file_max_time = None
                                for row in reader:
                                    try:
                                        time_value = float(row[-1])  # Last column is time
                                        if file_max_time is None or time_value > file_max_time:
                                            file_max_time = time_value
                                    except ValueError:
                                        print(f"Invalid time value in file {file_path}: {row[-1]}")

                                if file_max_time is not None:
                                    max_times.append(file_max_time)

                    if max_times:
                        avg_max_time = sum(max_times) / len(max_times)  # Average of max times across files
                        x_value = int(directory[1:])  # Extract X from directory name (e.g., n106 -> 106)
                        speedup = ((x_value - 1) * 240 / 100) / avg_max_time  # Reciprocal of the original formula
                        results[directory][subdir] = speedup
                    else:
                        print(f"No valid stats.csv files found in {subdir_path}")

    return results

# Write results to a .txt file
def write_results_to_file(results, output_file):
    def fmt(val):
        return f"{val:.2f}" if val is not None else "N/A"

    with open(output_file, "w") as f:
        f.write("Subdirectory\t2-threads\t4-threads\t8-threads\t16-threads-1-24\n")
        for directory, subdir_results in results.items():
            two = fmt(subdir_results.get('2-threads'))
            four = fmt(subdir_results.get('4-threads'))
            eight = fmt(subdir_results.get('8-threads'))
            sixteen = fmt(subdir_results.get('16-threads-1-24'))
            f.write(f"{directory}\t{two}\t{four}\t{eight}\t{sixteen}\n")

def write_results_to_csv(results, output_file_csv):
    import csv as _csv
    header = ["Subdirectory", "2-threads", "4-threads", "8-threads", "16-threads-1-24"]

    def fmt_number(val):
        return f"{val:.2f}" if val is not None else ""

    with open(output_file_csv, "w", newline="") as f:
        writer = _csv.writer(f)
        writer.writerow(header)
        for directory, subdir_results in results.items():
            row = [
                directory,
                fmt_number(subdir_results.get("2-threads")),
                fmt_number(subdir_results.get("4-threads")),
                fmt_number(subdir_results.get("8-threads")),
                fmt_number(subdir_results.get("16-threads-1-24")),
            ]
            writer.writerow(row)

# Define the base directory and the list of directories to check
base_dir = os.getcwd()
directories = ["n106", "n289", "n359", "n491", "n573", "n627", "n783", "n895", "n936", "n1001"]

# Calculate the average max time and speedup
results = calculate_avg_max_time(base_dir, directories)

# Write the results to a .txt file
output_file = os.path.join(base_dir, "speedup_results_new.txt")
write_results_to_file(results, output_file)

# Also write a CSV for easy pasting into Google Slides/Sheets
output_file_csv = os.path.join(base_dir, "speedup_results_new.csv")
write_results_to_csv(results, output_file_csv)

print(f"Speedup results written to {output_file} and {output_file_csv}")