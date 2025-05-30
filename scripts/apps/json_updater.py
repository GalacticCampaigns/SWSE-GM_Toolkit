import json
import os
import re 
import argparse
import shutil
from datetime import datetime

# --- SCRIPT VERSION INFO ---
SCRIPT_VERSION = "2.4.5" 
SCRIPT_LAST_UPDATED = "2025-05-27"

# --- SCRIPT INSTRUCTIONS & SETUP ---
"""
JSON Updater Script for SAGA Edition Data & Character Profiles
Version: {SCRIPT_VERSION}
Last Updated: {SCRIPT_LAST_UPDATED}

Purpose:
This script applies batch edits (add, update, delete) to structured JSON data files.
It dynamically discovers JSON files and can handle:
1. SAGA Index item files (list of records within a wrapped structure).
   - Supports identification by a dedicated "id" field (highest priority).
   - Falls back to "name", "source_book", AND "page" (if all three provided in identifier).
   - Falls back further to "name" AND "source_book".
   - Finally, falls back to "name" only.
2. Single complex JSON object files (e.g., rule sets like class_rules.json) - indicated by
   an "is_single_object": true flag in the edit request.
3. Multi-collection files (e.g., Character Profiles) - configured statically.

Prerequisites & Usage: See command line help (python json_updater.py -h) and
the "Instructions for AI: Generating JSON Edits" document.

Identifier Priority for SAGA Index Files (when "is_single_object" is false or omitted):
1. "id" (if present in identifier)
2. "name" + "source_book" + "page" (if all present in identifier)
3. "name" + "source_book" (if page not present or no match with page)
4. "name" (if source_book also not present or no match with source_book)
"""

# --- CONFIGURATION ---
DEFAULT_LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'
NPC_PROFILE_FILE_PATH = r"D:\OneDrive\Documents\GitHub\SagaIndex\scripts\json\WIDT_NPCS.json" 
NPC_PROFILE_FILENAME_BASE = "WIDT_NPCS" 

NPC_PROFILE_COLLECTION_KEYS = {
    "pcs": {"id_field": "pc_id", "sort_key": "pc_id", "preferred_top_keys": ["pc_id", "name", "is_active"], "is_list_of_objects": True, "is_object_map": False},
    "npcs": {"id_field": "npc_id", "sort_key": "npc_id", "preferred_top_keys": ["npc_id", "name", "is_active"], "is_list_of_objects": True, "is_object_map": False},
    "factions": {"id_field": "faction_id", "is_list_of_objects": False, "is_object_map": True, "sort_key": None, "preferred_top_keys": ["faction_id", "faction_name"]},
    "npc_stat_blocks": {"id_field": "npc_id_ref", "sort_key": "npc_id_ref", "preferred_top_keys": ["npc_id_ref", "character_name_display"], "is_list_of_objects": True, "is_object_map": False}
}
DEFAULT_SAGA_INDEX_TOP_KEYS = ["id", "name", "source_book", "page"]
DEFAULT_CONFIG_OBJECT_TOP_KEYS = ["file_description", "source_book_reference", "page_reference_general"] 
DEFAULT_DYNAMIC_KEY_OBJECT_TOP_KEYS = [] 

INITIAL_TARGET_FILES_CONFIG = {} 

# --- HELPER FUNCTIONS ---
def populate_initial_config(npc_profile_path_override=None):
    global INITIAL_TARGET_FILES_CONFIG 
    actual_npc_profile_path = npc_profile_path_override if npc_profile_path_override else NPC_PROFILE_FILE_PATH
    base_npc_filename = NPC_PROFILE_FILENAME_BASE 
    for collection_key_suffix, details in NPC_PROFILE_COLLECTION_KEYS.items():
        target_key = f"{base_npc_filename}#{collection_key_suffix}"
        INITIAL_TARGET_FILES_CONFIG[target_key] = {
            "full_path": actual_npc_profile_path, "data_wrapper_key": None, "collection_key": collection_key_suffix, 
            "id_field": details["id_field"], "secondary_id_field": None,
            "is_list_of_objects": details.get("is_list_of_objects", True),
            "is_object_map": details.get("is_object_map", False), "is_single_object": False, 
            "sort_key": details.get("sort_key"), "preferred_top_keys": details.get("preferred_top_keys", [])
        }
    print(f"Initialized static config for '{base_npc_filename}' collections using path: {actual_npc_profile_path}")

