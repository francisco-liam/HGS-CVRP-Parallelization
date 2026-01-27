import os
import shutil

# Define the base directory
base_dir = os.getcwd()

# Iterate over all files in the base directory
for file_name in os.listdir(base_dir):
    # Skip directories, only process files
    if os.path.isfile(file_name):
        # Split the file name into parts based on the '-' delimiter
        parts = file_name.split('-')

        # Ensure the file name matches the expected pattern X-Y-
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            x_dir = f"n{parts[0]}"  # Corresponding X directory
            y_threads = f"{parts[1]}-threads"  # Corresponding Y-threads subdirectory

            # Construct the full path for the X directory
            x_dir_path = os.path.join(base_dir, x_dir)

            # Ensure the X directory exists
            if os.path.exists(x_dir_path):
                # Construct the full path for the Y-threads subdirectory
                y_threads_path = os.path.join(x_dir_path, y_threads)

                # Create the Y-threads subdirectory if it doesn't exist
                os.makedirs(y_threads_path, exist_ok=True)

                # Move the file to the Y-threads subdirectory
                src_path = os.path.join(base_dir, file_name)
                dest_path = os.path.join(y_threads_path, file_name)
                shutil.move(src_path, dest_path)

                print(f"Moved {file_name} to {dest_path}")
            else:
                print(f"X directory {x_dir} does not exist for file {file_name}")
        else:
            print(f"File {file_name} does not match the expected pattern X-Y-")