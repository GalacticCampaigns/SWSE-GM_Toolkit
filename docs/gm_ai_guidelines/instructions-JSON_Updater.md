## Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles

Version 4.2 (2025-05-24)

This document outlines the format for providing JSON-based edits to update structured data files. The json_updater.py script will process these edits.


### I. Overall Structure of the Edit File

The edit file itself must be a JSON array, where each element in the array is an "edit request object."

[

  {"target_file_key":"string","action":"string","is_single_object":false,"identifier":{},"payload":{}},

  {"target_file_key":"string","action":"string","is_single_object":true,"identifier":{"keys_to_delete":["some_key"]},"payload":{}}

]



* is_single_object** (boolean, optional):** Set to true if the target_file_key refers to a JSON file that is a single object at its root (e.g., class_rules.json) where edits apply to top-level keys. If omitted or false, the script assumes the target file contains a list of records or a multi-collection structure (like NPC Profiles).


### II. target_file_key

This string specifies the target data.



* **For SAGA Index files (e.g., armor, feats) or other files containing a list of records:** The target_file_key is the filename without the .json extension (e.g., "armor", "feats"). Do **not** set is_single_object: true for these.
* **For files that are a single JSON object at their root (e.g., **class_rules.json**):** The target_file_key is the filename without the .json extension (e.g., "class_rules"). **Crucially, also include **"is_single_object": true** in the edit request object (see Section I).**
* **For multi-collection files (e.g., an NPC Profile file containing PCs, NPCs, Factions):** Use a composite key: filename_base#collection_name.
    * Example for a file named npc_profiles.json:
        * To edit Player Characters: "target_file_key": "npc_profiles#pcs"
        * To edit Non-Player Characters: "target_file_key": "npc_profiles#npcs"
        * To edit Factions: "target_file_key": "npc_profiles#factions"
        * To edit NPC Stat Blocks: "target_file_key": "npc_profiles#npc_stat_blocks"
    * Do **not** use "is_single_object": true for these multi-collection targets, as the script handles their internal list/map structures via specific configurations.

The json_updater.py script uses target_file_key and the is_single_object flag to locate the correct file and apply edits appropriately.


### III. action

Defines the operation:



* "update": Modifies an existing record or top-level keys in a single-object file. Requires payload. Requires identifier for list/map-based files; identifier is optional for single-object files (payload keys dictate targets).
* "add": Adds a new record to a list, a new key-value pair to an object map, or new top-level keys to a single-object file. Requires payload. For object maps, identifier must specify the new key.
* "delete": Removes an existing record from a list, a key-value pair from an object map, or top-level keys from a single-object file. Requires identifier.


### IV. identifier (for "update" and "delete", and "add" to object maps)

Uniquely locates the record or target keys.



* **For SAGA Index files (list-based):**
    * "name" (string, required)
    * "source_book" (string, recommended)
    * Example: {"name":"Combat Jumpsuit","source_book":"CR"}
* **For NPC Profile collections (list-based or object map):**
    * If targeting ...#pcs: {"pc_id": "PC001"}
    * If targeting ...#npcs: {"npc_id": "NPC001"}
    * If targeting ...#factions (object map): {"faction_id": "FACTION_ID_001"} (also used as the key for "add")
    * If targeting ...#npc_stat_blocks: {"npc_id_ref": "NPC001"}
* **For 'Single Object' files (when **is_single_object: true**):**
    * For action: "update" or action: "add": identifier is not strictly needed by the script for the operation itself (payload keys are targets). Can be {}, or include contextual info like {"file_scope": "class_rules_document"} for logging.
    * For action: "delete": identifier **must** contain {"keys_to_delete": ["key1_to_remove", "key2_to_remove"]}.


### V. payload (for "update" and "add")



* **For list-based files or collections:**
    * "add": payload is the **complete new record object**.
    * "update": payload contains **only fields to change/add**. Do NOT resend the whole record.
* **For object maps (e.g., **...#factions**):**
    * "add": payload is the **complete new value object** for the key specified in identifier.
    * "update": payload contains **only fields to change/add** within the existing object value.
* **For 'Single Object' files (when **is_single_object: true**):**
    * "add" or "update": payload is an object where keys are top-level keys in the target JSON file. Values in the payload will replace or add these top-level keys and their entire content.
        * Example: {"level_dependent_benefits_heroic": { ...new content... }, "new_top_level_rule": "details"}
* **General Rules for **payload**:**
    * Replacing complex fields (objects/arrays like cost or effects): Provide the complete new object/array in the payload for that field.
    * To remove an optional field: Set its value to null in the payload.
    * Field names: snake_case. Data types: Adhere to schemas.


### VI. Examples

**1. Update Armor Cost (SAGA Index file - list-based):**

{"target_file_key":"armor","action":"update","identifier":{"name":"Combat Jumpsuit","source_book":"CR"},"payload":{"cost":{"text_original":"1250 credits","options":[{"type":"fixed_amount","value":1250}],"selection_logic":null},"availability":"Common"}}

**2. Update a Top-Level Section in **class_rules.json** (Single Object file):**

{"target_file_key":"class_rules","action":"update","is_single_object":true,"identifier":{"scope":"class_rules_document"},"payload":{"level_dependent_benefits_heroic":{"description":"Updated description.","new_detail":"Added this."}}}

**3. Add a New PC (NPC Profile file - list-based):**

{"target_file_key":"npc_profiles#pcs","action":"add","payload":{"pc_id":"PC002","name":"Zara Krell","is_active":true,"species":"Zabrak"}}

**4. Delete Top-Level Keys from **class_rules.json** (Single Object file):**

{"target_file_key":"class_rules","action":"delete","is_single_object":true,"identifier":{"keys_to_delete":["old_rule_section", "obsolete_config"]}}


## Version Log



* **Version 4.2 (2025-05-24):**
    * Added optional is_single_object: true flag to the edit request structure (Section I).
    * Updated Section II (target_file_key) to explain how is_single_object interacts with file targeting.
    * Updated Section IV (identifier) with specific instructions for "single object" files, especially for the "delete" action.
    * Updated Section V (payload) with specific instructions for "single object" files for "update" and "add" actions.
    * Added new examples (2 and 4) to illustrate operations on "single object" files.
* **Version 4.1 (2025-05-24):**
    * Added versioning information and this version log to the document.
    * Compacted JSON example in Section I ("Overall Structure of the Edit File") for improved readability based on user feedback.
    * Further clarified instructions in Section V ("payload" for "update" action) to explicitly state that the payload must *only* contain changed or new fields, and *not* entire records if only partial updates are intended. Added a "Common Mistake to Avoid" note.
* **Version 4.0 (Implied - circa 2025-05-24):**
    * Updated Section II (target_file_key) to explain derivation from filenames in any data/ subdirectory (excluding meta_info/) and the use of a composite key like npc_profiles#pcs for multi-collection files.
    * Updated Section IV (identifier) with explicit ID fields (pc_id, npc_id, faction_id, npc_id_ref) for NPC profile collections.
    * Updated Section V (payload) to clarify "add" action for object maps (like factions).