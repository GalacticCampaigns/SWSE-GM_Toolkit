Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles
===============================================================================
Version 6.0 (2025-06-13)

1\. Introduction
----------------
This document outlines the format for providing JSON-based edits to update structured data files (e.g., SAGA Index item files, Character Profiles, Rule Set configurations). The `json_updater.py` script is designed to process these edits. Adherence to this format is crucial for successful and predictable data updates.

2\. Overall Structure of the Edit File
--------------------------------------
The edit file itself must be a JSON Array, starting with `[` and ending with `]`. This array holds one or more "Edit Request Objects." This structure allows for batching multiple edits, potentially across different data files, in a single transaction.
An Edit Request Object is a complete, self-contained instruction for a single operation. It has the following structure:

```JSON
    {
      "target_file_key": "string",
      "action": "string",
      "is_single_object": false,
      "identifier": {},
      "payload": []
    }
```

To perform multiple edits, place each complete Edit Request Object as an element in the root array:

```JSON
    [
      { /* First complete edit request object */ },
      { /* Second complete edit request object */ }
    ]
```

3\. `target_file_key` (String, Required)
----------------------------------------
This string specifies which main data category (and thus which JSON data file) the edit applies to. Each edit request object must target only one data collection.
*   Derivation: The `target_file_key` is the filename without the `.json` extension. The `json_updater.py` script dynamically scans subdirectories under a pre-configured `data/` directory to find these files.
*   For files containing a list of records (e.g., SAGA Index files like `armor.json`, `feats.json`, `vehicles.json`):
    *   The `target_file_key` is the filename base (e.g., `"vehicles"`).
    *   `is_single_object` should be omitted or set to `false`.
    *   The script expects a structure like `{"vehicles_data": {"vehicle_list": [...]}}`.
*   For files where the content of the `*_data` wrapper is a single object (e.g., `class_rules.json`):
    *   The `target_file_key` is the filename base (e.g., `"class_rules"`).
    *   Include `"is_single_object": true`. Paths in update payloads are relative to the object _inside_ the `*_data` wrapper.
*   For multi-collection files (e.g., an NPC Profile file like `SWFO_Profiles.json`):
    *   Use a composite key: `filename_base#collection_name`.
    *   Example: `"SWFO_Profiles#pcs"` to target the `pcs` list, or `"SWFO_Profiles#factions"` to target the `factions` object.
    *   Do not use `"is_single_object": true` for list-based collections within these files (like `#pcs` or `#npcs`). You should use `is_single_object: true` for object map collections that are treated as single objects (like `#factions`).

4\. `is_single_object` (Boolean, Optional)
------------------------------------------
This flag tells the script how to interpret the structure of the target file for the operation.
*   If omitted or `false` (default): The script assumes the target file contains a list of records (e.g., `armor.json` with an `armor_list`).
*   Set to `true`: Use this if the `target_file_key` refers to a JSON file where the content _within_ its primary `*_data` wrapper (e.g., inside `class_rules_data`) is to be treated as a single object for path-based operations.

5\. `action` (String, Required)
-------------------------------
Defines the operation to perform:
*   `"update"`: Modifies an existing record or a single-object file using a series of patch operations defined in the `payload`. Requires `identifier` (for list/map/dynamic-key single-object files) and `payload` (as an array of operations).
*   `"add"`: Adds a new, entirely separate record/entry. Requires `payload` (as the complete new object/value).
*   `"delete"`: Removes an existing record/entry or top-level keys from a single-object file. Requires `identifier`.

6\. `identifier` (Object, Required for `update` & `delete`)
-----------------------------------------------------------
Uniquely locates the record or target keys.
*   For SAGA Index Files (list-based): The script will try to find a match using the following priority:
    1.  `"id"` (string, strongly preferred): The globally unique ID of the record.
        *   Example: `{"id": "feat_weapon_focus_cr"}`
    2.  If `"id"` is not provided or not found, it falls back to:
        *   `"name"` (string, required in this case).
        *   `"source_book"` (string, recommended).
        *   `"page"` (integer/string, optional for further disambiguation).
        *   Example: `{"name": "Weapon Focus", "source_book": "CR", "page": 87}`
