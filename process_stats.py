import os
import csv
import sys

def process_files(directory, reference_value=None):
    lowest_second_col_values = []
    first_col_values = []
    last_col_values = []
    file_count = 0  # Counter for the number of files found
    total_lines = 0  # Counter for the total number of lines (excluding headers)

    # Traverse the specified directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("stats.csv"):
                file_count += 1  # Increment the file counter
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Skip header if present
                    line_count = 0  # Counter for lines in the current file
                    lowest_row = None

                    for row in reader:
                        line_count += 1
                        try:
                            second_col = float(row[1])
                            fourth_col = float(row[3])
                        except (ValueError, IndexError):
                            continue  # Skip rows with invalid data

                        if second_col > 0 and (lowest_row is None or (
                            second_col < float(lowest_row[1]) or
                            (second_col == float(lowest_row[1]) and fourth_col < float(lowest_row[3]))
                        )):
                            lowest_row = row

                    total_lines += line_count  # Add the current file's line count to the total

                    if lowest_row:
                        lowest_second_col_values.append(float(lowest_row[1]))
                        first_col_values.append(float(lowest_row[0]))
                        last_col_values.append(float(lowest_row[-1]))

    # Print the number of files found
    print(f"Number of files found: {file_count}")

    # Calculate and print the average number of lines per file
    avg_lines_per_file = total_lines / file_count if file_count > 0 else 0
    print(f"Average number of lines per file (excluding header): {avg_lines_per_file:.2f}")

    # Calculate averages
    avg_lowest_second_col = sum(lowest_second_col_values) / len(lowest_second_col_values) if lowest_second_col_values else 0
    avg_first_col = sum(first_col_values) / len(first_col_values) if first_col_values else 0
    avg_last_col = sum(last_col_values) / len(last_col_values) if last_col_values else 0

    # Print results
    print(f"Average of lowest second column values: {avg_lowest_second_col}")
    print(f"Average of first column values: {avg_first_col}")
    print(f"Average of last column values: {avg_last_col}")

    # Calculate percentage difference if reference value is provided
    if reference_value is not None:
        try:
            reference_value = float(reference_value)
            percent_difference = ((avg_lowest_second_col - reference_value) / reference_value) * 100
            print(f"Percentage difference from {reference_value}: {percent_difference:.2f}%")
        except ValueError:
            print("Invalid reference value provided.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <directory> [reference_value]")
    else:
        directory = sys.argv[1]
        reference_value = sys.argv[2] if len(sys.argv) > 2 else None
        process_files(directory, reference_value)