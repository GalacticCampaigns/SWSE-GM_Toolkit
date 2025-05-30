#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name: compile_saga_data.py
Version: 1.2.0
Date: 2025-05-26

Purpose:
This script dynamically discovers and compiles all .json files within a specified 
base 'data' directory and its subdirectories. It creates a single, consolidated 
JSON file that mirrors the original directory structure as nested JSON objects. 
This allows for easy access to all Star Wars Saga Edition index data in one place.

Instructions for Use:

1.  Prerequisites:
    * Python 3.x installed on your system.
    * Your Star Wars Saga Edition index data organized into subdirectories 
        within a main 'data' folder, with individual data elements stored as 
        '.json' files.

2.  Save the Script:
    * Copy this Python script.
    * Save it as a Python file (e.g., `compile_saga_data.py`) in a 
        convenient location.
        * Recommendation: Place this script in a 'scripts' directory at the 
            same level as your main 'SagaIndex-...' project folder. For example:
            
            SagaIndex-XXXXXXXX/
            ├── data/
            │   ├── character_elements/
            │   │   ├── abilities.json
            │   │   └── ... (other json files)
            │   ├── core_rules/
            │   └── ... (other subdirectories and json files)
            └── scripts/
                └── compile_saga_data.py 

3.  Configure the `base_data_directory` Path:
    * Open this script (`compile_saga_data.py`) in a text editor.
    * Locate the line within the `if __name__ == "__main__":` block:
        `base_data_directory = "REPLACE_WITH_YOUR_FULL_PATH_TO_DATA_FOLDER"`
    * IMPORTANT: Replace `"REPLACE_WITH_YOUR_FULL_PATH_TO_DATA_FOLDER"` 
        with the actual path to your 'data' directory.
        * Using an absolute path (most reliable):
            * Example for Windows: 
                `base_data_directory = "C:/Users/YourName/Documents/SagaIndex-XXXXXXXX/data"`
            * Example for macOS/Linux: 
                `base_data_directory = "/Users/YourName/Documents/SagaIndex-XXXXXXXX/data"`
        * Using a relative path (if the script is placed correctly):
            * If you placed `compile_saga_data.py` inside a 'scripts/' folder 
                that is a sibling to your 'data/' folder (as recommended):
                `base_data_directory = os.path.join(os.path.dirname(__file__), '..', 'data')`
                (Ensure `import os` is at the top of the script).
            * If `compile_saga_data.py` is directly inside the main 
                `SagaIndex-XXXXXXXX` folder (which contains the 'data' folder):
                `base_data_directory = "data"`

4.  Configure Output (Optional):
    * By default, the script saves the compiled file as 
        `compiled_saga_index.json` inside a folder named `compiled_output`. 
        This `compiled_output` folder will be created in the same directory 
        where the script is run.
    * You can change the `compiled_output_directory` and 
        `compiled_output_filename` variables in the `if __name__ == "__main__":` 
        block if you prefer a different output location or filename.

5.  Run the Script:
    * Open your system's terminal or command prompt.
    * Navigate to the directory where you saved `compile_saga_data.py`.
        * For example, if saved in `SagaIndex-XXXXXXXX/scripts/`, type:
            `cd path/to/your/SagaIndex-XXXXXXXX/scripts/`
    * Execute the script using the command: `python compile_saga_data.py`

6.  Verify Output:
    * The script will print messages indicating its progress, including which 
        files are processed and if any errors occur.
    * After successful execution, you will find the `compiled_saga_index.json` 
        file in the `compiled_output` directory (or your custom output location). 
        This file will contain all the data from your individual JSON files, 
        merged into a single, structured JSON object.

Version Notes:
* 1.0.0 (Initial Release): Basic functionality to compile JSON files.
* 1.1.0 (2025-05-26): 
    * Added dynamic subdirectory traversal.
    * Preserves directory structure in output JSON.
    * Excludes 'backup' folders.
    * Improved error handling and console output.
    * Output directory creation.
* 1.2.0 (2025-05-26):
    * Embedded detailed instructions and versioning directly into the script's docstring.
    * Added shebang and encoding declaration.
