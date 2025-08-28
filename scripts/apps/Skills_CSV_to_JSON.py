import json
import csv
import io
import re
import os

# --- 1. CONFIGURATION: SET CSV DATA SOURCE ---
# Using the paths you provided for your local setup
LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'

SKILL_DEFINITIONS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Skills.csv')
SKILL_USES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Skill uses 1.8.csv') # File 1
SKILL_ACTIONS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Use.csv')      # File 3
OUTPUT_JSON_FILE_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\skills.json')


# --- Placeholder for pasting CSV data directly (alternative) ---
"""
SKILL_DEFINITIONS_CSV_PATH = None
SKILL_USES_CSV_PATH = None
SKILL_ACTIONS_CSV_PATH = None

SKILL_DEFINITIONS_CSV_STRING_DATA = \"""PASTE Character-Skills.csv CONTENT HERE\"""
SKILL_USES_CSV_STRING_DATA = \"""PASTE Character-Skill uses 1.8.csv CONTENT HERE\"""
SKILL_ACTIONS_CSV_STRING_DATA = \"""PASTE Character-Use.csv CONTENT HERE\"""
"""

# --- 2. HELPER FUNCTIONS ---

def mtr_explanations(text):
    if not text: return ""
    description = text
    clarification_text = "(must take re-roll)"
    description = description.replace(", mtr", f" {clarification_text}")
    description = description.replace(" mtr", f" {clarification_text}")
    target_phrase_lower = "you must accept the result of the reroll"
    if target_phrase_lower in description.lower() and clarification_text not in description:
        description += f" {clarification_text}"
    while f" {clarification_text} {clarification_text}" in description:
        description = description.replace(f" {clarification_text} {clarification_text}", f" {clarification_text}")
    while f"{clarification_text}{clarification_text}" in description:
        description = description.replace(f"{clarification_text}{clarification_text}", clarification_text)
    description = re.sub(r'\s+\(\s*must take re-roll\s*\)', r' (must take re-roll)', description)
    description = description.replace(f". {clarification_text}", f" {clarification_text}.")
    description = description.strip()
    if description.endswith(clarification_text) and text.strip().endswith('.') and not description.endswith('.'):
        description += '.'
    return description

def normalize_use_name(name):
    """Normalizes a skill use/action name for matching purposes."""
    return name.lower().strip()

# --- 3. MAIN SCRIPT LOGIC ---

