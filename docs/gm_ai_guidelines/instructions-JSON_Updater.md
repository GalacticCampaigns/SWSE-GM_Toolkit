Instructions for AI: Generating JSON Edits for SAGA Index Data & Character Profiles
===================================================================================

Version 5.2 (2025-06-04)

1\. Introduction
----------------

This document outlines the format for providing JSON-based edits to update structured data files (e.g., SAGA Index item files, Character Profiles, Rule Set configurations). The `json_updater.py` script is designed to process these edits. Adherence to this format is crucial for successful and predictable data updates.

2\. Overall Structure of the Edit File
--------------------------------------

The edit file itself must be a JSON array. Each element in this array is an "edit request object." This structure allows for batching multiple edits, potentially across different data files, in a single transaction.

Example Root Structure:

    [
      {
        "target_file_key": "string",
        "action": "string",
        "is_single_object": false,
        "identifier": {"key": "value"},
        "payload": [
          {"op": "operation", "path": "/path_relative_to_record", "value": "new_value"}
        ]
      },
      {
        "target_file_key": "string",
        "action": "string",
        "is_single_object": true,
        "identifier": {},
        "payload": [
          {"op": "operation", "path": "/path_from_data_wrapper_content_root", "value": "new_value"}
        ]
      }
    ]
    

*   `is_single_object` (boolean, optional):
    
    *   Set to `true` if the `target_file_key` refers to a JSON file where the content _within its primary `*_data` wrapper_ (e.g., inside `class_rules_data`) is to be treated as a single object for path-based operations. Also use for files that are genuinely single root objects without a wrapper, if any exist and are configured as such.
        
    *   If omitted or `false` (default for SAGA Index item files like `armor.json`), the script assumes the target file contains a list of records within its `*_data` -> `*_list` structure.
        
*   `payload` for "update" actions is an array of patch operations (see Section V).
    

### II. `target_file_key`

This string specifies the target data. Assumes all primary data files (SAGA Index lists and Single Object Rule/Lore files) have a top-level `{filename_base}_data` wrapper.

*   For files containing a list of records (e.g., SAGA Index files like `armor.json`, `feats.json`, `vehicles.json`):
    
    *   `target_file_key` is the filename base (e.g., `"vehicles"`).
        
    *   `is_single_object` should be omitted or `false`. Paths in update payloads are relative to the identified record in the `*_list`.
        
*   For files where the content of the `*_data` wrapper is a single object (e.g., `class_rules.json`, `ability_system_rules.json`):
    
    *   `target_file_key` is the filename base (e.g., `"class_rules"`).
        
    *   Include `"is_single_object": true`. Paths in update payloads are relative to the object _inside_ the `*_data` wrapper (see Section V for path details).
        
*   For multi-collection files (e.g., `WIDT_NPCS.json`): Use `filename_base#collection_name` (e.g., `"WIDT_NPCS#pcs"`). Do not use `is_single_object: true`.
    

### III. `action`

Defines the operation: `"update"`, `"add"`, `"delete"`.

### IV. `identifier`

Uniquely locates records or target keys.

*   For SAGA Index files (list-based, `is_single_object: false` or omitted):
    
    *   Preferred: `{"id":"unique_item_id"}`
        
    *   Fallback: `{"name":"Item Name", "source_book":"CR", "page":123}`
        
    *   For `"add"` to lists, `identifier` is not used by the script.
        
*   For NPC Profile collections (`is_single_object: false` or omitted):
    
    *   `...#pcs`: `{"pc_id": "PC001"}`
        
    *   `...#factions` (object map): `{"faction_id": "FACTION_ID_001"}` (also for "add" key)
        
*   For 'Single Object' files (when `is_single_object: true`):
    
    *   Type A (Config-like, e.g., content of `class_rules_data`):
        
        *   `action: "update"`: `identifier` is not used.
            
        *   `action: "add"` (adding top-level keys within the `*_data` wrapper content): `identifier` is not used.
            
        *   `action: "delete"`: `identifier` must be `{"keys_to_delete": ["key1_to_remove_from_wrapper_content"]}`.
            
    *   Type B (Dynamic-key object within wrapper, e.g., if `vehicles_data` contained a map of vehicle IDs):
        
        *   `action: "update"` or `action: "delete"`: `identifier` uses the key (e.g., `{"id": "vehicle_id_key"}`).
            
        *   `action: "add"`: `identifier` not needed if key is from `payload.id`.
            

