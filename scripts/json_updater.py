import json
import os
import re 
import argparse
import shutil
from datetime import datetime

# --- SCRIPT INSTRUCTIONS & SETUP ---
"""
JSON Updater Script for SAGA Edition Data & Character Profiles

Purpose:
This script applies batch edits (add, update, delete) to the structured JSON data files
for the SAGA Edition project. It reads a list of edit requests from a specified
JSON file and modifies the target data files accordingly.

Prerequisites:
1. Python 3.x installed.
2. An "edits file" in JSON format, conforming to the structure outlined in
   "Instructions for AI: Generating JSON Edits for SAGA Index Data".
   (See project documentation or the ai_json_edit_instructions_v4 artifact).

Directory Structure:
The script assumes a root project directory (e.g., SagaIndex/) with the following structure:
  SagaIndex/
  ├── data/
  │   ├── character_elements/
  │   │   ├── backup/  <-- Backups for character_elements files go here
  │   │   └── *.json
  │   ├── index_elements/
  │   │   ├── backup/  <-- Backups for index_elements files go here
  │   │   └── *.json
  │   └── meta_info/ 
  │       └── *.json (meta_info is currently excluded from dynamic scanning)
  └── scripts/
      └── json_updater.py (this script)
      └── (your_edits_file.json - can be anywhere, path provided as argument)

Usage from Command Line:
python json_updater.py <path_to_edits_file.json> [--root_path <path_to_SagaIndex_root>] [--dry_run]

Arguments:
  edits_file          : (Required) Path to the JSON file containing the edit requests.
  --root_path         : (Optional) Root path for dynamically discovered SAGA Index files.
                        Defaults to DEFAULT_LOCAL_ROOT_PATH.
  --npc_profile_file  : (Optional) Absolute path to an external NPC Profile JSON file if it's
                        not discoverable under the `root_path/data` structure.
                        Defaults to script-configured NPC_PROFILE_FILE_PATH.
  --dry_run           : (Optional) Simulate operations without modifying files or creating backups.

Backup Mechanism (Live Run):
- Before a target JSON file is modified, a backup of its original state is created.
- Backups are placed in a 'backup/' subfolder within the original file's directory
  (e.g., `data/character_elements/backup/species.backup_YYYYMMDD_HHMMSS.json`).
- The script will create the 'backup/' subfolder if it doesn't exist.
- Backup Naming: `original_filename.backup_YYYYMMDD_HHMMSS.json`

Dynamic Configuration:
- SAGA Index files: Discovered in `root_path/data/*/*.json` (excluding meta_info).
- External/Special files (like NPC Profiles): Configured in `INITIAL_TARGET_FILES_CONFIG`
  at the top of the script, requiring you to set the correct `NPC_PROFILE_FILE_PATH`.
"""

# --- CONFIGURATION ---
DEFAULT_LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'
# IMPORTANT: Configure the path to your external NPC Profile JSON file here if it's not under the root_path/data structure
NPC_PROFILE_FILE_PATH = r"D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\WIDT_NPCS.json" # Example path, PLEASE UPDATE

INITIAL_TARGET_FILES_CONFIG = {
    "npc_profiles#pcs": {
        "full_path": NPC_PROFILE_FILE_PATH, "data_wrapper_key": None, "collection_key": "pcs",
        "id_field": "pc_id", "secondary_id_field": None, "is_list_of_objects": True, "sort_key": "pc_id",
        "preferred_top_keys": ["pc_id", "name", "is_active", "player_name"]
    },
    "npc_profiles#npcs": {
        "full_path": NPC_PROFILE_FILE_PATH, "data_wrapper_key": None, "collection_key": "npcs",
        "id_field": "npc_id", "secondary_id_field": None, "is_list_of_objects": True, "sort_key": "npc_id",
        "preferred_top_keys": ["npc_id", "name", "is_active", "quick_summary_for_gm"]
    },
    "npc_profiles#factions": {
        "full_path": NPC_PROFILE_FILE_PATH, "data_wrapper_key": None, "collection_key": "factions",
        "id_field": "faction_id", "secondary_id_field": None, "is_list_of_objects": False, "sort_key": None, 
        "preferred_top_keys": ["faction_id", "faction_name", "faction_type", "allegiance_primary"]
    },
    "npc_profiles#npc_stat_blocks": {
        "full_path": NPC_PROFILE_FILE_PATH, "data_wrapper_key": None, "collection_key": "npc_stat_blocks",
        "id_field": "npc_id_ref", "secondary_id_field": None, "is_list_of_objects": True, "sort_key": "npc_id_ref",
        "preferred_top_keys": ["npc_id_ref", "character_name_display", "game_system", "cl"]
    }
}
DEFAULT_SAGA_INDEX_TOP_KEYS = ["id", "name", "source_book", "page"]


