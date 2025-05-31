Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles
===============================================================================

Version 5.1 (2025-05-30)

1\. Introduction
----------------

This document outlines the format for providing JSON-based edits to update structured data files (e.g., SAGA Index item files, Character Profiles, Rule Set configurations). The `json_updater.py` script is designed to process these edits. Adherence to this format is crucial for successful and predictable data updates.

2\. Overall Structure of the Edit File
--------------------------------------

The edit file itself must be a JSON array. Each element in this array is an "edit request object." This structure allows for batching multiple edits, potentially across different data files, in a single transaction.

Example Root Structure:

    [
      {
        "target_file_key": "string", "action": "string", "is_single_object": false, "identifier": {"key": "value"},
        "payload": [
          {"op": "operation", "path": "/path", "value": "new_value"},
          {"op": "operation", "path": "/path", "value": "new_value"}
        ]
      },
      {
        "target_file_key": "string", "action": "string", "is_single_object": true, "identifier": {"keys_to_delete": ["some_key"]},
        "payload": [
          {"op": "operation", "path": "/path", "value": "new_value"},
          {"op": "operation", "path": "/path", "value": "new_value"}
        ]
      }
    ]
    

*   `is_single_object` (boolean, optional):
    
    *   Set to `true` only if the `target_file_key` refers to a JSON file that is fundamentally:
        
        1.  A single configuration object at its root (e.g., `class_rules.json`).
            
        2.  OR a file where individual records are _intentionally_ stored as top-level keys in the root object (e.g., a hypothetical `custom_id_map.json` file structured as `{"id_1": {...}, "id_2": {...}}`).
            
    *   If omitted or `false` (this is the default and correct setting for standard SAGA Index item files like `armor.json`, `feats.json`, `vehicles.json` when they follow the `*_data`/`*_list` structure), the script assumes the target file contains a list of records (potentially within a wrapper object) or is a multi-collection file (like NPC Profiles).
        
*   `payload` for "update" actions is an array of patch operations (see Section V).
    

### II. `target_file_key`

This string specifies which main data category (and thus which JSON file) the edit applies to.

*   For files containing a list of records (e.g., SAGA Index files like `armor.json`, `feats.json`, `vehicles.json`):
    
    *   The `target_file_key` is the filename without the `.json` extension (e.g., `"armor"`, `"vehicles"`).
        
    *   Important: For these files, ensure `is_single_object` is omitted or set to `false` in the edit request. The script will expect a structure like `{"vehicles_data": {"vehicle_list": [...]}}`.
        
*   For files that are genuinely a single JSON object at their root (Type A or Type B described in Section I):
    
    *   The `target_file_key` is the filename without the `.json` extension (e.g., `"class_rules"`).
        
    *   Crucially, include `"is_single_object": true` in the edit request object for these files.
        
*   For multi-collection files (e.g., an NPC Profile file like `WIDT_NPCS.json`): Use a composite key: `filename_base#collection_name`.
    
    *   Example: `"WIDT_NPCS#pcs"`.
        
    *   Do not use `"is_single_object": true` for these multi-collection targets.
        

The `json_updater.py` script uses `target_file_key` and the `is_single_object` flag to locate the correct file and apply edits appropriately based on its dynamically generated or static configuration for that target.

### III. `action`

Defines the operation:

*   `"update"`: Modifies an existing record or a single-object file using a series of patch operations defined in the `payload`. Requires `identifier` (for list/map/dynamic-key single-object files) and `payload` (as an array of operations).
    
*   `"add"`: Adds a new, entirely separate record/entry. Requires `payload` (as the complete new object/value). For object maps or dynamic-key single objects, `identifier` specifies the new key.
    
*   `"delete"`: Removes an existing record/entry or top-level keys from a single-object file. Requires `identifier`.
    

### IV. `identifier` (for "update" and "delete", and "add" to object maps/dynamic-key single objects)

Uniquely locates the record or target keys.

*   For SAGA Index files (list-based, e.g., `target_file_key: "vehicles"`, ensure `is_single_object: false` or omitted):
    
    *   `"id"` (string, optional but preferred if the record has a unique ID field).
        
    *   `"name"` (string, required if `"id"` is not used/available).
        
    *   `"source_book"` (string, recommended if using `"name"`).
        
    *   `"page"` (integer or string, optional, for further disambiguation if using `"name"` and `"source_book"`).
        
    *   For `"add"` to these lists, the `identifier` is typically not used by the script.
        
    *   Example for update/delete (preferred): `{"id":"laati_gunship_cr"}`
        
*   For NPC Profile collections (list-based or object map, `is_single_object: false` or omitted):
    
    *   If targeting `...#pcs`: `{"pc_id": "PC001"}`
        
    *   If targeting `...#npcs`: `{"npc_id": "NPC001"}`
        
    *   If targeting `...#factions` (object map): `{"faction_id": "FACTION_ID_001"}` (also used as the key for "add")
        
    *   If targeting `...#npc_stat_blocks`: `{"npc_id_ref": "NPC001"}`
        
