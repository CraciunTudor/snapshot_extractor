# Copyright 2024 Nokia. All rights reserved.
#
# Script to unzip the BTS Snapshot file and get the core files used in MCTRL analysis
# Convert to .py .exe using pyinstaller
# Developed using Python 3.11.8, converted using pyinstaller 6.4.0 (pyinstaller --onefile script.py)
# 13.02.2024 - Initial version
# 14.02.2024 - Upon starting the application, the CLI will open and request the zip path
#               - The files will be extracted inside a new directory created in the folder where the .exe is
#            - Now pm files are also extracted
#            - Unfortunately, cannot provide the zip path from a remote server, as the process does not have privileges to open the remote zip
import os
import zipfile
import lzma

def second_core_correct_zip(target_string, nested_zip_filename):
    return ("2011" not in target_string) or ("_2011_part" in nested_zip_filename)
    # target is not 2nd core; or (if reached here, target is 2nd core) and contains the string in the filename

def extract_file_containing_string_from_snapshot(snapshot_zip_path, target_string, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    with zipfile.ZipFile(snapshot_zip_path, 'r') as snapshot_zip:
        with snapshot_zip.open('snapshot_file_list.txt') as file_list:
            nested_zip_filename = None
            for line in file_list:
                if line.decode('utf-8')[:3] == 'BTS' and line.decode('utf-8').strip()[-5:] == '.zip:':
                    nested_zip_filename = line.decode('utf-8').strip().split(':')[0]
                else:
                    if target_string in line.decode('utf-8') and second_core_correct_zip(target_string, nested_zip_filename):
                        break

        print(f"Found nested zip {nested_zip_filename}")

        if nested_zip_filename:
            with snapshot_zip.open(nested_zip_filename) as nested_zip_file:
                with zipfile.ZipFile(nested_zip_file) as nested_zip:
                    for file in nested_zip.namelist():
                        if target_string in file:
                            nested_zip.extract(file, output_folder)
                            print(f"File '{file}' containing '{target_string}' extracted successfully.")
                            return
            print(f"File containing '{target_string}' not found in nested zip.")
        else:
            print(f"File containing '{target_string}' not found in snapshot.")

# First level implies the extraction of the ims2 and the .xs' for the runtime and startup logs
def extract_first_level(snapshot_zip_path, output_folder, target_strings):
    for target_string in target_strings:
        extract_file_containing_string_from_snapshot(snapshot_zip_path, target_string, output_folder)

def extract_from_zip_to_path(zip_path, target_filename, output_path):
    with zipfile.ZipFile(zip_path) as nested_zip:
        for file in nested_zip.namelist():
            if target_filename in file:
                nested_zip.extract(file, output_path)
                print(f"File '{file}' extracted successfully from '{zip_path}'")
                return True
        print(f"File '{target_filename}' not found in '{zip_path}'")
        return False

def extract_file_from_zip_to_output(zip_path, target_filename, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    return extract_from_zip_to_path(zip_path, target_filename, output_folder)

def extract_from_xz_to_path(xz_file_path, output_path):
    with lzma.open(xz_file_path, 'rb') as xz_file:
        xz_data = xz_file.read()

    with open(os.path.join(output_path, os.path.basename(xz_file_path)[:-3]), 'wb') as log_file:
        log_file.write(xz_data)

    return True

def extract_log_and_clear(xz_file_name, input_folder, file, remove_source = True):
    extraction_result = extract_file_from_zip_to_output(os.path.join(input_folder, file), xz_file_name, input_folder)
    if extraction_result:
        extract_from_xz_to_path(os.path.join(input_folder, xz_file_name), input_folder)
        os.remove(os.path.join(input_folder, xz_file_name))

    if remove_source:
        try:
            # Clean clutter
            os.remove(os.path.join(input_folder, file))
        except FileNotFoundError as e:
            print(f"Tried to remove absent file {e}")


# Second level implies the extraction of the runtime and startup logs from their .xz zips
def extract_second_level(input_folder):
    for file in os.listdir(input_folder):
        if "_runtime.zip" in file:
            extract_log_and_clear('runtime_BTSOM.log.xz', input_folder, file)
        if "_startup.zip" in file:
            extract_log_and_clear('startup_BTSOM.log.xz', input_folder, file)
        if "_syslog.zip" in file:
            extract_log_and_clear('runtime_BTSOM.log.xz', input_folder, file, False)
            extract_log_and_clear('startup_BTSOM.log.xz', input_folder, file)

new_folder_name = ""

# Path of the unzipping location for the snapshot
def true_output_path(output_path):
    return os.path.join(os.getcwd(), new_folder_name, output_path)

def prepare_unzipping_directory(snapshot_zip_path):
    global new_folder_name
    try:
        new_folder_name = input("Enter new directory name: ").strip()
        print("New directory for unzipping: " + new_folder_name)
        return True
    except Exception as e:
        print("Error when reading the folder name")
        return False

def runCLI():
    snapshot_zip_path = input("Enter snapshot.zip path: ").strip()

    if prepare_unzipping_directory(snapshot_zip_path) is False:
        return

    # Define a list of tuples containing output_folder and target_strings for each core
    target_dir_and_files_to_extract = [
        ("1011_logs", ['1011_im', '1011_runtime.zip', '1011_startup.zip']),
        ("2011_logs", ['2011_im', '2011_runtime.zip', '2011_startup.zip']),
        ("1011_pm_1", ['1011_pm_1_im_snapshot', '1011_pm_1_syslog']),
        ("1011_pm_2", ['1011_pm_2_im_snapshot', '1011_pm_2_syslog']),
        ("2011_pm_1", ['2011_pm_1_im_snapshot', '2011_pm_1_syslog']),
        ("2011_pm_2", ['2011_pm_2_im_snapshot', '2011_pm_2_syslog'])
    ]

    # Iterate over the list of tuples and call extract_first_level for each core
    for output_folder, target_strings in target_dir_and_files_to_extract:
        output_folder_path = true_output_path(output_folder)
        extract_first_level(snapshot_zip_path, output_folder_path, target_strings)

    # Update input_folders_for_second_level if needed
    input_folders_for_second_level = [core[0] for core in target_dir_and_files_to_extract]

    for input_folder in input_folders_for_second_level:
        extract_second_level(true_output_path(input_folder))

    next_action = input("Extract another (y/n):")
    if next_action.strip() == "y":
        runCLI()
    else:
        print("Exit")

def main():
    try:
        runCLI()
    except Exception as e:
        print(f"Exception: {e}")
        input_user = input("Failure; Possibly unexpected snapshot structure scenario; Please report the problem to tudor.craciun@nokia by providing the snapshot and the logs above")

if __name__ == "__main__":
    main()