def generate_dynamic_target_files_config(root_path, existing_config):
    config = existing_config 
    data_base_path = os.path.join(root_path, 'data')
    print("Dynamically scanning for other JSON files...")
    if not os.path.isdir(data_base_path):
        print(f"Warning: Base data directory not found: {data_base_path}"); return config
    for category_dir_name in os.listdir(data_base_path):
        category_dir_path = os.path.join(data_base_path, category_dir_name)
        if os.path.isdir(category_dir_path) and category_dir_name != 'meta_info':
            print(f"  Scanning subdirectory: data\\{category_dir_name}")
            for filename_with_ext in os.listdir(category_dir_path):
                if filename_with_ext.endswith(".json"):
                    base_filename, _ = os.path.splitext(filename_with_ext)
                    target_file_key = base_filename
                    if target_file_key in config or any(k.startswith(target_file_key + "#") for k in config) or \
                       filename_with_ext == os.path.basename(NPC_PROFILE_FILE_PATH):
                        continue 
                    full_file_path = os.path.join(category_dir_path, filename_with_ext)
                    
                    is_single_obj_inferred = False 
                    preferred_keys_list = DEFAULT_SAGA_INDEX_TOP_KEYS.copy()
                    id_field_inferred = "name" 
                    secondary_id_inferred = "source_book"
                    sort_key_inferred = "name" 
                    data_key_conv = f"{target_file_key}_data"
                    list_key_conv = f"{target_file_key}_list"

                    # Removed special handling for equipment_general as it now follows convention
                    
                    json_content_peek = load_json_file(full_file_path)
                    if not json_content_peek: 
                        print(f"    Warning: Could not load/parse {filename_with_ext}. Assuming new SAGA Index List structure for config.")
                        is_single_obj_inferred = False
                    elif isinstance(json_content_peek, dict) and data_key_conv in json_content_peek and isinstance(json_content_peek[data_key_conv], dict):
                        wrapped_content = json_content_peek[data_key_conv]
                        if list_key_conv in wrapped_content and isinstance(wrapped_content.get(list_key_conv), list):
                            is_single_obj_inferred = False 
                            print(f"    Inferred '{target_file_key}' as SAGA Index List structure (wrapped).")
                        else: 
                            is_single_obj_inferred = True
                            data_key_conv = None; list_key_conv = None # This was incorrect, wrapper still exists
                            data_key_conv = f"{target_file_key}_data" # Keep wrapper
                            list_key_conv = None # Content of wrapper is the single object
                            id_field_inferred = None 
                            secondary_id_inferred = None
                            sort_key_inferred = None
                            preferred_keys_list = DEFAULT_CONFIG_OBJECT_TOP_KEYS.copy()
                            print(f"    Inferred '{target_file_key}' as Single Object Content (within wrapper).")
                    else: 
                        print(f"    Warning: File {filename_with_ext} does not have expected wrapper '{data_key_conv}'. Defaulting to SAGA Index List config.")
                        is_single_obj_inferred = False 

                    config[target_file_key] = {"full_path": full_file_path, "data_wrapper_key": data_key_conv, "collection_key": list_key_conv,
                        "id_field": id_field_inferred, "secondary_id_field": secondary_id_inferred,
                        "is_list_of_objects": not is_single_obj_inferred, 
                        "is_single_object_content": is_single_obj_inferred, # Renamed for clarity
                        "is_object_map": False, "sort_key": sort_key_inferred, "preferred_top_keys": preferred_keys_list}
                    print(f"    Discovered and configured: '{target_file_key}' -> {full_file_path} (Config: is_single_object_content: {is_single_obj_inferred})")
    return config

def reorder_record_keys(record_dict, preferred_keys):
    if not isinstance(record_dict, dict) or not preferred_keys: return record_dict
    ordered_record = {}; 
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

