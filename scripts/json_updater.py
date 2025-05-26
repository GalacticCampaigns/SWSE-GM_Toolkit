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
This script applies batch edits (add, update, delete) to structured JSON data files.
It dynamically discovers JSON files and can handle:
1. SAGA Index item files (list of records within a wrapped structure).
2. Single complex JSON object files (e.g., rule sets like class_rules.json) - indicated by
   an "is_single_object": true flag in the edit request.
3. Multi-collection files (e.g., Character Profiles) - configured statically for now
   due to their unique internal structure and ID fields.

Prerequisites & Usage: See command line help (python json_updater.py -h) and
the "Instructions for AI: Generating JSON Edits" document.

Key for AI Edit Files:
- For SAGA Index files (e.g. armor.json): "target_file_key": "armor"
- For single object files (e.g. class_rules.json): 
  "target_file_key": "class_rules", "is_single_object": true
- For multi-collection files (e.g. npc_profiles.json containing a "pcs" list):
  "target_file_key": "npc_profiles#pcs" 
  (Note: The base filename 'npc_profiles' here should match NPC_PROFILE_FILENAME_BASE)
"""

# --- CONFIGURATION ---
DEFAULT_LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'
NPC_PROFILE_FILE_PATH = r"D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\WIDT_NPCS.json" # PLEASE UPDATE
NPC_PROFILE_FILENAME_BASE = "WIDT_NPCS" 

NPC_PROFILE_COLLECTION_KEYS = {
    "pcs": {"id_field": "pc_id", "sort_key": "pc_id", "preferred_top_keys": ["pc_id", "name", "is_active"], "is_list_of_objects": True, "is_object_map": False},
    "npcs": {"id_field": "npc_id", "sort_key": "npc_id", "preferred_top_keys": ["npc_id", "name", "is_active"], "is_list_of_objects": True, "is_object_map": False},
    "factions": {"id_field": "faction_id", "is_list_of_objects": False, "is_object_map": True, "sort_key": None, "preferred_top_keys": ["faction_id", "faction_name"]},
    "npc_stat_blocks": {"id_field": "npc_id_ref", "sort_key": "npc_id_ref", "preferred_top_keys": ["npc_id_ref", "character_name_display"], "is_list_of_objects": True, "is_object_map": False}
}
DEFAULT_SAGA_INDEX_TOP_KEYS = ["id", "name", "source_book", "page"]
DEFAULT_SINGLE_OBJECT_TOP_KEYS = ["file_description", "source_book_reference", "page_reference_general"] 

INITIAL_TARGET_FILES_CONFIG = {} 

# --- HELPER FUNCTIONS ---

def populate_initial_config(npc_profile_path_override=None):
    global INITIAL_TARGET_FILES_CONFIG 
    actual_npc_profile_path = npc_profile_path_override if npc_profile_path_override else NPC_PROFILE_FILE_PATH
    base_npc_filename = NPC_PROFILE_FILENAME_BASE 

    for collection_key_suffix, details in NPC_PROFILE_COLLECTION_KEYS.items():
        target_key = f"{base_npc_filename}#{collection_key_suffix}"
        INITIAL_TARGET_FILES_CONFIG[target_key] = {
            "full_path": actual_npc_profile_path,
            "data_wrapper_key": None, 
            "collection_key": collection_key_suffix, 
            "id_field": details["id_field"],
            "secondary_id_field": None,
            "is_list_of_objects": details.get("is_list_of_objects", True),
            "is_object_map": details.get("is_object_map", False),
            "is_single_object": False, 
            "sort_key": details.get("sort_key"),
            "preferred_top_keys": details.get("preferred_top_keys", [])
        }
    print(f"Initialized static config for '{base_npc_filename}' collections using path: {actual_npc_profile_path}")

def generate_dynamic_target_files_config(root_path, existing_config):
    config = existing_config 
    data_base_path = os.path.join(root_path, 'data')
    print("Dynamically scanning for other JSON files...")
    if not os.path.isdir(data_base_path):
        print(f"Warning: Base data directory not found for dynamic scan: {data_base_path}")
        return config

    for category_dir_name in os.listdir(data_base_path):
        category_dir_path = os.path.join(data_base_path, category_dir_name)
        if os.path.isdir(category_dir_path) and category_dir_name != 'meta_info':
            print(f"  Scanning subdirectory: data\\{category_dir_name}")
            for filename_with_ext in os.listdir(category_dir_path):
                if filename_with_ext.endswith(".json"):
                    base_filename, _ = os.path.splitext(filename_with_ext)
                    target_file_key = base_filename
                    
                    if target_file_key in config or \
                       any(key.startswith(target_file_key + "#") for key in config) or \
                       filename_with_ext == os.path.basename(NPC_PROFILE_FILE_PATH):
                        continue 

                    full_file_path = os.path.join(category_dir_path, filename_with_ext)
                    
                    list_key_convention = f"{target_file_key}_list"
                    data_key_convention = f"{target_file_key}_data"
                    preferred_keys_list = DEFAULT_SAGA_INDEX_TOP_KEYS.copy()
                    is_single_obj_default = False 

                    if target_file_key == "equipment_general": 
                        list_key_convention = "general_equipment_list"; data_key_convention = "general_equipment_data"
                    
                    # Attempt to load to infer if it's a single object, if not explicitly multi-collection or SAGA list
                    try:
                        json_content_peek = load_json_file(full_file_path)
                        if json_content_peek and isinstance(json_content_peek, dict) and \
                           not (data_key_convention in json_content_peek and \
                                list_key_convention in json_content_peek.get(data_key_convention, {})):
                            # If it's a dict but doesn't match SAGA list structure, assume single object for now
                            # This relies on the edit request's "is_single_object" flag for definitive handling
                            is_single_obj_default = True 
                            data_key_convention = None
                            list_key_convention = None
                            preferred_keys_list = DEFAULT_SINGLE_OBJECT_TOP_KEYS.copy()
                            print(f"    Inferring '{target_file_key}' as potentially single object based on structure.")
                    except Exception:
                        pass # Could not load or parse, will default to list structure

                    config[target_file_key] = {
                        "full_path": full_file_path,
                        "data_wrapper_key": data_key_convention,
                        "collection_key": list_key_convention,
                        "id_field": "name" if not is_single_obj_default else None, 
                        "secondary_id_field": "source_book" if not is_single_obj_default else None,
                        "is_list_of_objects": not is_single_obj_default, 
                        "is_single_object": is_single_obj_default, 
                        "is_object_map": False, 
                        "sort_key": "name" if not is_single_obj_default else None,
                        "preferred_top_keys": preferred_keys_list
                    }
                    print(f"    Discovered and configured: '{target_file_key}' -> {full_file_path}")
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
    except json.JSONDecodeError as e: print(f"Error: Could not decode JSON from {file_path}. {e}"); return None
    except Exception as e: print(f"An unexpected error occurred while loading {file_path}: {e}"); return None

def save_updated_json_file(full_data_obj, output_path, config_entry, is_single_object_from_edit_flag=False): # Added parameter
    # Determine if the file *type* is single object based on config, or override from edit request flag
    is_single_object_file_type = is_single_object_from_edit_flag or config_entry.get("is_single_object", False)
    preferred_top_keys = config_entry.get("preferred_top_keys", DEFAULT_SINGLE_OBJECT_TOP_KEYS if is_single_object_file_type else [])

    if is_single_object_file_type:
        full_data_obj = reorder_record_keys(full_data_obj, preferred_top_keys)
    else: 
        data_wrapper_key = config_entry.get("data_wrapper_key")
        collection_key = config_entry.get("collection_key")
        is_list = config_entry.get("is_list_of_objects", False)
        sort_key = config_entry.get("sort_key")
        
        collection_parent = full_data_obj
        if data_wrapper_key:
            if data_wrapper_key not in collection_parent: print(f"Error: save - data_wrapper_key '{data_wrapper_key}' missing for {output_path}."); return
            collection_parent = collection_parent[data_wrapper_key]
        if collection_key not in collection_parent: print(f"Error: save - collection_key '{collection_key}' missing for {output_path}."); return
        actual_collection = collection_parent[collection_key]

        if is_list:
            if isinstance(actual_collection, list):
                reordered_collection = [reorder_record_keys(record, preferred_top_keys) for record in actual_collection]
                if sort_key: collection_parent[collection_key] = sorted(reordered_collection, key=lambda x: str(x.get(sort_key, "")))
                else: collection_parent[collection_key] = reordered_collection
            else: print(f"Warning: Expected list for '{collection_key}', found {type(actual_collection)}. Skip sort/reorder.")
        else: # Object map
            if isinstance(actual_collection, dict):
                reordered_map = {}
                for key_map in sorted(actual_collection.keys()): 
                    reordered_map[key_map] = reorder_record_keys(actual_collection[key_map], preferred_top_keys)
                collection_parent[collection_key] = reordered_map
            else: print(f"Warning: Expected object map for '{collection_key}', found {type(actual_collection)}. Skip key reorder.")
            
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(full_data_obj, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated and saved {config_entry.get('target_file_key', os.path.basename(output_path))} JSON to: {output_path}")
    except Exception as e: print(f"Error writing {os.path.basename(output_path)} JSON to file {output_path}: {e}")

def find_record_index_or_key(data_collection, identifier, config_details, is_single_object_override=False):
    if is_single_object_override: return True 
    
    id_field = config_details.get("id_field"); secondary_id_field = config_details.get("secondary_id_field")
    is_list = config_details.get("is_list_of_objects", False)

    identifier_primary_value = identifier.get(id_field)
    if not identifier_primary_value and id_field: print(f"Warning: Identifier missing primary ID field '{id_field}'."); return -1 if is_list else None
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

def apply_edit(data_collection_or_object, edit_request, dry_run=False, config_details=None, is_single_object_override=False):
    action = edit_request.get("action"); identifier = edit_request.get("identifier"); payload = edit_request.get("payload")
    if not config_details: print(f"Error: apply_edit missing config_details. Edit: {edit_request}"); return False
    
    id_field = config_details.get("id_field")
    is_list = config_details.get("is_list_of_objects", False)
    operation_successful = False

    if is_single_object_override:
        if action == "update":
            if not payload: print(f"Warning: 'update' for single object file missing payload. Edit: {edit_request}"); return False
            if dry_run: print(f"  DRY RUN: Would update top-level keys with payload:\n{json.dumps(payload, indent=4)}")
            else: print(f"  Updating top-level keys."); data_collection_or_object.update(payload)
            operation_successful = True
        elif action == "add": 
            if not payload: print(f"Warning: 'add' for single object file missing payload. Edit: {edit_request}"); return False
            if dry_run: print(f"  DRY RUN: Would add/update top-level keys:\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding/updating top-level keys."); data_collection_or_object.update(payload) 
            operation_successful = True
        elif action == "delete": 
            keys_to_delete = identifier.get("keys_to_delete") if identifier else None
            if not keys_to_delete or not isinstance(keys_to_delete, list): print(f"Warning: 'delete' for single object file requires 'keys_to_delete' list in identifier. Edit: {edit_request}"); return False
            for key_del in keys_to_delete:
                if key_del in data_collection_or_object:
                    if dry_run: print(f"  DRY RUN: Would delete top-level key '{key_del}'.")
                    else: print(f"  Deleting top-level key '{key_del}'."); del data_collection_or_object[key_del]
                    operation_successful = True 
                else: print(f"  Warning: Key '{key_del}' not found for deletion.")
        else: print(f"Warning: Unknown action '{action}' for single object file. Edit: {edit_request}")
        return operation_successful

    if action == "update":
        if not identifier or not payload: print(f"Warning: 'update' missing identifier/payload. Edit: {edit_request}"); return False
        if is_list:
            idx = find_record_index_or_key(data_collection_or_object, identifier, config_details)
            if idx != -1:
                if dry_run: print(f"  DRY RUN: Would update record identified by {identifier} with payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Updating record identified by {identifier}"); data_collection_or_object[idx].update(payload)
                operation_successful = True
            else: print(f"  Warning: Record not found for update: {identifier}")
        else: # Object map
            key = find_record_index_or_key(data_collection_or_object, identifier, config_details)
            if key: 
                if dry_run: print(f"  DRY RUN: Would update record with key '{key}' with payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Updating record with key '{key}'"); data_collection_or_object[key].update(payload)
                operation_successful = True
            else: print(f"  Warning: Record not found for update (key: {identifier.get(id_field)})")
            
    elif action == "add":
        if not payload: print(f"Warning: 'add' missing payload. Edit: {edit_request}"); return False
        if is_list:
            add_id_val = payload.get(id_field)
            add_ident = {id_field: add_id_val}
            if config_details.get("secondary_id_field"): add_ident[config_details["secondary_id_field"]] = payload.get(config_details["secondary_id_field"])
            if find_record_index_or_key(data_collection_or_object, add_ident, config_details) != -1:
                print(f"  Warning: Record identified by {add_ident} already exists. Skipping add."); return False
            if dry_run: print(f"  DRY RUN: Would add new record:\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record: {add_id_val}"); data_collection_or_object.append(payload)
            operation_successful = True
        else: # Object map
            add_key = identifier.get(id_field) 
            if not add_key: print(f"Warning: 'add' to object map missing '{id_field}' in identifier. Edit: {edit_request}"); return False
            if add_key in data_collection_or_object: print(f"  Warning: Record with key '{add_key}' already exists. Skipping add."); return False
            if dry_run: print(f"  DRY RUN: Would add new record with key '{add_key}':\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record with key '{add_key}'"); data_collection_or_object[add_key] = payload
            operation_successful = True

    elif action == "delete":
        if not identifier: print(f"Warning: 'delete' missing identifier. Edit: {edit_request}"); return False
        if is_list:
            idx = find_record_index_or_key(data_collection_or_object, identifier, config_details)
            if idx != -1:
                rec_data = data_collection_or_object[idx] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record identified by {identifier}:\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record identified by {identifier}"); del data_collection_or_object[idx]
                operation_successful = True
            else: print(f"  Warning: Record not found for delete: {identifier}")
        else: # Object map
            key = find_record_index_or_key(data_collection_or_object, identifier, config_details)
            if key:
                rec_data = data_collection_or_object[key] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record with key '{key}':\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record with key '{key}'"); del data_collection_or_object[key]
                operation_successful = True
            else: print(f"  Warning: Record not found for delete (key: {identifier.get(id_field)})")
    else: print(f"Warning: Unknown action '{action}'. Edit: {edit_request}")
    return operation_successful

# --- MAIN PROCESSING LOGIC ---
def main(edits_file_path, root_path, dry_run=False):
    if dry_run: print("*** DRY RUN MODE ENABLED: No files will be modified. ***\n")
    print(f"Starting JSON update process for edits in: {edits_file_path}")
    print(f"Using SAGA Index root path (for dynamic discovery): {root_path}")

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

        config_entry = TARGET_FILES_CONFIG[target_key] 
        file_path = config_entry["full_path"] 
        
        print(f"\nProcessing edits for: {target_key} (File: {file_path})")
        
        target_data_obj_original = None
        if os.path.exists(file_path):
            target_data_obj_original = load_json_file(file_path)
            if not target_data_obj_original: print(f"Error: Could not load target file {file_path}. Skipping."); continue
        elif all(edit.get("action") == "add" for edit in edits_for_file):
             print(f"Target file {file_path} not found. Will simulate/create new file for 'add' operations.")
             # Determine structure for new file based on config or edit request flag
             # The first edit request's flag will determine the structure for a new file
             is_single_obj_for_new_file = edits_for_file[0].get("is_single_object", config_entry.get("is_single_object", False))
             if is_single_obj_for_new_file: target_data_obj_original = {} 
             elif config_entry.get("data_wrapper_key"): target_data_obj_original = {config_entry["data_wrapper_key"]: {"description": f"Compilation of {target_key.split('#')[0].replace('_', ' ').title()}", config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}}}
             else: target_data_obj_original = {config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}}
        else: print(f"Error: Target file {file_path} not found and not all edits 'add'. Skipping."); continue
        
        target_data_obj_modified = json.loads(json.dumps(target_data_obj_original)) 

        file_would_be_modified = False; edits_applied_this_file_count = 0
        for edit_request in edits_for_file:
            is_single_object_for_this_edit = edit_request.get("is_single_object", config_entry.get("is_single_object", False))
            
            actual_collection_to_edit = None
            if is_single_object_for_this_edit:
                actual_collection_to_edit = target_data_obj_modified 
            else:
                collection_parent = target_data_obj_modified
                if config_entry.get("data_wrapper_key"):
                    if config_entry["data_wrapper_key"] not in collection_parent: print(f"Error: File {file_path} missing wrapper '{config_entry['data_wrapper_key']}'. Skip edit."); continue
                    collection_parent = collection_parent[config_entry["data_wrapper_key"]]
                if config_entry["collection_key"] not in collection_parent: print(f"Error: File {file_path} missing collection '{config_entry['collection_key']}'. Skip edit."); continue
                actual_collection_to_edit = collection_parent[config_entry["collection_key"]]
            
            if apply_edit(actual_collection_to_edit, edit_request, dry_run=dry_run, config_details=config_entry, is_single_object_override=is_single_object_for_this_edit): 
                file_would_be_modified = True; edits_applied_this_file_count +=1
        
        if file_would_be_modified:
            total_edits_processed_successfully += edits_applied_this_file_count
            # For saving, use the flag from the *first edit request* if it was a new file,
            # otherwise use the config_entry's default is_single_object status.
            # This ensures consistency if a file is created as a single object.
            is_single_object_file_type_for_saving = edits_for_file[0].get("is_single_object", config_entry.get("is_single_object", False)) if not os.path.exists(file_path) and edits_for_file else config_entry.get("is_single_object", False)

            if dry_run: print(f"  DRY RUN SUMMARY for {target_key}: {edits_applied_this_file_count} edit(s) would be processed.")
            else:
                if os.path.exists(file_path): 
                    try:
                        file_dir, fname_ext = os.path.split(file_path)
                        fname_base, ext = os.path.splitext(fname_ext)
                        backup_dir = os.path.join(file_dir, "backup") 
                        if not os.path.exists(backup_dir): os.makedirs(backup_dir)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_filename = f"{fname_base}.backup_{timestamp}{ext}"
                        backup_file_path = os.path.join(backup_dir, backup_filename)
                        shutil.copy2(file_path, backup_file_path)
                        print(f"  Backup of '{fname_ext}' created at '{backup_file_path}'")
                    except Exception as e_backup: print(f"  Error creating backup for {file_path}: {e_backup}")
                save_updated_json_file(target_data_obj_modified, file_path, config_entry, is_single_object_from_edit_flag=is_single_object_file_type_for_saving) 
        elif not dry_run: print(f"  No changes processed or would be processed for {target_key}.")

    if dry_run: print(f"\nDRY RUN COMPLETE. {total_edits_processed_successfully} total edits simulated.")
    else: print(f"\nJSON update process complete. Total edits successfully applied: {total_edits_processed_successfully}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply JSON edits to SAGA Edition data files. See script header for detailed instructions.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("edits_file", help="Path to the JSON file containing edit requests.")
    parser.add_argument("--root_path", default=DEFAULT_LOCAL_ROOT_PATH, help=f"Root path of the SagaIndex repository. Defaults to:\n'{DEFAULT_LOCAL_ROOT_PATH}'.")
    parser.add_argument("--npc_profile_file", default=None, help=f"Absolute path to the NPC Profile JSON file. If not provided, uses path from script config: '{NPC_PROFILE_FILE_PATH}'.")
    parser.add_argument("--dry_run", action="store_true", help="Simulate updates without writing to files.")
    args = parser.parse_args()
    
    npc_profile_path_to_use = args.npc_profile_file if args.npc_profile_file else NPC_PROFILE_FILE_PATH
    if args.npc_profile_file and args.npc_profile_file != NPC_PROFILE_FILE_PATH: # Check if path was actually provided and different
        print(f"Overriding NPC Profile file path to: {args.npc_profile_file} from command line.")
        NPC_PROFILE_FILE_PATH = args.npc_profile_file # Update the global for populate_initial_config
    
    populate_initial_config(npc_profile_path_to_use) 
    
    main(args.edits_file, args.root_path, args.dry_run)
