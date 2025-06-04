import json
import os
import re 
import argparse
import shutil
from datetime import datetime

# --- SCRIPT VERSION INFO ---
SCRIPT_VERSION = "2.4.14" 
SCRIPT_LAST_UPDATED = "2025-06-04"

# --- SCRIPT INSTRUCTIONS & SETUP ---
"""
JSON Updater Script for SAGA Edition Data & Character Profiles
Version: {SCRIPT_VERSION}
Last Updated: {SCRIPT_LAST_UPDATED}

Purpose:
This script applies batch edits (add, update, delete) to structured JSON data files.
It dynamically discovers JSON files and can handle:
1. SAGA Index item files (list of records within a wrapped structure).
2. Single complex JSON object files (e.g., rule sets) - indicated by an "is_single_object": true flag
   in the edit request.
3. Multi-collection files (e.g., Character Profiles) - configured statically.
It also adds/updates a "last_modified" timestamp at the root of any file it saves.
Ensures only one backup per physical file is made per script run.

Prerequisites & Usage: See command line help (python json_updater.py -h) and
the "Instructions for AI: Generating JSON Edits" document.
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
DEFAULT_CONFIG_OBJECT_TOP_KEYS = ["file_description", "source_book_reference", "page_reference_general", "last_modified"] 
DEFAULT_DYNAMIC_KEY_OBJECT_TOP_KEYS = ["last_modified"] 

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
            "is_object_map": details.get("is_object_map", False), "is_single_object_content": False, 
            "sort_key": details.get("sort_key"), 
            "preferred_top_keys": details.get("preferred_top_keys", []), 
            "preferred_object_keys": [], 
            "preferred_root_keys": ["last_modified", "pcs", "npcs", "factions", "npc_stat_blocks"] 
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
                    
                    is_single_obj_content_inferred = False 
                    preferred_keys_for_list_records = DEFAULT_SAGA_INDEX_TOP_KEYS.copy()
                    preferred_keys_for_single_object_content = [] 
                    preferred_keys_root_default = ["last_modified", f"{target_file_key}_data"] 
                    id_field_inferred = "name" 
                    secondary_id_inferred = "source_book"
                    sort_key_inferred = "name" 
                    data_key_conv = f"{target_file_key}_data" 
                    list_key_conv = f"{target_file_key}_list" 
                    
                    json_content_peek = load_json_file(full_file_path)
                    if not json_content_peek: 
                        print(f"    Warning: Could not load/parse {filename_with_ext}. Assuming new SAGA Index List structure for config.")
                        is_single_obj_content_inferred = False
                    elif isinstance(json_content_peek, dict):
                        if data_key_conv in json_content_peek and isinstance(json_content_peek.get(data_key_conv), dict):
                            wrapped_content = json_content_peek[data_key_conv]
                            if list_key_conv in wrapped_content and isinstance(wrapped_content.get(list_key_conv), list):
                                is_single_obj_content_inferred = False 
                                preferred_keys_for_single_object_content = [] 
                                print(f"    Inferred '{target_file_key}' as SAGA Index List structure (wrapped).")
                            else: 
                                is_single_obj_content_inferred = True
                                list_key_conv = None 
                                id_field_inferred = None 
                                secondary_id_inferred = None
                                sort_key_inferred = None
                                preferred_keys_for_list_records = [] 
                                preferred_keys_for_single_object_content = DEFAULT_CONFIG_OBJECT_TOP_KEYS.copy() 
                                if base_filename not in ["class_rules", "combat_rules", "skill_rules", "eras_overview", "force_traditions_lore"]:
                                    id_field_inferred = "id" 
                                    preferred_keys_for_single_object_content = DEFAULT_DYNAMIC_KEY_OBJECT_TOP_KEYS.copy()
                                print(f"    Inferred '{target_file_key}' as Single Object Content (within wrapper '{data_key_conv}'). ID field for dynamic keys: '{id_field_inferred}'.")
                        else: 
                            print(f"    File '{filename_with_ext}' does not have expected wrapper '{data_key_conv}'. Assuming SAGA Index List structure config (will create wrapper).")
                            is_single_obj_content_inferred = False 
                            preferred_keys_for_single_object_content = [] 
                    else: 
                        print(f"    Warning: File {filename_with_ext} is not a JSON object at root. Assuming SAGA Index List structure config.")
                        is_single_obj_content_inferred = False
                        preferred_keys_for_single_object_content = [] 

                    config[target_file_key] = {"full_path": full_file_path, "data_wrapper_key": data_key_conv, "collection_key": list_key_conv,
                        "id_field": id_field_inferred, "secondary_id_field": secondary_id_inferred,
                        "is_list_of_objects": not is_single_obj_content_inferred, 
                        "is_single_object_content": is_single_obj_content_inferred, 
                        "is_object_map": False, "sort_key": sort_key_inferred, 
                        "preferred_top_keys": preferred_keys_for_list_records, # Corrected variable name here
                        "preferred_object_keys": preferred_keys_for_single_object_content, 
                        "preferred_root_keys": preferred_keys_root_default
                        }
                    print(f"    Discovered and configured: '{target_file_key}' -> {full_file_path} (Config: is_single_object_content: {is_single_obj_content_inferred})")
    return config

def reorder_record_keys(record_dict, preferred_keys):
    if not isinstance(record_dict, dict) or not preferred_keys: return record_dict
    ordered_record = {}; 
    temp_dict = record_dict.copy() 
    for key in preferred_keys:
        if key in temp_dict: ordered_record[key] = temp_dict.pop(key) 
    for key in sorted(temp_dict.keys()): 
        ordered_record[key] = temp_dict[key]
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
    
    data_wrapper_key = config_entry.get("data_wrapper_key")
    collection_key = config_entry.get("collection_key") 
    
    full_data_obj["last_modified"] = datetime.now().isoformat(timespec='seconds')
    
    if data_wrapper_key and data_wrapper_key in full_data_obj: 
        data_to_process = full_data_obj[data_wrapper_key]
        if is_single_object_content_file_type: 
            current_preferred_keys = config_entry.get("preferred_object_keys", DEFAULT_CONFIG_OBJECT_TOP_KEYS)
            full_data_obj[data_wrapper_key] = reorder_record_keys(data_to_process, current_preferred_keys)
        else: 
            if not collection_key or collection_key not in data_to_process: print(f"Error: save - collection '{collection_key}' missing in wrapper for {output_path}."); return
            actual_collection = data_to_process[collection_key]
            record_preferred_keys = config_entry.get("preferred_top_keys", DEFAULT_SAGA_INDEX_TOP_KEYS) 
            is_list = config_entry.get("is_list_of_objects", False) 
            sort_key = config_entry.get("sort_key")

            if is_list:
                if isinstance(actual_collection, list):
                    reordered_collection = [reorder_record_keys(record, record_preferred_keys) for record in actual_collection]
                    if sort_key: data_to_process[collection_key] = sorted(reordered_collection, key=lambda x: str(x.get(sort_key, "")))
                    else: data_to_process[collection_key] = reordered_collection
                else: print(f"Warning: Expected list for '{collection_key}', found {type(actual_collection)}. Skip sort/reorder.")
            else: 
                if isinstance(actual_collection, dict):
                    reordered_map = {}
                    for key_map in sorted(actual_collection.keys()): 
                        reordered_map[key_map] = reorder_record_keys(actual_collection[key_map], record_preferred_keys) 
                    data_to_process[collection_key] = reordered_map
                else: print(f"Warning: Expected object map for '{collection_key}', found {type(actual_collection)}. Skip key reorder.")
    elif not data_wrapper_key and collection_key and collection_key in full_data_obj: 
        actual_collection = full_data_obj[collection_key]
        is_list = config_entry.get("is_list_of_objects", False)
        is_object_map = config_entry.get("is_object_map", False)
        sort_key = config_entry.get("sort_key")
        record_preferred_keys = config_entry.get("preferred_top_keys", [])
        
        if is_list:
            if isinstance(actual_collection, list):
                reordered_collection = [reorder_record_keys(record, record_preferred_keys) for record in actual_collection]
                if sort_key: full_data_obj[collection_key] = sorted(reordered_collection, key=lambda x: str(x.get(sort_key, "")))
                else: full_data_obj[collection_key] = reordered_collection
            else: print(f"Warning: Expected list for top-level '{collection_key}', found {type(actual_collection)}. Skip sort/reorder.")
        elif is_object_map:
            if isinstance(actual_collection, dict):
                reordered_map = {}
                for key_map in sorted(actual_collection.keys()): 
                    reordered_map[key_map] = reorder_record_keys(actual_collection[key_map], record_preferred_keys)
                full_data_obj[collection_key] = reordered_map
            else: print(f"Warning: Expected object map for top-level '{collection_key}', found {type(actual_collection)}. Skip key reorder.")
    elif is_single_object_content_file_type and not data_wrapper_key and not collection_key : 
         current_preferred_keys = config_entry.get("preferred_object_keys", DEFAULT_CONFIG_OBJECT_TOP_KEYS)
         if not current_preferred_keys and isinstance(full_data_obj, dict): 
             temp_obj_for_reorder = full_data_obj.copy() 
             full_data_obj.clear()
             if "last_modified" in temp_obj_for_reorder: 
                 full_data_obj["last_modified"] = temp_obj_for_reorder.pop("last_modified")
             for key in sorted(temp_obj_for_reorder.keys()): 
                 if key in temp_obj_for_reorder: full_data_obj[key] = temp_obj_for_reorder[key]
         elif current_preferred_keys : 
            full_data_obj = reorder_record_keys(full_data_obj, current_preferred_keys) 
    else:
        print(f"Error: Save - Cannot determine data structure for {output_path} with config: {config_entry}")
        return
    
    if isinstance(full_data_obj, dict):
        root_preferred_keys = config_entry.get("preferred_root_keys", ["last_modified"])
        if "last_modified" not in root_preferred_keys: 
            root_preferred_keys.insert(0, "last_modified")
        
        primary_data_container_key = data_wrapper_key if data_wrapper_key else collection_key
        if primary_data_container_key and primary_data_container_key not in root_preferred_keys:
            idx = root_preferred_keys.index("last_modified") if "last_modified" in root_preferred_keys else -1
            root_preferred_keys.insert(idx + 1, primary_data_container_key)
        
        temp_full_obj = full_data_obj.copy()
        full_data_obj.clear()
        for key in root_preferred_keys:
            if key in temp_full_obj: full_data_obj[key] = temp_full_obj.pop(key)
        for key in sorted(temp_full_obj.keys()): full_data_obj[key] = temp_full_obj[key]
            
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(full_data_obj, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated and saved {config_entry.get('target_file_key', os.path.basename(output_path))} JSON to: {output_path}")
    except Exception as e: print(f"Error writing {os.path.basename(output_path)} JSON to file {output_path}: {e}")


def _decode_json_pointer_segment(segment):
    return segment.replace("~1", "/").replace("~0", "~")

def find_record_index_or_key(data_collection, identifier, config_details, is_single_object_content_override=False):
    if is_single_object_content_override: return True 
    
    is_list = config_details.get("is_list_of_objects", True) 
    
    identifier_id_val = identifier.get("id") 
    if identifier_id_val: 
        if is_list:
            if not isinstance(data_collection, list): return -1
            for index, record in enumerate(data_collection):
                if record.get("id") == identifier_id_val: return index
            print(f"  Info: Record with 'id': \"{identifier_id_val}\" not found by dedicated ID lookup.") 
            return -1 
        else: 
            if not isinstance(data_collection, dict): return None
            if identifier_id_val in data_collection: return identifier_id_val
            print(f"  Info: Record with key: \"{identifier_id_val}\" not found in object map.")
            return None

    configured_id_field = config_details.get("id_field") 
    secondary_id_field = config_details.get("secondary_id_field") 
    identifier_primary_value = identifier.get(configured_id_field)
    if not identifier_primary_value and configured_id_field:
        if not identifier_id_val: 
            print(f"Warning: Identifier missing primary configured ID field '{configured_id_field}'.")
        return -1 if is_list else None
        
    identifier_secondary_value = identifier.get(secondary_id_field) if secondary_id_field else None
    identifier_page_value = identifier.get("page") 

    if is_list:
        if not isinstance(data_collection, list): return -1
        for index, record in enumerate(data_collection):
            if record.get(configured_id_field) == identifier_primary_value:
                match_secondary = True 
                if secondary_id_field and identifier_secondary_value is not None: 
                    match_secondary = (record.get(secondary_id_field) == identifier_secondary_value)
                elif secondary_id_field and identifier_secondary_value is None: 
                    match_secondary = (record.get(secondary_id_field) is None or record.get(secondary_id_field) == "")
                if match_secondary:
                    match_page = True 
                    if identifier_page_value is not None: 
                        if "page" in record:
                            match_page = (str(record.get("page")) == str(identifier_page_value))
                        else: 
                            match_page = False
                    if match_page: return index
        return -1 
    else: 
        if not isinstance(data_collection, dict): return None
        return identifier_primary_value if identifier_primary_value in data_collection else None


def apply_edit(data_to_edit_or_list, edit_request, dry_run=False, config_details=None, is_single_object_content_override=False): 
    action = edit_request.get("action"); identifier = edit_request.get("identifier"); payload = edit_request.get("payload")
    if not config_details: print(f"Error: apply_edit missing config_details. Edit: {edit_request}"); return False
    id_field = config_details.get("id_field"); is_list_collection = config_details.get("is_list_of_objects", False) 
    is_object_map_collection = config_details.get("is_object_map", False); operation_successful = False

    if is_single_object_content_override: 
        target_object_for_patch = data_to_edit_or_list 
        if action == "update": 
            if not payload: print(f"Warning: 'update' for single object content missing payload."); return False
            if isinstance(payload, list): 
                if dry_run: print(f"  DRY RUN: Would apply patch operations to single object content:\n{json.dumps(payload, indent=4)}")
                else: 
                    print(f"  Applying patch operations to single object content.")
                    for op_item in payload:
                        path_str = op_item.get("path", "").strip("/")
                        op_type = op_item.get("op"); value = op_item.get("value")
                        path_segments_encoded = [seg for seg in path_str.split("/") if seg] if path_str else []
                        path_segments = [_decode_json_pointer_segment(seg) for seg in path_segments_encoded]
                        current_target_obj = target_object_for_patch
                        try:
                            for i, segment in enumerate(path_segments[:-1]):
                                current_target_obj = current_target_obj[int(segment) if segment.isdigit() and isinstance(current_target_obj, list) else segment]
                            final_segment = path_segments[-1] if path_segments else None
                            if op_type == "replace":
                                if final_segment is None and not path_segments: print(f"    Warning: 'replace' root of single object content requires path to a key."); continue 
                                elif final_segment is None: print(f"    Warning: Invalid 'replace' path: {path_str}"); continue
                                else: current_target_obj[int(final_segment) if final_segment.isdigit() and isinstance(current_target_obj, list) else final_segment] = value
                            elif op_type == "add":
                                if isinstance(current_target_obj, list) and final_segment == '-': current_target_obj.append(value)
                                elif isinstance(current_target_obj, list) and final_segment and final_segment.isdigit(): current_target_obj.insert(int(final_segment), value)
                                elif isinstance(current_target_obj, dict): 
                                    if final_segment is None: print(f"    Warning: 'add' to object root requires a key in path: {path_str}"); continue
                                    current_target_obj[final_segment] = value
                                else: print(f"    Warning: 'add' target is not list or object: {path_str}"); continue
                            elif op_type == "remove":
                                if final_segment is None: print(f"    Warning: 'remove' path cannot be empty."); continue
                                if isinstance(current_target_obj, list) and final_segment.isdigit(): del current_target_obj[int(final_segment)]
                                elif isinstance(current_target_obj, dict) and final_segment in current_target_obj : del current_target_obj[final_segment]
                                else: print(f"    Warning: Path not found for 'remove': {path_str}"); continue
                            operation_successful = True
                        except (KeyError, IndexError, TypeError) as e: print(f"    Error applying patch operation {op_item}: {e}. Path: /{'/'.join(path_segments)}")
            elif isinstance(payload, dict): 
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

    target_record_or_map_value = None; idx_or_key_for_update = None
    if action == "update":
        if not identifier or not payload: print(f"Warning: 'update' missing identifier/payload."); return False
        if not isinstance(payload, list): print(f"Warning: 'update' payload must be a list of patch operations."); return False
        if is_list_collection:
            idx_or_key_for_update = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if idx_or_key_for_update != -1: target_record_or_map_value = data_to_edit_or_list[idx_or_key_for_update]
        elif is_object_map_collection:
            idx_or_key_for_update = find_record_index_or_key(data_to_edit_or_list, identifier, config_details)
            if idx_or_key_for_update: target_record_or_map_value = data_to_edit_or_list[idx_or_key_for_update]
        if target_record_or_map_value:
            if dry_run: print(f"  DRY RUN: Would apply patch operations to record identified by {identifier}:\n{json.dumps(payload, indent=4)}")
            else: print(f"  Applying patch operations to record identified by {identifier}")
            for op_item in payload: 
                path_str = op_item.get("path", "").strip("/"); op_type = op_item.get("op"); value = op_item.get("value")
                path_segments_encoded = [seg for seg in path_str.split("/") if seg] if path_str else []
                path_segments = [_decode_json_pointer_segment(seg) for seg in path_segments_encoded]
                current_target_in_record = target_record_or_map_value
                try:
                    for i, segment in enumerate(path_segments[:-1]):
                        current_target_in_record = current_target_in_record[int(segment) if segment.isdigit() and isinstance(current_target_in_record, list) else segment]
                    final_segment = path_segments[-1] if path_segments else None
                    if op_type == "replace":
                        if final_segment is None and not path_segments: 
                            if is_list_collection: data_to_edit_or_list[idx_or_key_for_update] = value
                            elif is_object_map_collection: data_to_edit_or_list[idx_or_key_for_update] = value
                        elif final_segment is None: print(f"    Warning: Invalid 'replace' path for record item: {path_str}"); continue
                        else: current_target_in_record[int(final_segment) if final_segment.isdigit() and isinstance(current_target_in_record, list) else final_segment] = value
                    elif op_type == "add":
                        if isinstance(current_target_in_record, list) and final_segment == '-': current_target_in_record.append(value)
                        elif isinstance(current_target_in_record, list) and final_segment and final_segment.isdigit(): current_target_in_record.insert(int(final_segment), value)
                        elif isinstance(current_target_in_record, dict): 
                            if final_segment is None: print(f"    Warning: 'add' to object root requires a key in path. Path: {path_str}"); continue
                            current_target_in_record[final_segment] = value
                        else: print(f"    Warning: 'add' target is not list or object. Path: {path_str}"); continue
                    elif op_type == "remove":
                        if final_segment is None: print(f"    Warning: 'remove' path cannot be empty for record item."); continue
                        if isinstance(current_target_in_record, list) and final_segment.isdigit(): del current_target_in_record[int(final_segment)]
                        elif isinstance(current_target_in_record, dict) and final_segment in current_target_in_record : del current_target_in_record[final_segment]
                        else: print(f"    Warning: Path not found for 'remove': {path_str}"); continue
                    operation_successful = True 
                except (KeyError, IndexError, TypeError) as e: print(f"    Error applying patch operation {op_item} to record {identifier}: {e}. Path: /{'/'.join(path_segments)}")
            if not operation_successful and payload: print(f"  Warning: No patch operations successfully applied for update: {identifier}")
            elif not payload: operation_successful = True 
        else: print(f"  Warning: Record not found for update: {identifier}")
    elif action == "add": 
        if not payload: print(f"Warning: 'add' missing payload. Edit: {edit_request}"); return False
        if is_list_collection: 
            add_id_val_check = payload.get(id_field) if id_field else payload.get("id") 
            add_ident_for_check = {id_field if id_field else "id": add_id_val_check}
            if config_details.get("secondary_id_field"): add_ident_for_check[config_details["secondary_id_field"]] = payload.get(config_details["secondary_id_field"])
            if "page" in payload and payload.get("page") is not None: add_ident_for_check["page"] = payload.get("page")
            if find_record_index_or_key(data_to_edit_or_list, add_ident_for_check, config_details) != -1:
                print(f"  Warning: Record identified by {add_ident_for_check} already exists. Skipping add."); return False
            display_name_for_log = payload.get("name", add_id_val_check if add_id_val_check else "Unknown new record")
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
    print(f"--- JSON Updater Script v{SCRIPT_VERSION} ({SCRIPT_LAST_UPDATED}) ---") 
    if dry_run: print("*** DRY RUN MODE ENABLED: No files will be modified. ***\n")
    print(f"Starting JSON update process for edits in: {edits_file_path}")
    print(f"Using SAGA Index root path (for dynamic discovery): {root_path}")

    TARGET_FILES_CONFIG = INITIAL_TARGET_FILES_CONFIG.copy() 
    generate_dynamic_target_files_config(root_path, TARGET_FILES_CONFIG) 
    
    if not TARGET_FILES_CONFIG: print("Error: Failed to generate/load any target files configuration. Exiting."); return

    edit_requests = load_json_file(edits_file_path)
    if not edit_requests or not isinstance(edit_requests, list): print("Error: Edits file is empty, not found, or not a JSON list."); return

    edits_by_target = {}; total_edits_processed_successfully = 0; backed_up_files_this_run = set()
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
             if is_single_object_content_for_this_batch: target_data_obj_original = {} 
             elif config_entry.get("data_wrapper_key"): 
                 target_data_obj_original = {
                     config_entry["data_wrapper_key"]: {
                         "description": f"Compilation of {target_key.split('#')[0].replace('_', ' ').title()}", 
                         config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}
                     }
                 }
             else: 
                 target_data_obj_original = {
                     config_entry["collection_key"]: [] if config_entry.get("is_list_of_objects", True) else {}
                 }
        else: print(f"Error: Target file {file_path} not found and not all edits 'add'. Skipping."); continue
        
        target_data_obj_modified = json.loads(json.dumps(target_data_obj_original)) 

        actual_data_to_operate_on = None 
        if config_entry.get("data_wrapper_key"): 
            if config_entry["data_wrapper_key"] not in target_data_obj_modified: print(f"Error: File {file_path} missing wrapper '{config_entry['data_wrapper_key']}'. Skip batch."); continue
            parent_of_collection = target_data_obj_modified[config_entry["data_wrapper_key"]]
            if is_single_object_content_for_this_batch: 
                actual_data_to_operate_on = parent_of_collection
            elif config_entry.get("collection_key") and config_entry["collection_key"] in parent_of_collection: 
                actual_data_to_operate_on = parent_of_collection[config_entry["collection_key"]]
            elif not config_entry.get("collection_key") and is_single_object_content_for_this_batch: 
                 actual_data_to_operate_on = parent_of_collection
            else: print(f"Error: File {file_path} missing collection '{config_entry['collection_key']}' in wrapper. Skip batch."); continue
        else: 
            if is_single_object_content_for_this_batch: 
                actual_data_to_operate_on = target_data_obj_modified
            elif config_entry.get("collection_key") and config_entry["collection_key"] in target_data_obj_modified: 
                actual_data_to_operate_on = target_data_obj_modified[config_entry["collection_key"]]
            else: print(f"Error: File {file_path} missing collection '{config_entry['collection_key']}' at root. Skip batch."); continue

        if actual_data_to_operate_on is None: print(f"Error: Could not determine data to operate on for {target_key}."); continue
        
        file_would_be_modified = False; edits_applied_this_file_count = 0
        for edit_request in edits_for_file:
            if apply_edit(actual_data_to_operate_on, edit_request, dry_run=dry_run, config_details=config_entry, is_single_object_content_override=is_single_object_content_for_this_batch): 
                file_would_be_modified = True; edits_applied_this_file_count +=1
        
        if file_would_be_modified:
            total_edits_processed_successfully += edits_applied_this_file_count
            if dry_run: print(f"  DRY RUN SUMMARY for {target_key}: {edits_applied_this_file_count} edit(s) would be processed.")
            else:
                if os.path.exists(file_path) and file_path not in backed_up_files_this_run: 
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
                        backed_up_files_this_run.add(file_path) 
                    except Exception as e_backup: print(f"  Error creating backup for {file_path}: {e_backup}")
                save_updated_json_file(target_data_obj_modified, file_path, config_entry, is_single_object_content_from_edit_flag=is_single_object_content_for_this_batch) 
        elif not dry_run: print(f"  No changes processed or would be processed for {target_key}.")

    if dry_run: print(f"\nDRY RUN COMPLETE. {total_edits_processed_successfully} total edits simulated.")
    else: print(f"\nJSON update process complete. Total edits successfully applied: {total_edits_processed_successfully}")

if __name__ == '__main__':
    print(f"--- JSON Updater Script v{SCRIPT_VERSION} ({SCRIPT_LAST_UPDATED}) ---")

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
# Version 2.4.14 (2025-06-04):
# - Corrected UnboundLocalError in `generate_dynamic_target_files_config` by ensuring
#   `preferred_keys_for_single_object_content` is initialized before its potential use
#   when assigning to `preferred_object_keys` in the config dictionary.
# - Ensured `preferred_keys_for_list_records` is consistently used for the `preferred_top_keys`
#   field in the config dictionary for list-based files.
#
# Version 2.4.13 (2025-05-31):
# - Fixed UnboundLocalError for `preferred_keys_list_records` in `generate_dynamic_target_files_config`
#   by ensuring `preferred_keys_for_single_object_content` is initialized correctly in all paths
#   and used for `preferred_object_keys` in the config entry.
# - Synchronized SCRIPT_VERSION and SCRIPT_LAST_UPDATED constants with this log.
#
# Version 2.4.12 (2025-05-30):
# - Ensured `save_updated_json_file` only creates one backup per physical file path per script run
#   by introducing `backed_up_files_this_run` set.
# - Corrected `TypeError` in `apply_edit` by consistently using `is_single_object_content_override`
#   as the parameter name in both definition and calls from `main`.
# - Refined `save_updated_json_file` to correctly handle saving collections that are top-level keys 
#   (e.g., "pcs", "npcs" in NPC Profile files where data_wrapper_key is None).
#
# (Older version log entries omitted for brevity)