def save_updated_json_file(full_data_obj, output_path, config_entry, is_single_object_content_from_edit_flag=False): 
    is_single_object_content_file_type = is_single_object_content_from_edit_flag or config_entry.get("is_single_object_content", False)
    preferred_top_keys = config_entry.get("preferred_top_keys", []) 
    
    data_wrapper_key = config_entry.get("data_wrapper_key") # Always expect a wrapper now

    if data_wrapper_key and data_wrapper_key in full_data_obj:
        data_to_process = full_data_obj[data_wrapper_key]
        if is_single_object_content_file_type: # The content *inside* the wrapper is a single object
            if not preferred_top_keys: 
                 preferred_top_keys = DEFAULT_CONFIG_OBJECT_TOP_KEYS # Default for config-like single objects
            full_data_obj[data_wrapper_key] = reorder_record_keys(data_to_process, preferred_top_keys)
        else: # It's a list or object map within the wrapper
            collection_key = config_entry.get("collection_key")
            is_list = config_entry.get("is_list_of_objects", False)
            sort_key = config_entry.get("sort_key")
            if collection_key not in data_to_process: print(f"Error: save - collection '{collection_key}' missing in wrapper for {output_path}."); return
            actual_collection = data_to_process[collection_key]

            if is_list:
                if isinstance(actual_collection, list):
                    reordered_collection = [reorder_record_keys(record, preferred_top_keys) for record in actual_collection]
                    if sort_key: data_to_process[collection_key] = sorted(reordered_collection, key=lambda x: str(x.get(sort_key, "")))
                    else: data_to_process[collection_key] = reordered_collection
                else: print(f"Warning: Expected list for '{collection_key}', found {type(actual_collection)}. Skip sort/reorder.")
            else: # Object map (e.g. factions)
                if isinstance(actual_collection, dict):
                    reordered_map = {}
                    for key_map in sorted(actual_collection.keys()): 
                        reordered_map[key_map] = reorder_record_keys(actual_collection[key_map], preferred_top_keys)
                    data_to_process[collection_key] = reordered_map
                else: print(f"Warning: Expected object map for '{collection_key}', found {type(actual_collection)}. Skip key reorder.")
    elif is_single_object_content_file_type and not data_wrapper_key : # Should not happen with current generate_dynamic_config
         print(f"Error: Save - single object content expected wrapper but data_wrapper_key is None for {output_path}")
         return # This case should ideally not be reached if all files have wrappers
    else:
        print(f"Error: Save - Cannot determine data structure or wrapper missing for {output_path} with config: {config_entry}")
        return
            
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(full_data_obj, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated and saved {config_entry.get('target_file_key', os.path.basename(output_path))} JSON to: {output_path}")
    except Exception as e: print(f"Error writing {os.path.basename(output_path)} JSON to file {output_path}: {e}")


def find_record_index_or_key(data_collection, identifier, config_details, is_single_object_content_override=False):
    if is_single_object_content_override: return True 
    
    id_field = config_details.get("id_field"); secondary_id_field = config_details.get("secondary_id_field")
    is_list = config_details.get("is_list_of_objects", True) 
    
    identifier_id_val = identifier.get("id") 
    if identifier_id_val and is_list:
        if not isinstance(data_collection, list): return -1
        for index, record in enumerate(data_collection):
            if record.get("id") == identifier_id_val: return index
        print(f"  Info: Record with 'id': \"{identifier_id_val}\" not found by dedicated ID lookup. Attempting fallback...")

    identifier_primary_value = identifier.get(id_field)
    if not identifier_primary_value and id_field:
        print(f"Warning: Identifier missing primary configured ID field '{id_field}'."); return -1 if is_list else None
    identifier_secondary_value = identifier.get(secondary_id_field) if secondary_id_field else None
    identifier_page_value = identifier.get("page") 

    if is_list:
        if not isinstance(data_collection, list): return -1
        for index, record in enumerate(data_collection):
            if record.get(id_field) == identifier_primary_value:
                match_secondary = True 
                if secondary_id_field and identifier_secondary_value is not None: 
                    match_secondary = (record.get(secondary_id_field) == identifier_secondary_value)
                elif secondary_id_field and identifier_secondary_value is None: 
                    match_secondary = (record.get(secondary_id_field) is None or record.get(secondary_id_field) == "")
                if match_secondary:
                    match_page = True 
                    if identifier_page_value is not None and "page" in record: 
                        match_page = (str(record.get("page")) == str(identifier_page_value))
                    elif identifier_page_value is not None and "page" not in record: 
                        match_page = False
                    if match_page: return index
        return -1 
    else: 
        if not isinstance(data_collection, dict): return None
        return identifier_primary_value if identifier_primary_value in data_collection else None


def apply_edit(data_to_edit_or_list, edit_request, dry_run=False, config_details=None, is_single_object_content_override=False): # Renamed first param
    action = edit_request.get("action"); identifier = edit_request.get("identifier"); payload = edit_request.get("payload")
    if not config_details: print(f"Error: apply_edit missing config_details. Edit: {edit_request}"); return False
    
    id_field = config_details.get("id_field"); 
    is_list_collection = config_details.get("is_list_of_objects", False) 
    is_object_map_collection = config_details.get("is_object_map", False) 
    operation_successful = False

    if is_single_object_content_override: # Operating on a single object (e.g. content of class_rules_data)
        # data_to_edit_or_list IS the single object in this case
        if action == "update": 
            if not payload: print(f"Warning: 'update' for single object content missing payload."); return False
            if isinstance(payload, list): # Path-based update
                if dry_run: print(f"  DRY RUN: Would apply patch operations to single object content:\n{json.dumps(payload, indent=4)}")
                else: 
                    print(f"  Applying patch operations to single object content.")
                    for op_item in payload:
                        # This requires a proper JSON Patch implementation or careful path navigation
                        # For simplicity, this example assumes payload keys directly update top-level keys of data_to_edit_or_list
                        # A true JSON Patch would be more robust.
                        # For now, let's assume a simple dictionary update if not a list of ops
                        if op_item.get("op") == "replace" and op_item.get("path", "").startswith("/"):
                            path_segments = op_item.get("path").strip("/").split("/")
                            target_obj = data_to_edit_or_list
                            try:
                                for segment in path_segments[:-1]:
                                    target_obj = target_obj[segment]
                                target_obj[path_segments[-1]] = op_item.get("value")
                                operation_successful = True
                            except (KeyError, TypeError):
                                print(f"    Error: Path '{op_item.get('path')}' not found in single object for replace.")
                        else: # Fallback to direct update if not a recognized patch op for single object
                             data_to_edit_or_list.update(op_item) # Or payload if payload is not a list of ops
                             operation_successful = True

            elif isinstance(payload, dict): # Direct key update for single object
                if dry_run: print(f"  DRY RUN: Would update keys in object with payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Updating keys in object."); data_to_edit_or_list.update(payload)
                operation_successful = True
            else: print(f"Warning: 'update' for single object content has invalid payload type."); return False

        elif action == "add": 
            if not payload: print(f"Warning: 'add' for single object content missing payload."); return False
            if id_field and id_field in payload: 
                new_key = payload.get(id_field)
                if not new_key: print(f"  Warning: 'add' dynamic key, payload missing key field '{id_field}'."); return False
                if new_key in data_to_edit_or_list and not dry_run: print(f"  Warning: Key '{new_key}' already exists. Use 'update'. Skip add."); return False
                if dry_run: print(f"  DRY RUN: Would add key '{new_key}' with value (payload):\n{json.dumps(payload, indent=4)}")
                else: print(f"  Adding key '{new_key}'."); data_to_edit_or_list[new_key] = payload
                operation_successful = True
            else: 
                if dry_run: print(f"  DRY RUN: Would add/update keys from payload:\n{json.dumps(payload, indent=4)}")
                else: print(f"  Adding/updating keys from payload."); data_to_edit_or_list.update(payload) 
                operation_successful = True
        elif action == "delete": 
            keys_to_delete = identifier.get("keys_to_delete") if identifier else None 
            key_from_id_field = identifier.get(id_field) if identifier and id_field else None 
            if keys_to_delete and isinstance(keys_to_delete, list):
                for key_del in keys_to_delete:
                    if key_del in data_to_edit_or_list:
                        if dry_run: print(f"  DRY RUN: Would delete key '{key_del}'.")
                        else: print(f"  Deleting key '{key_del}'."); del data_to_edit_or_list[key_del]
                        operation_successful = True 
                    else: print(f"  Warning: Key '{key_del}' not found for deletion.")
            elif key_from_id_field: 
                 if key_from_id_field in data_to_edit_or_list:
                    if dry_run: print(f"  DRY RUN: Would delete key '{key_from_id_field}'.")
                    else: print(f"  Deleting key '{key_from_id_field}'."); del data_to_edit_or_list[key_from_id_field]
                    operation_successful = True
                 else: print(f"  Warning: Key '{key_from_id_field}' not found for deletion.")
            else: print(f"Warning: 'delete' for single object requires 'keys_to_delete' or valid '{id_field}' in identifier."); return False
        else: print(f"Warning: Unknown action '{action}' for single object content. Edit: {edit_request}")
        return operation_successful

    # --- Logic for lists of objects or object maps ---
    if action == "update": 
        if not identifier or not payload: print(f"Warning: 'update' missing identifier/payload."); return False
        if is_list_collection: 
            idx = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if idx != -1:
                target_record = data_to_edit_or_list[idx]
                if dry_run: print(f"  DRY RUN: Would update record (index {idx}) identified by {identifier} with patch operations:\n{json.dumps(payload, indent=4)}")
                else: 
                    print(f"  Updating record (index {idx}) identified by {identifier}")
                    if isinstance(payload, list): # JSON Patch style payload
                        for op_item in payload:
                            path_str = op_item.get("path", "")
                            op_type = op_item.get("op")
                            value = op_item.get("value") # Value might not exist for "remove"
                            
                            # Basic path navigation (does not support full JSON Pointer spec like ~0, ~1)
                            path_segments = [seg for seg in path_str.strip("/").split("/") if seg]
                            current_target = target_record
                            
                            try:
                                for i, segment in enumerate(path_segments[:-1]):
                                    current_target = current_target[int(segment) if segment.isdigit() and isinstance(current_target, list) else segment]
                                final_segment = path_segments[-1] if path_segments else None

                                if op_type == "replace":
                                    if final_segment is None: target_record = value # Replace whole record if path is empty
                                    else: current_target[int(final_segment) if final_segment.isdigit() and isinstance(current_target, list) else final_segment] = value
                                elif op_type == "add":
                                    if isinstance(current_target, list):
                                        if final_segment == '-': current_target.append(value)
                                        elif final_segment and final_segment.isdigit(): current_target.insert(int(final_segment), value)
                                        else: print(f"    Warning: Invalid 'add' path for list: {path_str}"); continue
                                    elif isinstance(current_target, dict): # Add/replace key in object
                                        if final_segment is None: print(f"    Warning: 'add' to object root requires a key in path. Path: {path_str}"); continue
                                        current_target[final_segment] = value
                                    else: print(f"    Warning: 'add' target is not list or object. Path: {path_str}"); continue
                                elif op_type == "remove":
                                    if final_segment is None: print(f"    Warning: 'remove' path cannot be empty for record item."); continue
                                    if isinstance(current_target, list) and final_segment.isdigit(): del current_target[int(final_segment)]
                                    elif isinstance(current_target, dict) and final_segment in current_target : del current_target[final_segment]
                                    else: print(f"    Warning: Path not found for 'remove': {path_str}"); continue
                                operation_successful = True
                            except (KeyError, IndexError, TypeError) as e:
                                print(f"    Error applying patch operation {op_item}: {e}. Path: {path_str}")
                    else: # Fallback to direct field update if payload is not a list of ops
                         target_record.update(payload)
                         operation_successful = True
            else: print(f"  Warning: Record not found for update: {identifier}")
        elif is_object_map_collection: 
            key = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if key: 
                target_record = data_to_edit_or_list[key]
                if dry_run: print(f"  DRY RUN: Would update record with key '{key}' with patch operations:\n{json.dumps(payload, indent=4)}")
                else: 
                    print(f"  Updating record with key '{key}'")
                    if isinstance(payload, list): # JSON Patch style payload
                        for op_item in payload: # Similar patch logic as above for list items
                            path_str = op_item.get("path", "")
                            op_type = op_item.get("op")
                            value = op_item.get("value")
                            path_segments = [seg for seg in path_str.strip("/").split("/") if seg]
                            current_target = target_record
                            try:
                                for i, segment in enumerate(path_segments[:-1]):
                                    current_target = current_target[int(segment) if segment.isdigit() and isinstance(current_target, list) else segment]
                                final_segment = path_segments[-1] if path_segments else None
                                if op_type == "replace": 
                                    if final_segment is None: data_to_edit_or_list[key] = value # Replace whole record object
                                    else: current_target[int(final_segment) if final_segment.isdigit() and isinstance(current_target, list) else final_segment] = value
                                elif op_type == "add": 
                                    if isinstance(current_target, list) and final_segment == '-': current_target.append(value)
                                    elif isinstance(current_target, list) and final_segment.isdigit(): current_target.insert(int(final_segment), value)
                                    else: current_target[final_segment] = value
                                elif op_type == "remove": 
                                    if final_segment is None: print(f"    Warning: 'remove' path cannot be empty for map item value."); continue
                                    if isinstance(current_target, list) and final_segment.isdigit(): del current_target[int(final_segment)]
                                    elif isinstance(current_target, dict) and final_segment in current_target : del current_target[final_segment]
                                    else: print(f"    Warning: Path not found for 'remove': {path_str}"); continue
                                operation_successful = True
                            except (KeyError, IndexError, TypeError) as e:
                                print(f"    Error applying patch operation {op_item} to record {key}: {e}")
                    else:
                        target_record.update(payload)
                        operation_successful = True
            else: print(f"  Warning: Record not found for update (key: {identifier.get(id_field)})")
            
    elif action == "add":
        if not payload: print(f"Warning: 'add' missing payload. Edit: {edit_request}"); return False
        if is_list_collection: 
            add_id_val = payload.get(id_field) 
            add_ident_for_check = {id_field: add_id_val}
            if config_details.get("secondary_id_field"): add_ident_for_check[config_details["secondary_id_field"]] = payload.get(config_details["secondary_id_field"])
            if "page" in payload and payload.get("page") is not None: add_ident_for_check["page"] = payload.get("page")
            if find_record_index_or_key(data_to_edit_or_list, add_ident_for_check, config_details) != -1:
                print(f"  Warning: Record identified by {add_ident_for_check} already exists. Skipping add."); return False
            display_name_for_log = payload.get("name", payload.get(id_field, "Unknown new record"))
            if dry_run: print(f"  DRY RUN: Would add new record '{display_name_for_log}':\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record: {display_name_for_log}"); data_to_edit_or_list.append(payload) 
            operation_successful = True
        elif is_object_map_collection: 
            add_key = identifier.get(id_field) 
            if not add_key: print(f"Warning: 'add' to object map missing '{id_field}' in identifier. Edit: {edit_request}"); return False
            if add_key in data_to_edit_or_list: print(f"  Warning: Record with key '{add_key}' already exists. Skipping add."); return False
            if dry_run: print(f"  DRY RUN: Would add new record with key '{add_key}':\n{json.dumps(payload, indent=4)}")
            else: print(f"  Adding new record with key '{add_key}'"); data_to_edit_or_list[add_key] = payload
            operation_successful = True

    elif action == "delete":
        if not identifier: print(f"Warning: 'delete' missing identifier. Edit: {edit_request}"); return False
        if is_list_collection:
            idx = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if idx != -1:
                rec_data = data_to_edit_or_list[idx] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record identified by {identifier}:\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record identified by {identifier}"); del data_to_edit_or_list[idx]
                operation_successful = True
            else: print(f"  Warning: Record not found for delete: {identifier}")
        elif is_object_map_collection: 
            key = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if key:
                rec_data = data_to_edit_or_list[key] if dry_run else {}
                if dry_run: print(f"  DRY RUN: Would delete record with key '{key}':\n{json.dumps(rec_data, indent=4)}")
                else: print(f"  Deleting record with key '{key}'"); del data_to_edit_or_list[key]
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
        
        is_single_object_content_for_this_batch = edits_for_file[0].get("is_single_object", config_entry.get("is_single_object_content", False))

        target_data_obj_original = None
        if os.path.exists(file_path):
            target_data_obj_original = load_json_file(file_path)
            if not target_data_obj_original: print(f"Error: Could not load target file {file_path}. Skipping."); continue
        elif all(edit.get("action") == "add" for edit in edits_for_file):
             print(f"Target file {file_path} not found. Will simulate/create new file for 'add' operations.")
             if is_single_object_content_for_this_batch: target_data_obj_original = {} # New single object (content) file starts empty
             elif config_entry.get("data_wrapper_key"): 
                 target_data_obj_original = {
                     config_entry["data_wrapper_key"]: {
                         "description": f"Compilation of {target_key.split('#')[0].replace('_', ' ').title()}", 
                         config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}
                     }
                 }
             else: # Top-level collections (like npc_profiles#pcs)
                 target_data_obj_original = {
                     config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}
                 }
        else: print(f"Error: Target file {file_path} not found and not all edits 'add'. Skipping."); continue
        
        target_data_obj_modified = json.loads(json.dumps(target_data_obj_original)) 

        actual_data_to_operate_on = None # This will be the list, the map, or the single root object / single wrapped object
        if config_entry.get("data_wrapper_key"):
            if config_entry["data_wrapper_key"] not in target_data_obj_modified: print(f"Error: File {file_path} missing wrapper '{config_entry['data_wrapper_key']}'. Skip batch."); continue
            parent_of_collection = target_data_obj_modified[config_entry["data_wrapper_key"]]
            if is_single_object_content_for_this_batch: # The content of the wrapper is the single object
                actual_data_to_operate_on = parent_of_collection
            elif config_entry["collection_key"] in parent_of_collection:
                actual_data_to_operate_on = parent_of_collection[config_entry["collection_key"]]
            else: print(f"Error: File {file_path} missing collection '{config_entry['collection_key']}' in wrapper. Skip batch."); continue
        else: # No wrapper, collection_key points to top-level list/map, OR it's a single root object
            if is_single_object_content_for_this_batch: # Flag from edit request says treat whole file as single object
                actual_data_to_operate_on = target_data_obj_modified
            elif config_entry["collection_key"] in target_data_obj_modified: # e.g. npc_profiles#pcs
                actual_data_to_operate_on = target_data_obj_modified[config_entry["collection_key"]]
            else: print(f"Error: File {file_path} missing collection '{config_entry['collection_key']}' at root. Skip batch."); continue

        if actual_data_to_operate_on is None: print(f"Error: Could not determine data to operate on for {target_key}."); continue
        
        file_would_be_modified = False; edits_applied_this_file_count = 0
        for edit_request in edits_for_file:
            if apply_edit(actual_data_to_operate_on, edit_request, dry_run=dry_run, config_details=config_entry, is_single_object_override=is_single_object_content_for_this_batch): 
                file_would_be_modified = True; edits_applied_this_file_count +=1
        
        if file_would_be_modified:
            total_edits_processed_successfully += edits_applied_this_file_count
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
                save_updated_json_file(target_data_obj_modified, file_path, config_entry, is_single_object_from_edit_flag=is_single_object_content_for_this_batch) 
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
    if args.npc_profile_file and args.npc_profile_file != NPC_PROFILE_FILE_PATH: 
        print(f"Overriding NPC Profile file path to: {args.npc_profile_file} from command line.")
        NPC_PROFILE_FILE_PATH = args.npc_profile_file 
    
    populate_initial_config(npc_profile_path_to_use) 
    
    main(args.edits_file, args.root_path, args.dry_run)