### V. `payload`

*   For `"add"` action:
    
    *   To a LIST (e.g., `vehicle_list` in `vehicles_data`): `payload` is the complete new record object itself.
        
    *   To an OBJECT MAP (e.g., `factions` in `WIDT_NPCS.json`): `identifier` specifies the new key. `payload` is the complete new value object.
        
    *   To 'Single Object' content (Type A - config-like, `is_single_object: true`): `payload` is an object where its keys are new keys to add/replace within the `*_data` wrapper's content.
        
    *   To 'Single Object' content (Type B - dynamic-key, `is_single_object: true`): `payload` is the complete new record object. Script uses `payload[config.id_field]` as the new key within the `*_data` wrapper's content.
        
*   For `"update"` action:
    
    *   `payload` is an array of patch operation objects: `{"op": "string", "path": "string", "value": "any"}`
        
        *   `"op"`: `"replace"`, `"add"`, `"remove"`.
            
        *   `"path"`: JSON Pointer string (RFC 6901).
            
            *   For list-based items (`is_single_object: false` or omitted): Path is relative to the identified record object. (e.g., to change the `name` of a feat, path is `"/name"`).
                
            *   For single-object content (`is_single_object: true`): Path is relative to the content of the `*_data` wrapper. (e.g., if `skill_rules.json` has `{"skill_rules_data": {"general_info": "..."}}`, to update `general_info`, the path is `"/general_info"`). Do NOT include the `*_data` wrapper key itself in these paths.
                
        *   `"value"`: New value for "replace"/"add". Omitted for "remove".
            
    *   JSON Pointer Paths (`path`): Start with `/`. Segments separated by `/`. Special characters `~` and `/` in segments are encoded as `~0` and `~1`.
        

Field Naming and Data Types in `value`:

*   `snake_case` for field names. Adhere to schemas.
    

### VI. Examples

1\. Add a Vehicle to `vehicles.json` (as a SAGA Index list file):

    {
      "target_file_key": "vehicles",
      "action": "add", 
      "is_single_object": false, 
      "payload": {
        "id": "laati_gunship_cr", 
        "name": "LAAT/i Gunship", 
        "source_book": "CR", 
        "page": 176 
        /*...other vehicle data...*/
      }
    }
    

2\. Update a Nested Description in `class_rules.json` (Single Object content within `class_rules_data`):

    {
      "target_file_key": "class_rules",
      "action": "update",
      "is_single_object": true,
      "payload": [
        {"op": "replace", "path": "/multiclass_characters/description", "value": "A new, concise description of multiclassing."}
      ]
    }
    

_(Path is relative to the content of `class_rules_data`)_

3\. Update a specific skill application in `skills.json` (SAGA Index list file):

    {
      "target_file_key": "skills",
      "action": "update",
      "is_single_object": false,
      "identifier": { "id": "acrobatics_cr" },
      "payload": [
        { "op": "replace", "path": "/common_uses/4/description", "value": "Updated description for Acrobatics common use at index 4."}
      ]
    }
    

_(Path is relative to the "acrobatics\_cr" skill object found in `skills_list`)_

Version Log
-----------

_This section is for tracking changes to these instructions. For the script's version log, see the comments within the `json_updater.py` file._

*   Version 5.2 (2025-06-04):
    
    *   CRITICAL CLARIFICATION for `path` in "update" operations (Section V): Explicitly stated that for `is_single_object: true` files that have a `*_data` wrapper (like `class_rules.json`), the JSON Pointer `path` must be relative to the _content of that wrapper_, not starting with the wrapper key itself. Example 2 updated for `class_rules.json`.
        
    *   Minor clarifications on identifier usage for different file types.
        
*   Version 5.1 (2025-05-30):
    
    *   Reformatted JSON examples in Section I and VI for improved human readability.
        
*   Version 5.0 (2025-05-27):
    
    *   Major Change: Replaced "update" `payload` structure to be an array of patch operations.
        
*   (Older version log entries omitted for brevity)