# --- HELPER FUNCTIONS ---

def generate_dynamic_target_files_config(root_path, existing_config):
    config = existing_config # Modify in place
    data_base_path = os.path.join(root_path, 'data')
    print("Dynamically scanning for SAGA Index files...")
    if not os.path.isdir(data_base_path):
        print(f"Warning: SAGA Index data directory not found for dynamic scan: {data_base_path}")
        return config

    for category_dir_name in os.listdir(data_base_path):
        category_dir_path = os.path.join(data_base_path, category_dir_name)
        if os.path.isdir(category_dir_path) and category_dir_name != 'meta_info':
            print(f"  Scanning subdirectory: data\\{category_dir_name}")
            for filename_with_ext in os.listdir(category_dir_path):
                if filename_with_ext.endswith(".json"):
                    base_filename, _ = os.path.splitext(filename_with_ext)
                    target_file_key = base_filename
                    if target_file_key in config or any(key.startswith(target_file_key + "#") for key in config):
                        continue # Skip if already handled by static config

                    list_key = f"{target_file_key}_list"
                    data_key = f"{target_file_key}_data"
                    if target_file_key == "equipment_general":
                        list_key = "general_equipment_list"; data_key = "general_equipment_data"
                    
                    config[target_file_key] = {
                        "full_path": os.path.join(category_dir_path, filename_with_ext), # Corrected to use category_dir_path
                        "data_wrapper_key": data_key, "collection_key": list_key,
                        "id_field": "name", "secondary_id_field": "source_book",
                        "is_list_of_objects": True, "sort_key": "name",
                        "preferred_top_keys": DEFAULT_SAGA_INDEX_TOP_KEYS.copy()
                    }
                    print(f"    Discovered and configured: '{target_file_key}' -> {config[target_file_key]['full_path']}")
    return config

def reorder_record_keys(record_dict, preferred_keys):
    if not isinstance(record_dict, dict) or not preferred_keys: return record_dict
    ordered_record = {}
    for key in preferred_keys:
        if key in record_dict: ordered_record[key] = record_dict[key]
    remaining_keys = sorted([k for k in record_dict if k not in ordered_record])
    for key in remaining_keys: ordered_record[key] = record_dict[key]
    return ordered_record

def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
        return data
    except FileNotFoundError: print(f"Error: File not found at {file_path}"); return None
    except json.JSONDecodeError: print(f"Error: Could not decode JSON from {file_path}"); return None
    except Exception as e: print(f"An unexpected error occurred while loading {file_path}: {e}"); return None

