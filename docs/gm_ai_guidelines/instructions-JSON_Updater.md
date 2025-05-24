## Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles
(version 4 - 2025/5/24)

This document outlines the format for providing JSON-based edits to update structured data files. The json_updater.py script will process these edits.


### I. Overall Structure of the Edit File

The edit file itself must be a JSON array, where each element in the array is an "edit request object."

[

  {"target_file_key":"string","action":"string","identifier":{},"payload":{}},

  {"target_file_key":"string","action":"string","identifier":{},"payload":{}}

]


### II. target_file_key

This string specifies which main data category (and thus which JSON file) the edit applies to. **The **target_file_key** should be the name of the JSON file (without the **.json** extension) located in any subdirectory under the main **data/** directory of the GitHub repository (e.g., **data/character_elements/**, **data/index_elements/**, **data/new_category/**, etc.), excluding the **data/meta_info/** directory.**

**How to determine the **target_file_key**:**



1. Identify the target JSON data file within the repository structure (e.g., SagaIndex/data/character_elements/species.json or SagaIndex/data/index_elements/armor.json).
2. The target_file_key is the filename without the .json extension.

**Examples:**



* If editing SagaIndex/data/character_elements/species.json, the target_file_key is "species".
* If editing SagaIndex/data/index_elements/armor.json, the target_file_key is "armor".
* If editing SagaIndex/data/vehicles/airspeeders.json (a hypothetical new file), the target_file_key would be "airspeeders".

The json_updater.py script uses this key to:



1. Construct the full path to the target JSON file by scanning subdirectories under data/.
2. Determine the name of the list within that JSON file that holds the records (e.g., for a target_file_key of "armor", the script expects a list named armor_list inside a top-level object like armor_data). This mapping is derived by convention ({key}_list, {key}_data) with specific exceptions handled in the script (like for equipment_general).

**Ensure the **target_file_key** you provide corresponds to an actual JSON file that the **json_updater.py** script can discover and for which it can determine the internal structure based on its naming conventions.** The script dynamically builds its internal configuration (TARGET_FILES_CONFIG) at runtime.


### III. action

Defines the operation:



* "update": Modifies an existing record. Requires identifier and payload. Use this to change existing fields or add new fields to a record.
* "add": Adds a new, entirely separate record. Requires payload.
    * For lists (most collections): The identifier is ignored; uniqueness is checked based on the record's inherent ID fields (e.g., name & source_book, or pc_id/npc_id).
    * For object maps (like factions): The identifier **must** contain the key for the new entry (e.g., {"faction_id": "NEW_FACTION_ID"}).
* "delete": Removes an existing record. Requires identifier.


### IV. identifier (for "update" and "delete", and "add" to object maps)

Uniquely locates the record.



* **For SAGA Index files (e.g., **target_file_key: "armor"**):**
    * "name" (string, required): Primary name.
    * "source_book" (string, recommended): Source book abbreviation.
    * Example: {"name":"Combat Jumpsuit","source_book":"CR"}
* **For NPC Profile collections (e.g., **target_file_key: "npc_profiles#pcs"**):**
    * If targeting ...#pcs: {"pc_id": "PC001"}
    * If targeting ...#npcs: {"npc_id": "NPC001"}
    * If targeting ...#factions: {"faction_id": "FACTION_ID_001"} (also used as the key for "add")
    * If targeting ...#npc_stat_blocks: {"npc_id_ref": "NPC001"}


### V. payload (for "update" and "add")



* **For **"add"** action:**
    * The payload is a **complete JSON object** for the new record, conforming to the target's schema.
    * For lists, ensure inherent ID fields (e.g., name & source_book for items; pc_id/npc_id for characters) are in the payload.
    * Attempting to "add" a record that effectively duplicates an existing one (based on its identifying fields) will be skipped by the updater script.
* **For **"update"** action:**
    * Use this action to modify an existing identified record. The payload **must only contain the specific fields you intend to change or add** to the existing record, along with their new values. **Do NOT include fields from the original record if their values are not changing.**
    * **This includes:**
        * **Modifying the value of an existing field:** Provide the field name and its new value (e.g., {"availability": "Rare"}).
        * **Adding a completely new field and its value to an existing record:** Provide the new field name and its value (e.g., {"designer_note": "Limited edition"}). The script will add this field to the identified record. If the field already exists, its value will be updated.
        * **Replacing the entire content of an existing complex field** (like an object or an array, e.g., cost, special_qualities, structured_effects): Provide the field name and its *complete new object or array* in the payload. The existing object/array for that field will be entirely replaced by what's in the payload. *Partial updates of nested structures (e.g., changing only one element in an array or one sub-key in an object without resending the whole array/object) are not supported by this mechanism; you must provide the full new state for the entire complex field if any part of it needs to change.*
    * **To remove an optional field** from a record (e.g., special_note on a feat that was previously filled): Include that field in the payload with its value set to null.
    * **Common Mistake to Avoid:** Do not use the "update" action to resend the entire existing record with just a few changes. Only send the specific fields that are being added or whose values are changing. If the AI sends the entire record as the payload, it will simply overwrite all fields in the target record with all fields from the payload. This is inefficient and can lead to errors if the AI's copy of the record is not perfectly synchronized with the latest version in the JSON file (potentially reverting other recent changes). The script is designed to merge in *only* the fields provided in the payload for an update.

**Field Naming and Data Types:**



* All field names in payload must use snake_case.
* Data types for all fields must strictly adhere to the JSON schemas established for the respective target_file_key. Refer to the files in the schemas/ directory.


### VI. Examples

**1. Update an Armor's Cost and Availability (SAGA Index file):**

{"target_file_key":"armor","action":"update","identifier":{"name":"Combat Jumpsuit","source_book":"CR"},"payload":{"cost":{"text_original":"1250 credits","options":[{"type":"fixed_amount","value":1250}],"selection_logic":null},"availability":"Common"}}

**2. Add New Field (**designer_note**) and Update **page** on an Existing Feat:**

{"target_file_key":"feats","action":"update","identifier":{"name":"Point-Blank Shot","source_book":"CR"},"payload":{"designer_note":"Essential for ranged combatants.","page":86}}

**3. Add an Entirely New Feat:**

{"target_file_key":"feats","action":"add","payload":{"name":"Advanced Targeting Array","type":["General","Starship"],"prerequisites_text":"Int 13, Point-Blank Shot","prerequisites_structured":[{"type":"ability_score","ability":"Intelligence","value":13,"text_description":"Int 13"},{"type":"feat_or_ability","name":"Point-Blank Shot","text_description":"Point-Blank Shot"}],"benefit_summary":"Reduce cover bonus of target by 1 step.","effects":[{"type":"narrative_only","summary":"When making a ranged attack with a starship weapon, you can reduce the target's cover bonus to its Reflex Defense by one step (from cover to improved cover, or from improved cover to no cover bonus from that source)."}],"bonus_feat_for_classes":[],"source_book":"SoG","page":25,"special_note":null}}

**4. Add a New Faction (NPC Profile file - object map):**

{"target_file_key":"npc_profiles#factions","action":"add","identifier":{"faction_id":"CRIMSON_DAWN_REMNANT"},"payload":{"faction_id":"CRIMSON_DAWN_REMNANT","faction_name":"Crimson Dawn Remnant Cell","faction_type":"Criminal Syndicate","allegiance_primary":"Self-interest (Crimson Dawn Ideals)","description":"A small, secretive cell of Crimson Dawn loyalists operating in the Outer Rim.","quick_status_summary_for_gm":{"current_primary_goal_active":"Acquire lost Sith artifact.","overall_disposition_towards_pcs_or_player_faction":"Neutral, wary.","immediate_concerns_threats":["Imperial patrols","Rival gangs"]},"npc_members":[],"pc_members":[],"goals_objectives":[{"goal_description":"Re-establish contact with other cells.","status":"Active","priority":"High"}],"creation_timestamp":"2025-05-24T12:00:00Z","last_modified_timestamp":"2025-05-24T12:00:00Z","information_log":[]}}

**5. Delete a SAGA Index Feat:**

{"target_file_key":"feats","action":"delete","identifier":{"name":"Obsolete Feat","source_book":"OLD"}}