# --- SCRIPT VERSION LOG ---
# Version 2.4.5 (2025-05-27):
# - Refined `generate_dynamic_target_files_config` to default newly discovered/empty/unrecognized files
#   to a SAGA Index list structure (`is_single_object_content: false` in config). The `is_single_object: true`
#   flag in an edit request becomes the primary driver for treating such a file's content as a single object.
# - Renamed `is_single_object` in config to `is_single_object_content` for clarity (content within wrapper).
# - Ensured `apply_edit` correctly handles "add" operations for "single object (dynamic key)" files
#   by using the `id_field` from the payload as the top-level key if the file's content is treated as single object.
# - Standardized the determination of `is_single_object_for_this_batch` in `main` to primarily
#   use the config, allowing override by the first edit request's flag.
# - Updated `save_updated_json_file` to correctly reorder keys for single object content within wrappers.
#
# Version 2.4.4 (2025-05-27):
# - Modified `find_record_index_or_key` to add optional "page" lookup for SAGA Index items.
#
# Version 2.4.3 (2025-05-27):
# - Modified `find_record_index_or_key` to prioritize generic "id" for SAGA Index list items.
#
# Version 2.4.2 (2025-05-27):
# - Refined `generate_dynamic_target_files_config` default behavior.
# - Corrected `apply_edit` for "add" to single-object files with dynamic keys.
# - Ensured consistent `is_single_object` flag usage in `main`.
#
# Version 2.4.1 (2025-05-26):
# - Corrected NameError for `DEFAULT_SINGLE_OBJECT_TOP_KEYS`.
#
# (Older version log entries omitted for brevity)
