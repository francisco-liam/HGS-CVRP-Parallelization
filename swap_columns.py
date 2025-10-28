import os
import csv
import sys

def swap_columns_in_files(directory):
    # Traverse the specified directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("stats.csv"):
                file_path = os.path.join(root, file)
                temp_file_path = file_path + ".tmp"

                with open(file_path, 'r') as csvfile, open(temp_file_path, 'w', newline='') as temp_csvfile:
                    reader = csv.reader(csvfile)
                    writer = csv.writer(temp_csvfile)

                    for row in reader:
                        if len(row) >= 3:  # Ensure there are at least 3 columns
                            row[1], row[2] = row[2], row[1]  # Swap the second and third columns
                        writer.writerow(row)

                # Replace the original file with the modified file
                os.replace(temp_file_path, file_path)
                print(f"Swapped columns in: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <directory>")
    else:
        directory = sys.argv[1]
        if os.path.isdir(directory):
            swap_columns_in_files(directory)
        else:
            print("Invalid directory. Please provide a valid path.")