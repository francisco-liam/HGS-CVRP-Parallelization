import os
import csv
import sys

def process_files(directory, target_iterations, comparison_factor):
    file_count = 0  # Counter for the number of files found
    total_time = 0  # Total time to reach the target iterations
    valid_files = 0  # Counter for files with valid data
    total_lowest_positive = 0  # Total of lowest positive values in column 2
    valid_lowest_positive_files = 0  # Counter for files with valid lowest positive values

    # Traverse the specified directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("stats.csv"):
                file_count += 1  # Increment the file counter
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Skip header if present
                    time_sum = 0
                    iteration_count = 0
                    lowest_positive = float('inf')  # Initialize to infinity

                    for row in reader:
                        try:
                            iterations = int(row[0])  # First column: iterations
                            value = float(row[1])  # Second column: value
                            time = float(row[3])  # Fourth column: time
                        except (ValueError, IndexError):
                            continue  # Skip rows with invalid data

                        if iterations <= target_iterations:
                            time_sum += time
                            iteration_count += 1

                            # Track the lowest positive value in column 2
                            if value > 0 and value < lowest_positive:
                                lowest_positive = value

                    if iteration_count > 0:
                        valid_files += 1
                        total_time += time_sum / iteration_count  # Average time for this file

                    if lowest_positive != float('inf'):
                        valid_lowest_positive_files += 1
                        total_lowest_positive += lowest_positive

    # Print the number of files found
    print(f"Number of files found: {file_count}")

    # Calculate and print the average time across all valid files
    avg_time = total_time / valid_files if valid_files > 0 else 0
    print(f"Average time to reach {target_iterations} iterations: {avg_time:.2f}")

    # Calculate and print the average lowest positive value in column 2
    avg_lowest_positive = total_lowest_positive / valid_lowest_positive_files if valid_lowest_positive_files > 0 else 0
    print(f"Average lowest positive value in column 2 before {target_iterations} iterations: {avg_lowest_positive:.2f}")

    # Calculate the comparison value and percentage difference
    comparison_value = comparison_factor * 240 / 100
    if comparison_value > 0:
        percentage_difference = ((comparison_value - avg_time) / comparison_value) * 100
        print(f"Comparison value (n * 240 / 100): {comparison_value:.2f}")
        print(f"Percentage difference: {percentage_difference:.2f}%")
    else:
        print("Invalid comparison factor provided.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <directory> <target_iterations> <comparison_factor>")
    else:
        directory = sys.argv[1]
        try:
            target_iterations = int(sys.argv[2])
            comparison_factor = float(sys.argv[3])
            process_files(directory, target_iterations, comparison_factor)
        except ValueError:
            print("Invalid input. Please provide valid numbers for target_iterations and comparison_factor.")