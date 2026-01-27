import os

def count_files_in_subdirectories(base_dir, directories):
    all_have_30_files = True

    for directory in directories:
        dir_path = os.path.join(base_dir, directory)

        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for subdir in os.listdir(dir_path):
                subdir_path = os.path.join(dir_path, subdir)

                if os.path.isdir(subdir_path):
                    file_count = len([f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))])

                    if file_count != 30:
                        print(f"Subdirectory {subdir_path} has {file_count} files (expected 30)")
                        all_have_30_files = False
        else:
            print(f"Directory {dir_path} does not exist")

    if all_have_30_files:
        print("All subdirectories have exactly 30 files")

# Define the base directory and the list of directories to check
base_dir = os.getcwd()
directories = ["n106", "n289", "n359", "n491", "n573", "n627", "n783", "n895", "n936", "n1001"]

# Run the function
count_files_in_subdirectories(base_dir, directories)