def save_updated_json_file(full_data_obj, output_path, config_entry):
    data_wrapper_key = config_entry.get("data_wrapper_key")
    collection_key = config_entry.get("collection_key")
    is_list = config_entry.get("is_list_of_objects", False)
    sort_key = config_entry.get("sort_key")
    preferred_top_keys = config_entry.get("preferred_top_keys", [])
    collection_parent = full_data_obj
    if data_wrapper_key:
        if data_wrapper_key not in collection_parent: print(f"Error: data_wrapper_key '{data_wrapper_key}' not found for {output_path}."); return
        collection_parent = collection_parent[data_wrapper_key]
    if collection_key not in collection_parent: print(f"Error: collection_key '{collection_key}' not found for {output_path}."); return
    actual_collection = collection_parent[collection_key]

    if is_list:
        if isinstance(actual_collection, list):
            reordered_collection = [reorder_record_keys(record, preferred_top_keys) for record in actual_collection]
            if sort_key: collection_parent[collection_key] = sorted(reordered_collection, key=lambda x: str(x.get(sort_key, ""))) # Ensure sort key is string for safety
            else: collection_parent[collection_key] = reordered_collection
        else: print(f"Warning: Expected list for '{collection_key}', found {type(actual_collection)}. Skip sort/reorder.")
    else: # Object map
        if isinstance(actual_collection, dict):
            reordered_map = {}
            for key_map in sorted(actual_collection.keys()): # Sort keys of the map
                reordered_map[key_map] = reorder_record_keys(actual_collection[key_map], preferred_top_keys)
            collection_parent[collection_key] = reordered_map
        else: print(f"Warning: Expected object map for '{collection_key}', found {type(actual_collection)}. Skip key reorder.")
            
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(full_data_obj, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated and saved {config_entry.get('target_file_key', os.path.basename(output_path))} JSON to: {output_path}")
    except Exception as e: print(f"Error writing {os.path.basename(output_path)} JSON to file {output_path}: {e}")

def find_record_index_or_key(data_collection, identifier, config_details):
    id_field = config_details.get("id_field"); secondary_id_field = config_details.get("secondary_id_field")
    is_list = config_details.get("is_list_of_objects", False)
    identifier_primary_value = identifier.get(id_field)
    if not identifier_primary_value: print(f"Warning: Identifier missing primary ID field '{id_field}'."); return -1 if is_list else None
    identifier_secondary_value = identifier.get(secondary_id_field) if secondary_id_field else None

    if is_list:
        if not isinstance(data_collection, list): return -1
        for index, record in enumerate(data_collection):
            if record.get(id_field) == identifier_primary_value:
                if secondary_id_field and identifier_secondary_value:
                    if record.get(secondary_id_field) == identifier_secondary_value: return index
                elif not secondary_id_field: return index
        return -1
    else: # Object map
        if not isinstance(data_collection, dict): return None
        return identifier_primary_value if identifier_primary_value in data_collection else None

def apply_edit(data_collection, edit_request, dry_run=False, config_details=None):
    action = edit_request.get("action"); identifier = edit_request.get("identifier"); payload = edit_request.get("payload")
    if not config_details: print(f"Error: apply_edit missing config_details. Edit: {edit_request}"); return False
    id_field = config_details.get("id_field"); is_list = config_details.get("is_list_of_objects", False)
    operation_successful = False

    if action == "update":
        if not identifier or not payload: print(f"Warning: 'update' missing identifier/payload. Edit: {edit_request}"); return False
        if is_list:
            idx = find_record_index_or_key(data_collection, identifier, config_details)
            if idx != -1:
                if dry_run: print(f"  DRY RUN: Would update record identified by {identifier} with payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Updating record identified by {identifier}"); data_collection[idx].update(payload)
                operation_successful = True
            else: print(f"  Warning: Record not found for update: {identifier}")
        else: # Object map
            key = find_record_index_or_key(data_collection, identifier, config_details)
            if key: 
                if dry_run: print(f"  DRY RUN: Would update record with key '{key}' with payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Updating record with key '{key}'"); data_collection[key].update(payload)
                operation_successful = True
            else: print(f"  Warning: Record not found for update (key: {identifier.get(id_field)})")
            
    elif action == "add":
        if not payload: print(f"Warning: 'add' missing payload. Edit: {edit_request}"); return False
        if is_list:
            add_id_val = payload.get(id_field)
            add_ident = {id_field: add_id_val}
            if config_details.get("secondary_id_field"): add_ident[config_details["secondary_id_field"]] = payload.get(config_details["secondary_id_field"])
            if find_record_index_or_key(data_collection, add_ident, config_details) != -1:
                print(f"  Warning: Record identified by {add_ident} already exists. Skipping add."); return False
            if dry_run: print(f"  DRY RUN: Would add new record:\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record: {add_id_val}"); data_collection.append(payload)
            operation_successful = True
        else: # Object map
            add_key = identifier.get(id_field) 
            if not add_key: print(f"Warning: 'add' to object map missing '{id_field}' in identifier. Edit: {edit_request}"); return False
            if add_key in data_collection: print(f"  Warning: Record with key '{add_key}' already exists. Skipping add."); return False
            if dry_run: print(f"  DRY RUN: Would add new record with key '{add_key}':\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record with key '{add_key}'"); data_collection[add_key] = payload
            operation_successful = True

    elif action == "delete":
        if not identifier: print(f"Warning: 'delete' missing identifier. Edit: {edit_request}"); return False
        if is_list:
            idx = find_record_index_or_key(data_collection, identifier, config_details)
            if idx != -1:
                rec_data = data_collection[idx] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record identified by {identifier}:\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record identified by {identifier}"); del data_collection[idx]
                operation_successful = True
            else: print(f"  Warning: Record not found for delete: {identifier}")
        else: # Object map
            key = find_record_index_or_key(data_collection, identifier, config_details)
            if key:
                rec_data = data_collection[key] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record with key '{key}':\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record with key '{key}'"); del data_collection[key]
                operation_successful = True
            else: print(f"  Warning: Record not found for delete (key: {identifier.get(id_field)})")
    else: print(f"Warning: Unknown action '{action}'. Edit: {edit_request}")
    return operation_successful

# --- MAIN PROCESSING LOGIC ---
def main(edits_file_path, root_path, dry_run=False):
    if dry_run: print("*** DRY RUN MODE ENABLED: No files will be modified. ***\n")
    print(f"Starting JSON update process for edits in: {edits_file_path}")
    # root_path is for SAGA Index files dynamic discovery
    # NPC_PROFILE_FILE_PATH (global or from arg) is for specific external files

    TARGET_FILES_CONFIG = INITIAL_TARGET_FILES_CONFIG.copy()
    generate_dynamic_target_files_config(root_path, TARGET_FILES_CONFIG) 
    
    if not TARGET_FILES_CONFIG: print("Error: Failed to generate/load any target files configuration. Exiting."); return

    edit_requests = load_json_file(edits_file_path)
    if not edit_requests or not isinstance(edit_requests, list): print("Error: Edits file is empty, not found, or not a JSON list."); return

    edits_by_target = {}; total_edits_processed_successfully = 0
    for edit in edit_requests:
        target_key = edit.get("target_file_key")
        if target_key: edits_by_target.setdefault(target_key, []).append(edit)
        else: print(f"Warning: Edit missing 'target_file_key': {edit}")
    
    for target_key, edits_for_file in edits_by_target.items():
        if target_key not in TARGET_FILES_CONFIG:
            print(f"Warning: Unknown target_file_key '{target_key}'. Skipping {len(edits_for_file)} edits.")
            continue

        config = TARGET_FILES_CONFIG[target_key]
        file_path = config["full_path"] 
        
        print(f"\nProcessing edits for: {target_key} (File: {file_path})")
        
        target_data_obj_original = None
        if os.path.exists(file_path):
            target_data_obj_original = load_json_file(file_path)
            if not target_data_obj_original: print(f"Error: Could not load target file {file_path}. Skipping."); continue
        elif all(edit.get("action") == "add" for edit in edits_for_file):
             print(f"Target file {file_path} not found. Will simulate/create new file for 'add' operations.")
             if config.get("data_wrapper_key"): target_data_obj_original = {config["data_wrapper_key"]: {"description": f"Compilation of {target_key.split('#')[0].replace('_', ' ').title()}", config["collection_key"]: [] if config.get("is_list_of_objects") else {}}}
             else: target_data_obj_original = {config["collection_key"]: [] if config.get("is_list_of_objects") else {}}
        else: print(f"Error: Target file {file_path} not found and not all edits 'add'. Skipping."); continue
        
        target_data_obj_modified = json.loads(json.dumps(target_data_obj_original)) 

        collection_parent = target_data_obj_modified
        if config.get("data_wrapper_key"):
            if config["data_wrapper_key"] not in collection_parent: print(f"Error: File {file_path} missing wrapper '{config['data_wrapper_key']}'. Skip."); continue
            collection_parent = collection_parent[config["data_wrapper_key"]]
        if config["collection_key"] not in collection_parent: print(f"Error: File {file_path} missing collection '{config['collection_key']}'. Skip."); continue
        actual_collection_to_edit = collection_parent[config["collection_key"]]
        
        file_would_be_modified = False; edits_applied_this_file_count = 0
        for edit_request in edits_for_file:
            if apply_edit(actual_collection_to_edit, edit_request, dry_run=dry_run, config_details=config): 
                file_would_be_modified = True; edits_applied_this_file_count +=1
        
        if file_would_be_modified:
            total_edits_processed_successfully += edits_applied_this_file_count
            if dry_run: print(f"  DRY RUN SUMMARY for {target_key}: {edits_applied_this_file_count} edit(s) would be processed.")
            else:
                if os.path.exists(file_path): 
                    try:
                        file_dir, fname_ext = os.path.split(file_path)
                        fname_base, ext = os.path.splitext(fname_ext)
                        backup_dir = os.path.join(file_dir, "backup") # Backup in subfolder
                        if not os.path.exists(backup_dir): os.makedirs(backup_dir)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_filename = f"{fname_base}.backup_{timestamp}{ext}"
                        backup_file_path = os.path.join(backup_dir, backup_filename)
                        shutil.copy2(file_path, backup_file_path)
                        print(f"  Backup of '{fname_ext}' created at '{backup_file_path}'")
                    except Exception as e_backup: print(f"  Error creating backup for {file_path}: {e_backup}")
                save_updated_json_file(target_data_obj_modified, file_path, config) 
        elif not dry_run: print(f"  No changes processed or would be processed for {target_key}.")

    if dry_run: print(f"\nDRY RUN COMPLETE. {total_edits_processed_successfully} total edits simulated.")
    else: print(f"\nJSON update process complete. Total edits successfully applied: {total_edits_processed_successfully}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply JSON edits to SAGA Edition data files. See script header for detailed instructions.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("edits_file", help="Path to the JSON file containing edit requests.")
    parser.add_argument("--root_path", default=DEFAULT_LOCAL_ROOT_PATH, help=f"Root path of the SagaIndex repository. Defaults to:\n'{DEFAULT_LOCAL_ROOT_PATH}'.")
    parser.add_argument("--npc_profile_file", default=NPC_PROFILE_FILE_PATH, help=f"Absolute path to the NPC Profile JSON file. Defaults to script-configured path:\n'{NPC_PROFILE_FILE_PATH}'.")
    parser.add_argument("--dry_run", action="store_true", help="Simulate updates without writing to files.")
    args = parser.parse_args()
    
    # Update NPC_PROFILE_FILE_PATH if provided via command line, affecting INITIAL_TARGET_FILES_CONFIG
    if args.npc_profile_file and args.npc_profile_file != NPC_PROFILE_FILE_PATH:
        print(f"Updating NPC Profile file path to: {args.npc_profile_file}")
        for key in INITIAL_TARGET_FILES_CONFIG:
            if INITIAL_TARGET_FILES_CONFIG[key]["full_path"] == NPC_PROFILE_FILE_PATH: # Check if it's using the default
                 INITIAL_TARGET_FILES_CONFIG[key]["full_path"] = args.npc_profile_file
    
    main(args.edits_file, args.root_path, args.dry_run)