*   For 'Single Object' files (when `is_single_object: true` in the edit request):
    
    *   Type A (Config-like, e.g., `class_rules.json` where payload keys are literal top-level keys):
        
        *   For `action: "update"`: `identifier` is not used by the script (patches apply to root). Can be `{}`.
            
        *   For `action: "add"` (adding/replacing top-level keys): `identifier` is not used. Payload keys are targets.
            
        *   For `action: "delete"`: `identifier` must contain `{"keys_to_delete": ["key1_to_remove"]}`.
            
    *   Type B (Dynamic-key root object, e.g., a hypothetical `ship_manifest.json` structured as `{"ship_id_1":{...}, ...}`):
        
        *   For `action: "update"` or `action: "delete"`: `identifier` uses the key (e.g., `{"id": "ship_id_1"}`).
            
        *   For `action: "add"`: `identifier` is not strictly needed if the key is derived from `payload.id`. Can be `{}`.
            

### V. `payload`

*   For `"add"` action:
    
    *   List-based files/collections: `payload` is the complete new record object itself.
        
    *   Object maps (e.g., `...#factions`): `identifier` specifies the new key. `payload` is the complete new value object.
        
    *   'Single Object' files (Type A - config-like): `payload` is an object where its keys are new top-level keys to add/replace in the target JSON file.
        
    *   'Single Object' files (Type B - dynamic-key root): `payload` is the complete new record object. The script uses `payload[config.id_field]` as the new top-level key.
        
*   For `"update"` action:
    
    *   The `payload` is an array of patch operation objects. Each object specifies a single atomic change.
        
    *   Patch Operation Object Structure:
        
            {"op": "string", "path": "string", "value": "any"}
            
        
        *   `"op"`: Operation - `"replace"`, `"add"`, `"remove"`.
            
        *   `"path"`: JSON Pointer string (RFC 6901) to the target field.
            
            *   For list-based items, path is relative to the identified item.
                
            *   For single-object files, path is from the root of the file's main content object.
                
        *   `"value"`: The new value. Required for `"replace"` and `"add"`. Omitted for `"remove"`.
            
    *   JSON Pointer Paths (`path`): Start with `/`. Segments separated by `/`. (e.g., `/memberName`, `/arrayName/index`, `/arrayName/-` to append). Special characters `~` and `/` in segments are encoded as `~0` and `~1`.
        

Field Naming and Data Types in `value`:

*   `snake_case` for field names.
    
*   Adhere to target's JSON schema.
    

### VI. Examples

1\. Update Armor Cost and Add a Note (SAGA Index list file):

    {
      "target_file_key": "armor", "action": "update", "identifier": {"name": "Combat Jumpsuit", "source_book": "CR"},
      "payload": [
        {"op": "replace", "path": "/cost", "value": {"text_original": "1250 credits", "options": [{"type": "fixed_amount", "value": 1250}], "selection_logic": null}},
        {"op": "add", "path": "/availability", "value": "Common"},
        {"op": "add", "path": "/designer_notes", "value": "Standard issue for planetary militias."}
      ]
    }
    
    

2\. Update a Nested Description in `class_rules.json` (Single Object file):

    {
      "target_file_key": "class_rules", "action": "update", "is_single_object": true,
      "payload": [
        {"op": "replace", "path": "/class_rules_data/multiclass_characters/description", "value": "A new, concise description of multiclassing."}
      ]
    }
    
    

3\. Add a New Vehicle to `vehicles.json` (as a SAGA Index list file; `is_single_object: false` or omitted):

    {
      "target_file_key": "vehicles", "action": "add",
      "payload": {
        "id": "laati_gunship_cr", "name": "LAAT/i Gunship", "source_book": "CR", "page": 176 
        /*...other vehicle data...*/
      }
    }
    
    

4\. Add an entry to a hypothetical `ship_manifest.json` (Single Object with dynamic keys from payload's "id"):

    {
      "target_file_key": "ship_manifest", "action": "add", "is_single_object": true,
      "payload": {
        "id": "millennium_falcon_yt1300", "name": "Millennium Falcon", "class": "YT-1300 light freighter" 
        /*...rest of object...*/
      }
    }
    
    

5\. Remove a Specific Special Quality from a Feat and Change its Benefit Summary:

    {
      "target_file_key": "feats", "action": "update", "identifier": { "name": "Powerful Charge", "source_book": "CR" },
      "payload": [
        { "op": "remove", "path": "/special_qualities/1" },
        { "op": "replace", "path": "/benefit_summary", "value": "New benefit summary after removing one quality." }
      ]
    }
    
    

_(Note: `/special_qualities/1` assumes the quality to remove is at index 1 of the array.)_

Version Log
-----------

_This section is for tracking changes to these instructions. For the script's version log, see the comments within the `json_updater.py` file._

*   Version 5.1 (2025-05-30):
    
    *   Reformatted JSON examples in Section I and VI for improved human readability, using multi-lines for edit request objects and their primary keys, while keeping individual patch operations compact.
        
*   Version 5.0 (2025-05-27):
    
    *   Major Change: Replaced "update" `payload` structure. It is now an array of patch operations (op, path, value), similar to JSON Patch, for granular updates to both list-based records and single-object files.
        
    *   Updated Sections I, III, V, and VI (Examples) to reflect the new path-based update mechanism.
        
*   Version 4.x (Prior to 2025-05-27):
    
    *   Included clarifications on `is_single_object` flag usage, `identifier` and `payload` distinctions for various file types (config-like single objects vs. dynamic-key root objects vs. list-based), and handling of multi-collection files. Added versioning to the document.