*   For NPC Profile Collections:
    *   `...#pcs`: `{"pc_id": "PC001"}`
    *   `...#npcs`: `{"npc_id": "NPC001"}`
    *   `...#factions` (object map): `{"faction_id": "FACTION_ID_001"}` (also used as the key for `"add"`)
    *   `...#npc_stat_blocks`: `{"npc_id_ref": "NPC001"}`
*   For 'Single Object' Files (when `is_single_object: true`):
    *   Type A (Config-like, e.g., `class_rules.json`):
        *   `action: "update"`: `identifier` is not used. Can be `{}`.
        *   `action: "delete"`: `identifier` must be `{"keys_to_delete": ["key_to_remove_from_wrapper_content"]}`.
    *   Type B (Dynamic-key root object):
        *   `action: "update"` or `action: "delete"`: `identifier` uses the key (e.g., `{"id": "some_id_key"}`).
        *   `action: "add"`: `identifier` not needed if key is derived from `payload.id`. Can be `{}`.

7\. `payload` (Object or Array, Required for `add` & `update`)
--------------------------------------------------------------
*   For `"add"` action:
    *   To a LIST (e.g., `vehicle_list`): `payload` is the complete new record object itself.
    *   To an OBJECT MAP (e.g., `factions`): `identifier` specifies the new key. `payload` is the complete new value object.
*   For `"update"` action:
    *   The `payload` is an array of patch operation objects: `{"op": "string", "path": "string", "value": "any"}`
        *   `"op"`: `"replace"`, `"add"`, `"remove"`.
        *   `"path"`: A JSON Pointer string (RFC 6901).
            *   For list-based items (`is_single_object: false`): Path is relative to the identified record object.
            *   For single-object content (`is_single_object: true`): Path is relative to the content of the `*_data` wrapper. Do not include the `*_data` wrapper key itself in the path.
        *   `"value"`: The new value for `"replace"` and `"add"`. Omitted for `"remove"`.
    *   JSON Pointer Paths (`path`): Start with `/`. Segments separated by `/`. Special characters `~` and `/` in segments are encoded as `~0` and `~1`.

8\. Examples
------------
1\. Update an Armor's Cost and Add a Note (SAGA Index list file):

```JSON
    {
      "target_file_key": "armor",
      "action": "update",
      "identifier": {"name": "Combat Jumpsuit", "source_book": "CR"},
      "payload": [
        {"op": "replace", "path": "/cost", "value": {"text_original": "1250 credits", "options": [{"type": "fixed_amount", "value": 1250}], "selection_logic": null}},
        {"op": "add", "path": "/availability", "value": "Common"},
        {"op": "add", "path": "/designer_notes", "value": "Standard issue for planetary militias."}
      ]
    }
```

2\. Update a Nested Description in `class_rules.json` (Single Object content):

```JSON
    {
      "target_file_key": "class_rules",
      "action": "update",
      "is_single_object": true,
      "payload": [
        {"op": "replace", "path": "/multiclass_characters/description", "value": "A new, concise description of multiclassing."}
      ]
    }
```

_(Path is relative to the content of `class_rules_data`)_
3\. Update Multiple Collections within a Single NPC Profile File (`SWFO_Profiles.json`):

```JSON
    [
      {
        "target_file_key": "swfo_profiles#factions",
        "action": "update",
        "is_single_object": true,
        "payload": [
          { "op": "remove", "path": "/PROTECTOR_ORDER_UNKNOWN_CELL_001/npc_members/2" }
        ]
      },
      {
        "target_file_key": "swfo_profiles#npcs",
        "action": "update",
        "identifier": { "npc_id": "NPC001" },
        "payload": [
          { "op": "replace", "path": "/background_story/summary", "value": "Updated summary for NPC001." }
        ]
      }
    ]
```

9\. Version Log
---------------
_This_ section is for tracking changes to these instructions. For the script's version log, see the comments _within the `json_updater.py` file._
*   Version 6.0 (2025-06-13):
    *   Merged and streamlined content from previous instruction versions into a single, comprehensive document.
    *   Standardized section numbering and titles.
    *   Clarified Identifier Priority lookup logic for SAGA Index files (Section 6).
    *   Ensured all examples are consistent with the path-based update mechanism for "update" actions.
*   (Older version log entries omitted for brevity)