def generate_skills_json():
    skills_data = {} # Using a dict for skills, keyed by skill name for easy access

    # --- Step 1: Load Base Skill Definitions (from Character-Skills.csv) ---
    source_type_def = "None"
    try:
        content_def = None
        if SKILL_DEFINITIONS_CSV_PATH and 'YOUR_PATH' not in SKILL_DEFINITIONS_CSV_PATH:
            with open(SKILL_DEFINITIONS_CSV_PATH, mode='r', encoding='utf-8-sig') as file:
                content_def = file.read()
            source_type_def = f"File: {SKILL_DEFINITIONS_CSV_PATH}"
        elif 'SKILL_DEFINITIONS_CSV_STRING_DATA' in globals() and \
              isinstance(SKILL_DEFINITIONS_CSV_STRING_DATA, str) and \
              SKILL_DEFINITIONS_CSV_STRING_DATA.strip().count('\n') > 0:
            content_def = SKILL_DEFINITIONS_CSV_STRING_DATA
            source_type_def = "String Data (Skill Definitions)"
        
        if content_def:
            reader_def = csv.DictReader(io.StringIO(content_def))
            for row in reader_def:
                skill_name = row.get('SKILLS', '').strip()
                if not skill_name: continue
                
                class_skills = []
                for class_col in ['Jedi', 'Noble', 'Scoundrel', 'Scout', 'Soldier']: # Corrected Scoundrel key
                    if row.get(class_col, '').strip().lower() == 'x':
                        class_skills.append(class_col)
                # Corrected key for "  Scoundrel" if it has leading spaces from CSV header
                if row.get('  Scoundrel', '').strip().lower() == 'x' and "Scoundrel" not in class_skills :
                    class_skills.append("Scoundrel")


                skills_data[skill_name] = {
                    "name": skill_name,
                    "key_ability": row.get('Ability', '').strip(),
                    "armor_check_penalty_applies_generally": row.get('Armor check penalty?', '').strip().upper() == 'Y',
                    "source_book": row.get('BOOK', '').strip(),
                    "page": row.get('PAGE', '').strip(),
                    "class_skill_for": sorted(list(set(class_skills))), # Ensure uniqueness and sort
                    "common_uses": {} # Temp dict for uses, keyed by normalized use_name
                }
            print(f"Successfully loaded base skill definitions from {source_type_def}.")
        else:
            print("Warning: No Skill Definitions CSV data source configured.")
            return None

    except FileNotFoundError: print(f"Error: Skill Definitions CSV not found at '{SKILL_DEFINITIONS_CSV_PATH}'.")
    except Exception as e: print(f"Error reading Skill Definitions CSV: {e}")


    # --- Step 2: Populate Initial Uses (from Character-Skill uses 1.8.csv) ---
    source_type_uses = "None"
    try:
        content_uses = None
        if SKILL_USES_CSV_PATH and 'YOUR_PATH' not in SKILL_USES_CSV_PATH:
            with open(SKILL_USES_CSV_PATH, mode='r', encoding='utf-8-sig') as file:
                content_uses = file.read()
            source_type_uses = f"File: {SKILL_USES_CSV_PATH}"
        elif 'SKILL_USES_CSV_STRING_DATA' in globals() and \
              isinstance(SKILL_USES_CSV_STRING_DATA, str) and \
              SKILL_USES_CSV_STRING_DATA.strip().count('\n') > 0:
            content_uses = SKILL_USES_CSV_STRING_DATA
            source_type_uses = "String Data (Skill Uses)"

        if content_uses:
            reader_uses = csv.DictReader(io.StringIO(content_uses))
            for row in reader_uses:
                skill_name = row.get('Skill', '').strip()
                use_name = row.get('Use', '').strip()
                if not skill_name or not use_name: continue

                if skill_name in skills_data:
                    normalized_use = normalize_use_name(use_name)
                    skills_data[skill_name]["common_uses"][normalized_use] = {
                        "use_name": use_name,
                        "source_book_for_use": skills_data[skill_name]["source_book"], # Default to skill's book
                        "page_for_use": skills_data[skill_name]["page"],       # Default to skill's page
                        "related_ability_for_use": row.get('Ability', skills_data[skill_name]["key_ability"]).strip(),
                        "trained_only": row.get('Trained', '').strip().upper() == 'Y',
                        "armor_check_penalty_for_this_use": row.get('AP', '').strip().upper() == 'YES',
                        "dc_details": row.get('DC', '').strip(),
                        "notes": mtr_explanations(row.get('Notes', '').strip()),
                        "requirements": None, # To be filled by SKILL_ACTIONS_CSV
                        "take_10_20_allowed": row.get('Take 10/20', '').strip(),
                        "retry_info": mtr_explanations(row.get('Retry', '').strip()),
                        "time_to_perform": row.get('Time', '').strip()
                    }
                else:
                    print(f"Warning: Skill '{skill_name}' found in Skill Uses CSV but not in Skill Definitions. Skipping use '{use_name}'.")
            print(f"Successfully processed initial skill uses from {source_type_uses}.")
        else:
            print("Warning: No Skill Uses (Character-Skill uses 1.8.csv) data source configured.")
            
    except FileNotFoundError: print(f"Error: Skill Uses CSV (Character-Skill uses 1.8.csv) not found at '{SKILL_USES_CSV_PATH}'.")
    except Exception as e: print(f"Error reading Skill Uses CSV (Character-Skill uses 1.8.csv): {e}")


    # --- Step 3: Enrich/Add Uses (from Character-Use.csv) ---
    source_type_actions = "None"
    try:
        content_actions = None
        if SKILL_ACTIONS_CSV_PATH and 'YOUR_PATH' not in SKILL_ACTIONS_CSV_PATH:
            with open(SKILL_ACTIONS_CSV_PATH, mode='r', encoding='utf-8-sig') as file:
                content_actions = file.read()
            source_type_actions = f"File: {SKILL_ACTIONS_CSV_PATH}"
        elif 'SKILL_ACTIONS_CSV_STRING_DATA' in globals() and \
              isinstance(SKILL_ACTIONS_CSV_STRING_DATA, str) and \
              SKILL_ACTIONS_CSV_STRING_DATA.strip().count('\n') > 0:
            content_actions = SKILL_ACTIONS_CSV_STRING_DATA
            source_type_actions = "String Data (Skill Actions/Use)"

        if content_actions:
            reader_actions = csv.DictReader(io.StringIO(content_actions))
            for row in reader_actions:
                skill_name = row.get('SKILL', '').strip()
                action_name = row.get('ACTION', '').strip()
                if not skill_name or not action_name: continue

                if skill_name in skills_data:
                    normalized_action = normalize_use_name(action_name)
                    
                    # Check if this use already exists from the previous CSV
                    if normalized_action in skills_data[skill_name]["common_uses"]:
                        # Enrich existing use
                        use_obj = skills_data[skill_name]["common_uses"][normalized_action]
                        use_obj["requirements"] = mtr_explanations(row.get('REQUIREMENTS', '').strip()) or use_obj.get("requirements")
                        use_obj["trained_only"] = row.get('Trained Only?', '').strip().lower() == 'x' or use_obj.get("trained_only", False)
                        if row.get('BOOK', '').strip(): # Update source if provided for this specific use
                            use_obj["source_book_for_use"] = row.get('BOOK', '').strip()
                        if row.get('PAGE', '').strip():
                            use_obj["page_for_use"] = row.get('PAGE', '').strip()
                    else:
                        # Add as a new use, might be less detailed if not in skill_uses.csv
                        skills_data[skill_name]["common_uses"][normalized_action] = {
                            "use_name": action_name,
                            "source_book_for_use": row.get('BOOK', skills_data[skill_name]["source_book"]).strip(),
                            "page_for_use": row.get('PAGE', skills_data[skill_name]["page"]).strip(),
                            "related_ability_for_use": skills_data[skill_name]["key_ability"], # Default to skill's key ability
                            "trained_only": row.get('Trained Only?', '').strip().lower() == 'x',
                            "armor_check_penalty_for_this_use": None, # Not in this CSV
                            "dc_details": None, # Not in this CSV
                            "notes": None, # Not in this CSV
                            "requirements": mtr_explanations(row.get('REQUIREMENTS', '').strip()),
                            "take_10_20_allowed": None, # Not in this CSV
                            "retry_info": None, # Not in this CSV
                            "time_to_perform": None # Not in this CSV
                        }
                else:
                    print(f"Warning: Skill '{skill_name}' found in Skill Actions CSV but not in Skill Definitions. Skipping action '{action_name}'.")
            print(f"Successfully processed and merged skill actions from {source_type_actions}.")
        else:
            print("Warning: No Skill Actions (Character-Use.csv) data source configured.")

    except FileNotFoundError: print(f"Error: Skill Actions CSV (Character-Use.csv) not found at '{SKILL_ACTIONS_CSV_PATH}'.")
    except Exception as e: print(f"Error reading Skill Actions CSV (Character-Use.csv): {e}")


    # --- Convert common_uses dict to list and finalize skill list ---
    final_skill_list = []
    for skill_name, skill_obj in skills_data.items():
        # Convert dict of uses to a list and sort by use_name
        skill_obj["common_uses"] = sorted(list(skill_obj["common_uses"].values()), key=lambda x: x["use_name"])
        final_skill_list.append(skill_obj)
    
    # Sort the final list of skills by skill name
    final_skill_list = sorted(final_skill_list, key=lambda x: x["name"])


    # --- Construct Final JSON ---
    output_data = {
        "skills_data": {
            "description": "Comprehensive list of skills in Star Wars SAGA Edition, their general properties, and detailed common uses with associated mechanics.",
            "skill_list": final_skill_list
        }
    }

    # --- Output JSON to file ---
    try:
        output_dir = os.path.dirname(OUTPUT_JSON_FILE_PATH)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        with open(OUTPUT_JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nSuccessfully generated Skills JSON output to: {OUTPUT_JSON_FILE_PATH}")

    except Exception as e:
        print(f"Error writing Skills JSON to file: {e}")


if __name__ == '__main__':
    print("Starting SAGA Skills JSON generation...")
    generate_skills_json()
    print("Script finished.")