"""

import json
import os

def compile_json_data(base_data_dir, output_file):
    """
    Compiles all .json files from a base directory and its subdirectories
    into a single JSON file, preserving the directory structure.

    Args:
        base_data_dir (str): The path to the base 'data' directory.
        output_file (str): The path where the compiled JSON file will be saved.
    """
    compiled_data = {}
    processed_files = 0
    failed_files = 0

    print(f"Starting compilation from base directory: {base_data_dir}")

    if not os.path.isdir(base_data_dir):
        print(f"Error: Base directory '{base_data_dir}' not found or is not a directory.")
        print("Please check the 'base_data_directory' path in the script.")
        return

    for root, dirs, files in os.walk(base_data_dir):
        # Exclude 'backup' directories from being traversed further
        # by modifying dirs in-place.
        dirs[:] = [d for d in dirs if d.lower() != 'backup']
        
        for filename in files:
            if filename.endswith(".json"):
                file_path = os.path.join(root, filename)
                
                # Create a key path that mimics the directory structure
                # relative to the base_data_dir
                relative_path = os.path.relpath(file_path, base_data_dir)
                # Normalize path separators for consistency (use '/')
                # and remove .json extension
                path_parts = relative_path.replace('\\', '/').replace('.json', '').split('/')
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # Navigate/create the nested dictionary structure
                    current_level = compiled_data
                    for i, part in enumerate(path_parts):
                        if i == len(path_parts) - 1: # Last part is the filename (key)
                            current_level[part] = content
                        else: # Directory part
                            current_level = current_level.setdefault(part, {})
                    
                    print(f"Successfully processed and added: {file_path}")
                    processed_files += 1
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {file_path}. Skipping.")
                    failed_files += 1
                except IOError:
                    print(f"Error reading file: {file_path}. Skipping.")
                    failed_files += 1
                except Exception as e:
                    print(f"An unexpected error occurred with file {file_path}: {e}. Skipping.")
                    failed_files += 1

    if processed_files == 0 and failed_files == 0:
        print(f"No .json files found in '{base_data_dir}' (excluding 'backup' directories).")
        return
    elif processed_files == 0 and failed_files > 0:
        print(f"No .json files were successfully processed. Failed to process {failed_files} file(s).")
        return


    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir): # Check if output_dir is not empty
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory {output_dir}: {e}")
            print("Please check permissions or choose a different output directory.")
            return

    # Write the compiled data to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(compiled_data, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully compiled {processed_files} JSON file(s).")
        if failed_files > 0:
            print(f"Failed to process {failed_files} file(s). Please check logs above for details.")
        print(f"Output saved to: {output_file}")
    except IOError as e:
        print(f"Error writing to output file {output_file}: {e}")
        print("Please check permissions or disk space.")
    except Exception as e:
        print(f"An unexpected error occurred while writing output: {e}")

if __name__ == "__main__":
    # --- IMPORTANT: SET THIS PATH ---
    # Set this to the absolute or relative path of your 'SagaIndex-XYZ/data' directory.
    # See instruction step 3 in the docstring at the top of this script for examples.
    base_data_directory = "D:\OneDrive\Documents\GitHub\SagaIndex\data"
    # Example for relative path if script is in 'scripts' and 'data' is a sibling:
    # base_data_directory = os.path.join(os.path.dirname(__file__), '..', 'data') 

    # --- Configure Output (Optional) ---
    compiled_output_directory = "compiled_output" # Folder for the output file
    compiled_output_filename = "compiled_saga_index.json" # Name of the output file
    
    # Construct the full output file path
    # This ensures compiled_output_directory is created relative to the script's location if it's a relative path
    script_dir = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    full_output_dir_path = os.path.join(script_dir, compiled_output_directory)
    full_output_file_path = os.path.join(full_output_dir_path, compiled_output_filename)


    # Initial check if the placeholder path has been replaced
    if "REPLACE_WITH_YOUR_FULL_PATH_TO_DATA_FOLDER" in base_data_directory:
        # Try to use a default relative path if the placeholder is still there
        # This assumes the script is in a 'scripts' folder and 'data' is a sibling.
        print("****************************************************************************")
        print("WARNING: 'base_data_directory' placeholder detected.")
        print("Attempting to use default relative path: ../data")
        print("If this is incorrect, please edit the 'base_data_directory' variable.")
        print("****************************************************************************")
        potential_relative_path = os.path.join(os.path.dirname(__file__) if "__file__" in locals() else os.getcwd(), '..', 'data')
        if os.path.isdir(potential_relative_path):
            base_data_directory = potential_relative_path
            print(f"Using detected relative path: {os.path.abspath(base_data_directory)}")
        else:
            print("****************************************************************************")
            print("ERROR: Default relative path '../data' not found.")
            print("Please manually update the 'base_data_directory' variable in the script")
            print("to point to your actual 'data' folder path.")
            print("Script will not run until this is configured.")
            print("****************************************************************************")
            exit(1) # Exit if path is not configured and default fails

    compile_json_data(base_data_directory, full_output_file_path)
