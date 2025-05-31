import json
import csv
import io
import re
import os

# --- 1. CONFIGURATION ---
LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'

# Input CSV Paths
SPECIES_MAIN_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Species.csv')
SPECIES_TRAITS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Traits.csv')
SKILLS_DEF_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Skills.csv')
SKILL_USES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Skill uses 1.8.csv')
SKILL_ACTIONS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Use.csv')
FEATS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Feats.csv')
TALENTS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Talents.csv')
TECHNIQUES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Techniques.csv')
SECRETS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Secrets.csv')
REGIMENS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Regimens.csv')
STARSHIP_MANEUVERS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Starship Maneuvers.csv')
FORCE_POWERS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-ForcePowers.csv')
PRESTIGE_CLASSES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Prestige.csv')
DROID_CHASSIS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Droids.csv') # New Droid CSV Path

# Output JSON Paths
SPECIES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\species.json')
SKILLS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\skills.json')
FEATS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\feats.json')
TALENTS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\talents.json')
TECHNIQUES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\force_techniques.json')
SECRETS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\force_secrets.json')
REGIMENS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\training_regimens.json')
STARSHIP_MANEUVERS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\starship_maneuvers.json') # Note: Path suggests index_elements
FORCE_POWERS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\force_powers.json')
PRESTIGE_CLASSES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\prestige_classes.json')
DROID_CHASSIS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\droid_chassis.json') # New Droid JSON Path


# --- SCRIPT EXECUTION CONFIGURATION ---
PROCESS_CONFIG = {
    "species": False, 
    "skills": False,
    "feats": False,
    "talents": False,
    "techniques": False,
    "secrets": False,
    "regimens": False,
    "starship_maneuvers": False,
    "force_powers": False,
    "prestige_classes": False,
    "droids": True,  # Added new entry for droids, set to True for processing
}

# --- Placeholder for pasting CSV data directly (alternative to file paths) ---
"""
FEATS_CSV_PATH = None 
# ... etc. for other paths

FEATS_CSV_STRING_DATA = \"""PASTE FEATS CSV HERE\"""
# ... etc. for other string data
"""

# --- 2. HELPER FUNCTIONS (GENERAL) ---

def clean_value(value): # CORRECTED
    if isinstance(value, str):
        value = re.sub(r"\[source:\s*\d+\]", "", value) 
        temp_value = value.strip()
        # Iteratively remove surrounding quotes
        while len(temp_value) >= 2 and \
              ((temp_value.startswith('"') and temp_value.endswith('"')) or \
               (temp_value.startswith("'") and temp_value.endswith("'"))):
            temp_value = temp_value[1:-1].strip()
        return temp_value
    return value

def mtr_explanations(text):
    if not text: return ""
    description = text; clarification_text = "(must take re-roll)"
    description = description.replace(", mtr", f" {clarification_text}").replace(" mtr", f" {clarification_text}")
    target_phrase_lower = "you must accept the result of the reroll"
    if target_phrase_lower in description.lower() and clarification_text not in description: description += f" {clarification_text}"
    while f" {clarification_text} {clarification_text}" in description: description = description.replace(f" {clarification_text} {clarification_text}", f" {clarification_text}")
    while f"{clarification_text}{clarification_text}" in description: description = description.replace(f"{clarification_text}{clarification_text}", clarification_text)
    description = re.sub(r'\s+\(\s*must take re-roll\s*\)', r' (must take re-roll)', description)
    description = description.replace(f". {clarification_text}", f" {clarification_text}.")
    description = description.strip()
    if description.endswith(clarification_text) and text.strip().endswith('.') and not description.endswith('.'): description += '.'
    return description

def get_prerequisite_text_from_row_dict(row_dict, column_options):
    for col_name in column_options:
        text = row_dict.get(col_name, '').strip()
        if text and text.lower() != 'none':
            return text
    return "None"

def get_prerequisite_text_from_row_list(row_list, indices_map, column_options):
    prereq_texts = []
    for key_name in column_options:
        idx = indices_map.get(key_name, -1)
        if 0 <= idx < len(row_list):
            text = clean_value(row_list[idx])
            if text and text.lower() != 'none':
                prereq_texts.append(text)
    return ", ".join(prereq_texts) if prereq_texts else "None"


def parse_prerequisites_from_text(text):
    if not text or text.strip().lower() == 'none': return []
    prereqs = []; normalized_text = re.sub(r'\s*;\s*|\s+and\s+', ', ', text, flags=re.IGNORECASE)
    parts = [p.strip() for p in normalized_text.split(',') if p.strip()]
    for part in parts:
        obj = {"text_description": part}
        ability_match = re.search(r"(Str|Dex|Con|Int|Wis|Cha|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*(\d+)", part, re.IGNORECASE)
        if ability_match:
            ability_map_short = {"str": "Strength", "dex": "Dexterity", "con": "Constitution", "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}
            ability_short = ability_match.group(1).lower()
            obj.update({"type": "ability_score", "ability": ability_map_short.get(ability_short, ability_match.group(1).capitalize()), "value": int(ability_match.group(2))}); prereqs.append(obj); continue
        bab_match = re.search(r"(?:BAB|Base attack bonus)\s*\+\s*(\d+)", part, re.IGNORECASE)
        if bab_match: obj.update({"type": "base_attack_bonus", "value": int(bab_match.group(1))}); prereqs.append(obj); continue
        trained_skill_match = re.search(r"Trained in ([\w\s\(\)]+)", part, re.IGNORECASE)
        if trained_skill_match: obj.update({"type": "skill_trained", "skill_name": trained_skill_match.group(1).strip()}); prereqs.append(obj); continue
        skill_rank_match = re.search(r"([\w\s\(\)]+?)\s*(\d+)\s*ranks?", part, re.IGNORECASE)
        if skill_rank_match: obj.update({"type": "skill_rank", "skill_name": skill_rank_match.group(1).strip(), "ranks": int(skill_rank_match.group(2))}); prereqs.append(obj); continue
        talent_prereq_match = re.search(r"([\w\s\'\’]+)\s*\(([\w\s]+)-([\w\s]+)\)", part)
        if talent_prereq_match:
            obj.update({"type": "talent_prerequisite", "talent_name": talent_prereq_match.group(1).strip(), "required_class": talent_prereq_match.group(2).strip(), "required_talent_tree": talent_prereq_match.group(3).strip()}); prereqs.append(obj); continue
        class_level_match = re.search(r"(\w+)\s*(?:level)?\s*(\d+)(?:st|nd|rd|th)?", part, re.IGNORECASE)
        if class_level_match:
            known_classes = ["jedi", "noble", "scoundrel", "scout", "soldier"]; class_name_match_lower = class_level_match.group(1).lower()
            is_known_class = class_name_match_lower in known_classes or any(known_class in class_name_match_lower for known_class in known_classes)
            if is_known_class: obj.update({"type": "class_level", "class_name": class_level_match.group(1).capitalize(), "level": int(class_level_match.group(2))}); prereqs.append(obj); continue
        char_level_match = re.search(r"(?:Character level|Level)\s*(\d+)(?:st|nd|rd|th)?", part, re.IGNORECASE)
        if char_level_match:
            is_class_level_already_found = any(p['text_description'] == part and p['type'] == 'class_level' for p in prereqs)
            if not is_class_level_already_found: obj.update({"type": "character_level", "level": int(char_level_match.group(1))}); prereqs.append(obj); continue
        not_feat_match = re.search(r"not possess(?:ed of)? the ([\w\s]+) feat", part, re.IGNORECASE)
        if not_feat_match: obj.update({"type": "restriction_feat", "name": not_feat_match.group(1).strip(), "restriction": "cannot_have"}); prereqs.append(obj); continue
        if not talent_prereq_match:
            if "feat" in part.lower() or \
               any(k.lower() in part.lower() for k in ["Focus", "Proficiency", "Mastery", "Attack", "Shot", "Strike", "Defense", "Talent", "Power", "Secret", "Technique", "Combat", "Vehicular", "Dodge", "Maneuver"]) or \
               (part.count(' ') < 5 and sum(1 for c in part if c.isupper()) > 0 and not re.match(r"^\d+", part) and "rank" not in part.lower() and "level" not in part.lower()):
                feat_name_candidate = re.sub(r'\bfeat\b', '', part, flags=re.IGNORECASE).strip()
                feat_name_candidate = re.sub(r'\s*\([\w\s\-]+\)$', '', feat_name_candidate).strip()
                if feat_name_candidate: obj.update({"type": "feat_or_ability", "name": feat_name_candidate}); prereqs.append(obj); continue
        obj["type"] = "other"; prereqs.append(obj)
    return prereqs

def parse_effects_from_text(description, context_skill=None, is_recursive_call=False):
    effects = []
    if not description: return [{"type": "narrative_only", "summary": "No description provided."}]
    if not is_recursive_call:
        dc_tier_pattern = re.compile(r"DC\s*(\d+)\s*:\s*([\s\S]+?)(?=(?:\n\s*DC\s*\d+\s*:)|\Z)", re.IGNORECASE | re.MULTILINE)
        dc_matches = list(dc_tier_pattern.finditer(description))
        if len(dc_matches) >= 1:
            tiers = []
            for match in dc_matches:
                dc_value = int(match.group(1)); tier_description_full = match.group(2).strip()
                tier_description_cleaned = mtr_explanations(tier_description_full)
                tier_structured_effects = parse_effects_from_text(tier_description_cleaned, context_skill=None, is_recursive_call=True)
                if len(tier_structured_effects) > 1 and tier_structured_effects[0].get("type") == "narrative_only": tier_structured_effects.pop(0)
                elif not tier_structured_effects and tier_description_cleaned: tier_structured_effects = [{"type": "narrative_only", "summary": tier_description_cleaned}]
                tiers.append({"dc": dc_value, "description": tier_description_cleaned, "structured_effects": tier_structured_effects})
            if tiers:
                progression_rule = "cumulative_up_to_achieved_dc"
                if "only the highest" in description.lower() or "instead of the normal effect" in description.lower(): progression_rule = "highest_achieved_only"
                effects.append({"type": "dc_progression", "check_skill_or_ability": context_skill or "Contextual Skill/Ability Check", "progression_rule": progression_rule, "tiers": sorted(tiers, key=lambda x: x['dc']), "full_progression_text": mtr_explanations(description)})
                return effects
    desc_lower = description.lower()
    bonus_penalty_regex = r"(gain(?:s)?|grants?|adds?|provides?|receives?|suffer(?:s)?|takes?|imposes?|reduces?|increases?)" \
                          r"\s*(?:a|an)?\s*" \
                          r"([+-]?\d+|one|two|three|four|five|half your level|character level|level|STR modifier|DEX modifier|CON modifier|INT modifier|WIS modifier|CHA modifier|Strength modifier|Dexterity modifier|Constitution modifier|Intelligence modifier|Wisdom modifier|Charisma modifier)" \
                          r"\s*" \
                          r"((?:point|step|die|persistent step|natural armor|species|armor|shield|equipment|circumstance|feat|inherent|insight|morale|size|dodge|racial|untyped))?" \
                          r"\s*" \
                          r"((?:bonus|penalty|points of damage|persistent step))?" \
                          r"\s*(?:on|to|against|from|of|in|with|for|by)\s*" \
                          r"([\w\s\(\)\-\,\/\%]+?)" \
                          r"(?:\s*(?:checks|defense|attacks|damage|rolls|speed|track|DC|modifier|penalty|threshold|damage threshold|duration)|$)"
    for match in re.finditer(bonus_penalty_regex, desc_lower):
        action = match.group(1).strip(); value_str = match.group(2).strip()
        specific_type_keywords = match.group(3).strip() if match.group(3) else ""
        general_indicator = match.group(4).strip() if match.group(4) else ""
        target_str = match.group(5).strip(); effect_type = "generic_modifier"; numeric_value = None
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        if value_str.isdigit() or (value_str.startswith(('+','-')) and value_str[1:].isdigit()): numeric_value = int(value_str)
        elif value_str in word_to_num: numeric_value = word_to_num[value_str]
        if "penalty" in general_indicator or (numeric_value is not None and numeric_value < 0) or value_str.startswith('-'): effect_type = "penalty"
        elif "bonus" in general_indicator or (numeric_value is not None and numeric_value > 0) or value_str.startswith('+'): effect_type = "bonus"
        elif "damage" in general_indicator or "damage" in target_str: effect_type = "damage_modifier"
        elif "speed" in target_str: effect_type = "speed_modifier"
        elif "condition track" in target_str or "persistent step" in general_indicator: effect_type = "condition_track_change"
        bonus_or_penalty_category = specific_type_keywords if specific_type_keywords else "untyped"
        if bonus_or_penalty_category == "untyped" and general_indicator and general_indicator not in ["bonus", "penalty"]: bonus_or_penalty_category = general_indicator
        effects.append({"type": effect_type, "action_verb": action, "value_description": value_str, "numeric_value_approx": numeric_value, "bonus_or_penalty_type": bonus_or_penalty_category, "target_description": target_str})
    feat_grant_match = re.search(r"gain(?:s)? ([\w\s\(\)]+?) as a bonus feat", desc_lower)
    if feat_grant_match:
        feat_name = feat_grant_match.group(1).strip()
        if "skill focus" in feat_name and "(" in feat_name and ")" in feat_name:
             actual_feat = feat_name[feat_name.find("(")+1:feat_name.find(")")]; effects.append({"type": "feat_grant", "feat_name": f"Skill Focus ({actual_feat.title()})"})
        else: effects.append({"type": "feat_grant", "feat_name": feat_name.title()})
    dr_match = re.search(r"(?:DR|damage reduction)\s*(\d+)", description, re.IGNORECASE);
    if dr_match: effects.append({"type": "damage_reduction", "value": int(dr_match.group(1))})
    natural_weapon_match = re.search(r"(claws?|teeth|bite|horns?|tail|tentacles?)(?:.*?dealing)?\s*(\d+d\d+)\s*(\w+)?\s*(?:damage)?", desc_lower)
    if natural_weapon_match: effects.append({"type": "natural_weapon", "weapon_name": natural_weapon_match.group(1).strip(), "damage_dice": natural_weapon_match.group(2).strip(), "damage_type": natural_weapon_match.group(3).strip() if natural_weapon_match.group(3) else "unspecified"})
    reroll_match = re.search(r"reroll (?:any |one |a )?([\w\s]+?)(?: check)?(?:, (keeping|but must accept|but must take|and take the better result|keeping the better result))?", desc_lower)
    if reroll_match:
        check_type = reroll_match.group(1).strip(); condition = reroll_match.group(2).strip() if reroll_match.group(2) else "unspecified"
        if "must accept" in condition or "must take" in condition: condition = "must take result"
        elif "keeping" in condition or "better result" in condition : condition = "keep better/specified result"
        effects.append({"type": "reroll", "check_type": check_type, "condition": condition})
    class_skill_match = re.findall(r"([\w\s\(\),]+?)\s*(?:is|are)\s*(?:always considered a |a )?class skill", desc_lower)
    for skill_match_group in class_skill_match:
        skills_text = skill_match_group.replace("and", ",").strip()
        skills = [s.strip() for s in skills_text.split(',') if s.strip() and len(s.strip()) > 2]
        for skill in skills: effects.append({"type": "class_skill", "skill": skill.title()})
    action_match = re.search(r"(once per encounter|once per day|at will)?\s*(?:as a|as an)?\s*(swift|standard|full-round|move|free|reaction)\s*(?:action)?", desc_lower)
    if action_match: effects.append({"type": "special_action", "frequency": action_match.group(1).strip() if action_match.group(1) else "at will (unless specified otherwise)", "action_cost": action_match.group(2).strip()})
    immunity_match = re.findall(r"immune to ([\w\s]+?)(?: effects)?(?:and|or|,|\.|$)", desc_lower)
    for immune_item in immunity_match: effects.append({"type": "immunity", "immune_to": immune_item.strip()})
    if not effects and description: effects.append({"type": "narrative_only", "summary": "Mechanics are described textually in the description."})
    elif not effects and not description: effects.append({"type": "narrative_only", "summary": "No description provided."})
    return effects

def parse_action_type(action_text):
    if not action_text: return None
    text_lower = action_text.lower().strip()
    action_map = {"stan": "Standard Action", "standard": "Standard Action", "move": "Move Action", "swif": "Swift Action", "swift": "Swift Action", "full": "Full-Round Action", "full-round": "Full-Round Action", "full round": "Full-Round Action", "reac": "Reaction", "reaction": "Reaction", "free": "Free Action"}
    for key, value in action_map.items():
        if key == text_lower: return value
    return action_text.title() if len(action_text) > 3 else action_text

def parse_special_rules_from_description(description_text):
    notes = [];
    if not description_text: return notes
    lsf_pattern = re.compile(r"Lightsaber Form\s*\(([\w\s-]+)\):\s*([\s\S]+?)(?=\n\s*(?:Special:|Lightsaber Form \(|\Z))", re.IGNORECASE | re.MULTILINE)
    for match in lsf_pattern.finditer(description_text):
        notes.append({"note_type": "lightsaber_form_interaction", "form_name": match.group(1).strip(), "text": mtr_explanations(match.group(2).strip())})
    special_pattern = re.compile(r"Special:\s*([\s\S]+?)(?=\n\s*(?:Lightsaber Form \(|Special:|\Z))", re.IGNORECASE | re.MULTILINE)
    for match in special_pattern.finditer(description_text):
        text = mtr_explanations(match.group(1).strip())
        note_type = "general_special_rule";
        if "force point" in text.lower(): note_type = "force_point_option"
        notes.append({"note_type": note_type, "text": text})
    return notes

def attempt_numeric_conversion(value_str, item_name_for_warning="Unknown Item", field_name_for_warning="Unknown Field", data_type_for_warning="Data"): # Added default parameters
    original_value_for_warning = value_str
    if value_str is None or value_str == '': return None
    if isinstance(value_str, (int, float)): return value_str
    
    # Explicitly handle cases that should not be converted to numbers but are valid text
    known_non_numeric_values = ['varies', 'none', 's', '∞', '?', '-', 'see text', 'see description', 'n/a', 'various']
    # Ensure clean_value is applied for the check, as the input string might have quotes or source tags.
    # Convert to string first in case it's already a number (though the first check handles int/float).
    cleaned_check_str = clean_value(str(value_str)).lower()

    if cleaned_check_str in known_non_numeric_values:
        # Return the original string if it's a recognized non-numeric textual value,
        # so it can be stored as is (e.g., "Varies", "None").
        # Or return None if the schema expects null for these. For now, let's assume original text is better if it's a recognized word.
        # Based on schema for droids cost (allows null), returning None for these seems appropriate if they mean "not a number".
        # However, if the schema field is string and these are valid strings, return them.
        # Let's refine: if schema expects number and it's "Varies", return None. If schema expects string, return "Varies".
        # This function is primarily for numeric conversion, so if it's a known non-numeric, it's not a number.
        if cleaned_check_str == "-" and field_name_for_warning.startswith("Cost"): # Specifically for costs where "-" often means N/A or not for sale
            return None
        return None # For other known non-numeric, assume it means no numeric value.

    cleaned_str = str(value_str).replace(',', '') # Remove commas for thousands separators
    
    # Handle specific textual multipliers or indicators if necessary, though regex might be better for complex cases.
    # Example: if "x2" means something, it's likely handled by specific parsers (like damage_string).
    # This function is for more direct numeric fields.

    if '/m' in cleaned_str.lower(): return value_str # e.g. speed like "30/m"
    if ' or ' in cleaned_str: return value_str # e.g. "10 or 20"

    # Remove trailing asterisks or similar non-numeric annotations if they are common and not part of the value
    if '*' in cleaned_str: cleaned_str = cleaned_str.replace('*', '').strip()
    if cleaned_str.lower().endswith('x') and field_name_for_warning.lower() in ['cost', 'weight', 'cost_credits', 'weight_kg']:
        cleaned_str = cleaned_str[:-1].strip() # For cases like "1000x" in cost/weight

    try:
        if '.' in cleaned_str: # Check for float
            return float(cleaned_str)
        else: # Assume int
            return int(cleaned_str)
    except ValueError:
        # Only print warning if the string isn't overly long (to avoid polluting logs with full descriptions)
        # and if it wasn't an intentionally non-numeric value handled above.
        # if len(str(original_value_for_warning)) < 50 :
        #     print(f"Warning ({data_type_for_warning}): Could not convert '{field_name_for_warning}' to number for '{item_name_for_warning}'. Original CSV value: '{original_value_for_warning}'. Storing as None.")
        return None # Return None if conversion fails

def read_csv_data(file_path, string_data_var_name=None):
    content = None; source_type = "None"
    try:
        if file_path and 'YOUR_PATH_TO_CSV' not in file_path and os.path.exists(file_path):
            with open(file_path, mode='r', encoding='utf-8-sig') as file: content = file.read()
            source_type = f"File: {file_path}"
        elif string_data_var_name and string_data_var_name in globals() and isinstance(globals()[string_data_var_name], str) and globals()[string_data_var_name].strip().count('\n') > 0:
            content = globals()[string_data_var_name]; source_type = f"String Data ({string_data_var_name})"
        if content:
            if content.startswith('\ufeff'): content = content[1:]
            cleaned_content = "\n".join([line for line in content.splitlines() if line.strip()])
            if not cleaned_content: print(f"Warning: CSV content for {source_type} is empty after cleaning."); return []
            reader = csv.DictReader(io.StringIO(cleaned_content))
            print(f"Successfully prepared to read from {source_type}."); return list(reader)
        else: print(f"Warning: No data source configured or found for {file_path or string_data_var_name}."); return []
    except FileNotFoundError: print(f"Error: CSV file not found at '{file_path}'."); return []
    except Exception as e: print(f"Error reading or parsing CSV data from {source_type}: {e}"); return []

def save_json_data(data, output_path, data_type_name):
    if not data: print(f"No data to save for {data_type_name}."); data_to_save = []
    else: data_to_save = sorted(data, key=lambda x: x.get("name", "")) # Ensure 'name' exists or handle missing key
    
    # Correctly form the top-level key based on data_type_name
    list_key_name = f"{data_type_name.lower().replace(' ', '_')}_list"
    wrapper_key_name = f"{data_type_name.lower().replace(' ', '_')}_data"

    final_output = {
        wrapper_key_name: {
            "description": f"Compilation of {data_type_name} for Star Wars SAGA Edition.",
            list_key_name: data_to_save
        }
    }
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir); print(f"Created output directory: {output_dir}")
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_output, f, indent=2)
        print(f"Successfully generated {data_type_name} JSON to: {output_path}\n")
    except Exception as e: print(f"Error writing {data_type_name} JSON to file {output_path}: {e}\n")

# --- Helper functions specific to Species processing (MUST BE DEFINED BEFORE process_species_csv) ---
def species_parse_ability_modifiers(row_dict):
    modifiers = []
    ability_map = {"Str": "Strength", "Dex": "Dexterity", "Con": "Constitution", "Int": "Intelligence", "Wis": "Wisdom", "Cha": "Charisma"}
    species_traits_col_text = row_dict.get('TRAITS', '').strip()
    if "one +2, one -2" in species_traits_col_text:
        modifiers.append({"ability": "Choice", "value": "One ability score +2, one ability score -2"}); return modifiers
    if "add +2 to one ability" in species_traits_col_text and "Str " in species_traits_col_text: # This condition seems very specific, might need review
        modifiers.append({"ability": "Choice", "value": "+2 to one ability score"}); return modifiers
    for csv_col, full_name in ability_map.items():
        val_str = row_dict.get(csv_col, "").strip()
        if val_str:
            cleaned_val_str = val_str.replace('*', '') # Remove asterisks often used for notes
            try: 
                numeric_val = int(cleaned_val_str)
                if numeric_val != 0: # Only add non-zero modifiers
                    modifiers.append({"ability": full_name, "value": numeric_val})
            except ValueError: 
                print(f"Warning (Species): Non-integer ability value '{val_str}' for {full_name} in species '{row_dict.get('SPECIES', 'Unknown')}'.")
    return modifiers


def species_parse_size(size_char):
    if not size_char: return "Unknown"
    size_map = {'S': "Small", 'M': "Medium", 'L': "Large", 'D': "Diminutive", 'T':"Tiny", 'H':"Huge", 'G':"Gargantuan", 'C':"Colossal"}
    # Handle full names possibly already in CSV, or ensure input is always a char code
    cleaned_size_char = size_char.strip()
    if len(cleaned_size_char) > 1 : # If it's likely a full word already
        # Capitalize first letter, rest lower, for consistency if full names are passed
        return cleaned_size_char.capitalize() if cleaned_size_char.lower() in [v.lower() for v in size_map.values()] else cleaned_size_char
    return size_map.get(cleaned_size_char.upper(), cleaned_size_char)


def species_parse_speed(spd_str):
    if not spd_str: return 0 # Default to 0 or None based on schema requirements
    try: 
        # Handle cases like "6 squares" or "6"
        match = re.search(r"(\d+)", spd_str)
        if match:
            return int(match.group(1))
        return int(spd_str.split('/')[0].strip()) # Original logic
    except ValueError: 
        print(f"Warning (Species Speed): Could not parse speed '{spd_str}'. Returning 0.")
        return 0

def species_parse_languages(row_dict):
    languages = set(); basic_q_col = row_dict.get('Basic?', '').strip().upper(); lang1_val = row_dict.get('Language 1', '').strip()
    if basic_q_col == 'Y':
        if "understand only" in lang1_val.lower() or "understand)" in lang1_val.lower() and "basic" in lang1_val.lower(): languages.add("Basic (Understand only)")
        else: languages.add("Basic")
    elif basic_q_col and "understand" in basic_q_col.lower(): languages.add("Basic (Understand only)")
    for key in ['Language 1', 'Language 2', 'Language 3']:
        lang = row_dict.get(key, '').strip()
        if lang:
            is_basic_understand_variant = "basic" in lang.lower() and ("understand only" in lang.lower() or "understand)" in lang.lower())
            is_plain_basic = lang.lower() == "basic"
            if is_basic_understand_variant:
                if "Basic" in languages: languages.remove("Basic")
                languages.add("Basic (Understand only)")
            elif is_plain_basic:
                if "Basic (Understand only)" not in languages: languages.add("Basic")
            else: languages.add(lang)
    return sorted(list(languages))

def species_add_trait_if_new(special_qualities_list, name, description, existing_names_set, defense_types_covered):
    name_lower = name.lower()
    if name_lower not in existing_names_set:
        processed_description = mtr_explanations(description)
        trait_effects = parse_effects_from_text(processed_description, context_skill="Trait") # Trait context
        special_qualities_list.append({"name": name, "description": processed_description, "effects": trait_effects})
        existing_names_set.add(name_lower)
        # Simplified defense coverage check; ideally parse_effects_from_text should identify defense bonuses more reliably
        desc_lower = processed_description.lower()
        if "all defenses" in desc_lower and re.search(r"[+-]\d+", desc_lower): # More generic check for "all defenses"
            defense_types_covered.update(['reflex', 'fortitude', 'will'])
        else:
            if "reflex defense" in desc_lower and re.search(r"[+-]\d+", desc_lower): defense_types_covered.add('reflex')
            if "fortitude defense" in desc_lower and re.search(r"[+-]\d+", desc_lower): defense_types_covered.add('fortitude')
            if "will defense" in desc_lower and re.search(r"[+-]\d+", desc_lower): defense_types_covered.add('will')
        return True
    return False

# --- Helper function for Droid Class Levels (New) ---
def _parse_droid_class_levels(row_dict):
    class_levels = {}
    # Define the exact column names from your CSV that represent classes and their levels
    # This list is based on the sample CSV provided. Adjust if column names differ.
    class_columns = [
        'NON-HEROIC', 'NOBLE', 'SCOUNDREL', 'SCOUT', 'SOLDIER',
        'BOUNTY HUNT.', 'DROID COM.', 'ELITE TROOPER', 'INDEP. DROID',
        'JEDI', 'OFFICER'
        # Add any other class columns present in your Droid CSV here
    ]

    notes_val = None # Placeholder if you have a specific column for class build notes for droids

    for class_col_name in class_columns:
        level_val_str = row_dict.get(class_col_name, '').strip() # row_dict should already have cleaned values
        if level_val_str: # Check if there's any value
            try:
                level_val_int = int(level_val_str)
                if level_val_int > 0:
                    # Clean up common column name variations for better key names in JSON
                    clean_class_name = class_col_name.replace('.', '').replace('NON-HEROIC', 'Non-Heroic').title()
                    # Further specific cleanups if needed:
                    if clean_class_name == "Droid Com": clean_class_name = "Droid Commander"
                    if clean_class_name == "Indep. Droid": clean_class_name = "Independent Droid"
                    if clean_class_name == "Bounty Hunt": clean_class_name = "Bounty Hunter"
                    
                    class_levels[clean_class_name] = level_val_int
            except ValueError:
                # Only log if it's not an empty string or an expected non-numeric like "-"
                if level_val_str not in ['', '-']:
                    print(f"Warning (Droid Class Levels): Non-integer value '{level_val_str}' for class '{class_col_name}' in droid '{row_dict.get('DROID', 'Unknown Droid')}'.")
    
    # The schema expects a "notes" field within typical_class_levels_summary
    final_summary = {"notes": notes_val}
    final_summary.update(class_levels) # Add the parsed class levels
    
    return final_summary


# --- 3. PROCESSING FUNCTIONS ---

def process_species_csv():
    print("Processing Species...")
    species_traits_data = {}
    raw_traits_data = read_csv_data(SPECIES_TRAITS_CSV_PATH)
    if raw_traits_data:
        for row in raw_traits_data:
            s_name = clean_value(row.get('SPECIES', '')); t_name = clean_value(row.get('TRAIT', '')); benefit = clean_value(row.get('BENEFIT', ''))
            if s_name and t_name: species_traits_data.setdefault(s_name, []).append({"name": t_name, "description": benefit})
    
    raw_species_data = read_csv_data(SPECIES_MAIN_CSV_PATH)
    processed_species = []
    if not raw_species_data: save_json_data(processed_species, SPECIES_JSON_PATH, "Species"); return
    
    for row_raw in raw_species_data:
        row = {k: clean_value(v) for k,v in row_raw.items()} # Clean values once per row
        name = row.get('SPECIES', '')
        if not name or not row.get('BOOK'): continue # Ensure essential fields are present

        current_sq_list, existing_trait_names, defense_types_covered = [], set(), set()
        base_name_for_trait_lookup = name.split('(')[0].strip()
        trait_sources_to_check = [name, base_name_for_trait_lookup]
        if "Droid," in name: trait_sources_to_check.append("Droid") # Special case for Droid species traits

        for lookup_name in set(trait_sources_to_check): # Use set to avoid redundant lookups
            if lookup_name in species_traits_data:
                for trait_data in species_traits_data[lookup_name]:
                    species_add_trait_if_new(current_sq_list, trait_data['name'], trait_data['description'], existing_trait_names, defense_types_covered)
        
        vis_char = row.get('Vis', '').strip().upper()
        if vis_char == 'L': species_add_trait_if_new(current_sq_list, "Low-Light Vision", "Ignores concealment (but not total concealment) from darkness.", existing_trait_names, defense_types_covered)
        elif vis_char == 'D': species_add_trait_if_new(current_sq_list, "Darkvision", "Ignores concealment (including total concealment) from darkness.", existing_trait_names, defense_types_covered)
        
        defense_map = {'Ref': ('reflex', 'Reflex Defense'), 'Fort': ('fortitude', 'Fortitude Defense'), 'Will': ('will', 'Will Defense')}
        for def_col, (def_key, def_full_name) in defense_map.items():
            def_val_str = row.get(def_col, '')
            if def_val_str: # Check if there's any value
                bonus = attempt_numeric_conversion(def_val_str, name, def_col, 'Species Def')
                if bonus is not None and isinstance(bonus, int) and bonus != 0: # Ensure it's a valid, non-zero number
                    if def_key not in defense_types_covered: # Only add if not already covered by a more general trait
                        species_add_trait_if_new(current_sq_list, f"Species Bonus to {def_full_name}", f"Gains a {bonus:+d} species bonus to {def_full_name}.", existing_trait_names, defense_types_covered)

        species_obj = {
            "name": name, 
            "pc_or_npc": row.get('NPC or PC?', '').strip(), 
            "ability_modifiers": species_parse_ability_modifiers(row), 
            "size": species_parse_size(row.get('Size', '')), 
            "speed_squares": species_parse_speed(row.get('Spd', '')), 
            "special_qualities": sorted(current_sq_list, key=lambda x: x['name']), 
            "automatic_languages": species_parse_languages(row), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        processed_species.append(species_obj)
    save_json_data(processed_species, SPECIES_JSON_PATH, "Species")

def process_skills_csv():
    print("Processing Skills...")
    skills_base_data = {}
    raw_def_data = read_csv_data(SKILLS_DEF_CSV_PATH)
    if not raw_def_data: save_json_data([], SKILLS_JSON_PATH, "Skills"); return
    for row_raw in raw_def_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        skill_name = row.get('SKILLS', '')
        if not skill_name: continue
        class_skills = []
        class_cols_to_check = ['Jedi', 'Noble', 'Scoundrel', 'Scout', 'Soldier', '  Scoundrel'] # Note: "  Scoundrel" might be a typo in CSV
        for class_col_raw in class_cols_to_check:
            class_col_cleaned = class_col_raw.strip() # Clean the column name itself
            if row.get(class_col_raw, '').strip().lower() == 'x' and class_col_cleaned not in class_skills:
                class_skills.append(class_col_cleaned)
        skills_base_data[skill_name] = {
            "name": skill_name, 
            "key_ability": row.get('Ability', '').strip(), 
            "armor_check_penalty_applies_generally": row.get('Armor check penalty?', '').strip().upper() == 'Y', 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip(), 
            "class_skill_for": sorted(list(set(class_skills))), # Ensure unique and sorted
            "common_uses": {}
        }
    raw_uses_data = read_csv_data(SKILL_USES_CSV_PATH)
    if raw_uses_data:
        for row_raw in raw_uses_data:
            row = {k: clean_value(v) for k,v in row_raw.items()}
            skill_name = row.get('Skill', ''); use_name = row.get('Use', '')
            if not skill_name or not use_name or skill_name not in skills_base_data: continue
            normalized_use = use_name.lower().strip() # Use lower for consistent keying
            skills_base_data[skill_name]["common_uses"][normalized_use] = {
                "use_name": use_name, 
                "source_book_for_use": skills_base_data[skill_name]["source_book"], 
                "page_for_use": skills_base_data[skill_name]["page"], 
                "related_ability_for_use": row.get('Ability', skills_base_data[skill_name]["key_ability"]).strip(), 
                "trained_only": row.get('Trained', '').strip().upper() == 'Y', 
                "armor_check_penalty_for_this_use": row.get('AP', '').strip().upper() == 'YES', 
                "dc_details": row.get('DC', '').strip(), 
                "notes": mtr_explanations(row.get('Notes', '').strip()), 
                "requirements": None, # Will be filled by actions data if available
                "take_10_20_allowed": row.get('Take 10/20', '').strip(), 
                "retry_info": mtr_explanations(row.get('Retry', '').strip()), 
                "time_to_perform": row.get('Time', '').strip()
            }
    raw_actions_data = read_csv_data(SKILL_ACTIONS_CSV_PATH)
    if raw_actions_data:
        for row_raw in raw_actions_data:
            row = {k: clean_value(v) for k,v in row_raw.items()}
            skill_name = row.get('SKILL', ''); action_name = row.get('ACTION', '')
            if not skill_name or not action_name or skill_name not in skills_base_data: continue
            normalized_action = action_name.lower().strip() # Use lower for consistent keying
            use_obj = skills_base_data[skill_name]["common_uses"].get(normalized_action)
            if use_obj: # Update existing use object
                use_obj["requirements"] = mtr_explanations(row.get('REQUIREMENTS', '').strip()) or use_obj.get("requirements")
                use_obj["trained_only"] = row.get('Trained Only?', '').strip().lower() == 'x' or use_obj.get("trained_only", False)
                if row.get('BOOK','').strip(): use_obj["source_book_for_use"] = row.get('BOOK','').strip()
                if row.get('PAGE','').strip(): use_obj["page_for_use"] = str(row.get('PAGE','')).strip()
            else: # Create new use object if not found (less likely if SKILL_USES_CSV is comprehensive)
                skills_base_data[skill_name]["common_uses"][normalized_action] = {
                    "use_name": action_name, 
                    "source_book_for_use": row.get('BOOK', skills_base_data[skill_name]["source_book"]).strip(), 
                    "page_for_use": str(row.get('PAGE', skills_base_data[skill_name]["page"])).strip(), 
                    "related_ability_for_use": skills_base_data[skill_name]["key_ability"], 
                    "trained_only": row.get('Trained Only?', '').strip().lower() == 'x', 
                    "armor_check_penalty_for_this_use": None, # Not in this CSV
                    "dc_details": None, # Not in this CSV
                    "notes": None, # Not in this CSV
                    "requirements": mtr_explanations(row.get('REQUIREMENTS', '').strip()), 
                    "take_10_20_allowed": None, # Not in this CSV
                    "retry_info": None, # Not in this CSV
                    "time_to_perform": None # Not in this CSV
                }
    final_skill_list = []
    for skill_name_key in sorted(skills_base_data.keys()):
        skill_obj = skills_base_data[skill_name_key]
        skill_obj["common_uses"] = sorted(list(skill_obj["common_uses"].values()), key=lambda x: x["use_name"])
        final_skill_list.append(skill_obj)
    save_json_data(final_skill_list, SKILLS_JSON_PATH, "Skills")

def process_feats_csv():
    print("Processing Feats...")
    raw_data = read_csv_data(FEATS_CSV_PATH)
    processed_feats = []
    if not raw_data: save_json_data(processed_feats, FEATS_JSON_PATH, "Feats"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('FEAT', row.get('Feat', '')) # Check alternative column names
        if not name: continue
        benefit_text = mtr_explanations(row.get('BENEFIT', row.get('Benefit', '')))
        # Handle multiple possible desc columns, prioritizing more specific ones
        full_text_additional_raw = row.get('Desc.', row.get('DESC', row.get('Desc', row.get('Description', ''))))
        full_text_additional = mtr_explanations(full_text_additional_raw) if full_text_additional_raw else None
        
        prereq_text_raw = get_prerequisite_text_from_row_dict(row, ['PREREQUISITES', 'PREREQUISITE', 'Prerequisites', 'Prerequisite'])
        tags_str = row.get('TAG', '')
        feat_types = []
        if tags_str:
            cleaned_tags = tags_str.replace('][', ',').replace('[', '').replace(']', '') # Handle "][", "[", "]"
            feat_types = sorted([t.strip() for t in cleaned_tags.split(',') if t.strip()])
        
        bonus_classes = []
        base_class_columns = ["Jedi", "Noble", "Scoundrel", "Scout", "Soldier"] # Standard SAGA base classes
        for char_class_col_name in base_class_columns:
            class_marker = row.get(char_class_col_name, '')
            if class_marker.strip().lower() == 'x': # Check for 'x' or similar marker
                bonus_classes.append(char_class_col_name)

        primary_effect_text = benefit_text if benefit_text else full_text_additional
        
        feat = {
            "name": name, 
            "type": feat_types if feat_types else ["Unknown"], 
            "prerequisites_text": prereq_text_raw, 
            "prerequisites_structured": parse_prerequisites_from_text(prereq_text_raw), 
            "benefit_summary": benefit_text, 
            "effects": parse_effects_from_text(primary_effect_text), # Parse based on primary text
            "bonus_feat_for_classes": sorted(list(set(bonus_classes))), 
            "source_book": row.get('BOOK', row.get('Source', '')).strip(), 
            "page": str(row.get('PAGE', row.get('Page', ''))).strip(), 
            "special_note": row.get('SPECIAL', row.get('Special', '')).strip() or None
        }
        if full_text_additional and full_text_additional != benefit_text : 
            feat["full_text_description"] = full_text_additional
        processed_feats.append(feat)
    save_json_data(processed_feats, FEATS_JSON_PATH, "Feats")

def process_talents_csv():
    print("Processing Talents...")
    raw_data = read_csv_data(TALENTS_CSV_PATH)
    processed_talents = []
    if not raw_data: save_json_data(processed_talents, TALENTS_JSON_PATH, "Talents"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('TALENT', '')
        if not name: continue
        benefit_text = mtr_explanations(row.get('BENEFIT', row.get('Benefit', '')))
        full_text_additional_raw = row.get('Desc.', row.get('DESC', row.get('Desc', row.get('Description', ''))))
        full_text_additional = mtr_explanations(full_text_additional_raw) if full_text_additional_raw else None
        
        prereq_text_raw = get_prerequisite_text_from_row_dict(row, ['PREREQUISITE', 'Prerequisites'])
        class_association_val = row.get('CLASS', '')
        associated_classes = sorted(list(set([c.strip() for c in class_association_val.split(',') if c.strip()]))) if class_association_val else ["Unknown"]
        
        primary_effect_text = benefit_text if benefit_text else full_text_additional

        talent = {
            "name": name, 
            "talent_tree": row.get('TREE', 'Unknown').strip(), 
            "class_association": associated_classes, 
            "prerequisites_text": prereq_text_raw, 
            "prerequisites_structured": parse_prerequisites_from_text(prereq_text_raw), 
            "description": benefit_text, # Main benefit in "description"
            "effects": parse_effects_from_text(primary_effect_text), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        if full_text_additional and full_text_additional != benefit_text : 
            talent["full_text_description"] = full_text_additional # Store extra desc if different
        processed_talents.append(talent)
    save_json_data(processed_talents, TALENTS_JSON_PATH, "Talents")

def process_techniques_csv():
    print("Processing Force Techniques...")
    raw_data = read_csv_data(TECHNIQUES_CSV_PATH)
    processed_techniques = []
    if not raw_data: save_json_data(processed_techniques, TECHNIQUES_JSON_PATH, "Force Techniques"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('FORCE TECHNIQUE', '')
        if not name: continue
        effect_text = mtr_explanations(row.get('EFFECT', ''))
        full_text_additional_raw = row.get('Desc.', '')
        full_text_additional = mtr_explanations(full_text_additional_raw) if full_text_additional_raw else None
        prereq_text_raw = get_prerequisite_text_from_row_dict(row, ['PREREQUISITE', 'Prerequisites'])
        context_skill = "Use the Force" # Default for Force items
        primary_effect_text = effect_text if effect_text else full_text_additional

        technique = {
            "name": name, 
            "force_power_association": row.get('Force Power Association', '').strip() or None, 
            "prerequisites_text": prereq_text_raw, 
            "prerequisites_structured": parse_prerequisites_from_text(prereq_text_raw), 
            "effect_description": effect_text, 
            "effects": parse_effects_from_text(primary_effect_text, context_skill), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        if full_text_additional and full_text_additional != effect_text: 
            technique["full_text_additional_desc"] = full_text_additional
        processed_techniques.append(technique)
    save_json_data(processed_techniques, TECHNIQUES_JSON_PATH, "Force Techniques")

def process_secrets_csv():
    print("Processing Force Secrets...")
    raw_data = read_csv_data(SECRETS_CSV_PATH)
    processed_secrets = []
    if not raw_data: save_json_data(processed_secrets, SECRETS_JSON_PATH, "Force Secrets"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('FORCE SECRET', '')
        if not name: continue
        effect_text = mtr_explanations(row.get('EFFECT', ''))
        full_text_additional_raw = row.get('Desc.', '')
        full_text_additional = mtr_explanations(full_text_additional_raw) if full_text_additional_raw else None
        prereq_text_raw = get_prerequisite_text_from_row_dict(row, ['PREREQUISITE', 'Prerequisites'])
        context_skill = "Use the Force"
        primary_effect_text = effect_text if effect_text else full_text_additional

        secret = {
            "name": name, 
            "line_of_sight_requirement_text": row.get('LOS', '').strip() or None, 
            "prerequisites_text": prereq_text_raw, 
            "prerequisites_structured": parse_prerequisites_from_text(prereq_text_raw), 
            "effect_description": effect_text, 
            "effects": parse_effects_from_text(primary_effect_text, context_skill), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        if full_text_additional and full_text_additional != effect_text: 
            secret["full_text_additional_desc"] = full_text_additional
        processed_secrets.append(secret)
    save_json_data(processed_secrets, SECRETS_JSON_PATH, "Force Secrets")

def process_regimens_csv():
    print("Processing Training Regimens...")
    raw_data = read_csv_data(REGIMENS_CSV_PATH)
    processed_regimens = []
    if not raw_data: save_json_data(processed_regimens, REGIMENS_JSON_PATH, "Training Regimens"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('FORCE REGIMEN', '')
        if not name: continue
        effect_text = mtr_explanations(row.get('EFFECT', ''))
        full_text_additional_raw = row.get('Desc.', '')
        full_text_additional = mtr_explanations(full_text_additional_raw) if full_text_additional_raw else None
        prereq_text_raw = get_prerequisite_text_from_row_dict(row, ['PREREQUISITE', 'Prerequisites'])
        
        lightsaber_col_val = row.get(' Lightsaber?', row.get('Lightsaber?', '')).strip().lower() # Check both possible column names
        act_text = row.get('ACT', '').strip()
        
        context_skill = "Use the Force"; # Default context
        if "mechanics check" in act_text.lower(): context_skill = "Mechanics"
        elif "athletics check" in act_text.lower(): context_skill = "Athletics"
        
        primary_effect_text = effect_text if effect_text else full_text_additional
        
        regimen = {
            "name": name, 
            "action_text": act_text or None, 
            "target_info": row.get('Target', '').strip() or None, 
            "is_lightsaber_related": True if lightsaber_col_val == 'yes' else (False if lightsaber_col_val == 'no' else None), 
            "time_to_complete": row.get('Time', '').strip() or None, 
            "prerequisites_text": prereq_text_raw, 
            "prerequisites_structured": parse_prerequisites_from_text(prereq_text_raw), 
            "effect_description": effect_text, 
            "effects": parse_effects_from_text(primary_effect_text, context_skill), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        if full_text_additional and full_text_additional != effect_text: 
            regimen["full_text_additional_desc"] = full_text_additional
        processed_regimens.append(regimen)
    save_json_data(processed_regimens, REGIMENS_JSON_PATH, "Training Regimens")

def process_starship_maneuvers_csv():
    print("Processing Starship Maneuvers...")
    raw_data = read_csv_data(STARSHIP_MANEUVERS_CSV_PATH)
    processed_maneuvers = []
    if not raw_data: save_json_data(processed_maneuvers, STARSHIP_MANEUVERS_JSON_PATH, "Starship Maneuvers"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('STARSHIP MANEUVER', '')
        if not name: continue
        effect_text = mtr_explanations(row.get('EFFECT', ''))
        descriptor_str = row.get('DESCRIPTOR', '')
        descriptor_tags = []
        if descriptor_str:
            cleaned_descriptors = descriptor_str.replace('][', ',').replace('], [', ',') # Handle variations
            cleaned_descriptors = cleaned_descriptors.replace('[', '').replace(']', '')
            descriptor_tags = sorted([t.strip() for t in cleaned_descriptors.split(',') if t.strip()])
        
        action_type_text = parse_action_type(row.get('Time', ''))
        context_skill = "Pilot"; # Default for starship maneuvers
        skill_check_raw_text = row.get('CHECK', '')
        if skill_check_raw_text:
             if "use the force" in skill_check_raw_text.lower(): context_skill = "Use the Force"
             elif "mechanics" in skill_check_raw_text.lower(): context_skill = "Mechanics"

        maneuver = {
            "name": name, 
            "descriptor_tags": descriptor_tags if descriptor_tags else [], 
            "action_to_activate": action_type_text or "Unknown", 
            "target_info": row.get('Target', '').strip() or None, 
            "skill_check_raw_text": skill_check_raw_text or None, 
            "effect_description": effect_text, 
            "effects": parse_effects_from_text(effect_text, context_skill), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        processed_maneuvers.append(maneuver)
    save_json_data(processed_maneuvers, STARSHIP_MANEUVERS_JSON_PATH, "Starship Maneuvers")

def process_force_powers_csv():
    print("Processing Force Powers...")
    raw_data = read_csv_data(FORCE_POWERS_CSV_PATH)
    processed_powers = []
    if not raw_data: save_json_data(processed_powers, FORCE_POWERS_JSON_PATH, "Force Powers"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        power_name_raw = row.get('FORCE POWER', '')
        if not power_name_raw: continue
        name = power_name_raw; name_qualifier = None
        match_qualifier = re.search(r"\[([\w\s-]+)\]$", power_name_raw) # Check for qualifier like [Move Object]
        if match_qualifier: 
            name_qualifier = match_qualifier.group(1).strip()
            name = power_name_raw[:match_qualifier.start()].strip()
        
        full_description_text = mtr_explanations(row.get('Desc.', ''))
        effect_summary_text = mtr_explanations(row.get('EFFECT', ''))
        
        # Standardize descriptor keys for consistency
        descriptors = {
            "dark_light_affinity": row.get('   Dark/Light', row.get('Dark/Light','')).strip() or None, 
            "is_lightsaber_form_related": row.get('   Lightsaber form   ', row.get('Lightsaber form','')).strip().lower() == 'x', 
            "is_mind_affecting": row.get(' Mind-affect.', row.get('Mind-affecting','')).strip().lower() == 'x', 
            "is_telekinetic": row.get('  Telekinetic', row.get('Telekinetic','')).strip().lower() == 'x', 
            "is_unleashed_power": row.get('  Unleashed', row.get('Unleashed','')).strip().lower() == 'x'
        }
        if descriptors["dark_light_affinity"] and descriptors["dark_light_affinity"].lower() not in ['dark', 'light']:
            descriptors["dark_light_affinity"] = None # Ensure only valid values or None

        power = {
            "name": name, 
            "name_qualifier": name_qualifier, 
            "full_text_description": full_description_text or None, 
            "action_to_activate": parse_action_type(row.get('Action to activate', '')), 
            "action_to_maintain": parse_action_type(row.get('Action to maintain', '')) or None, 
            "target_info": row.get('Target', '').strip() or None, 
            "range_squares": row.get('Sq.', '').strip() or None, 
            "line_of_sight_requirement_text": row.get('LOS', '').strip() or None, 
            "effect_summary_dc_progression": effect_summary_text, # This is likely the text with DC tiers
            "effects": parse_effects_from_text(effect_summary_text, context_skill="Use the Force"), 
            "descriptors": descriptors, 
            "special_rules_and_notes": parse_special_rules_from_description(full_description_text), 
            "source_book": row.get('BOOK', '').strip(), 
            "page": str(row.get('PAGE', '')).strip()
        }
        processed_powers.append(power)
    save_json_data(processed_powers, FORCE_POWERS_JSON_PATH, "Force Powers")

def process_prestige_classes_csv():
    print("Processing Prestige Classes...")
    raw_rows_list = []
    source_type = "None"
    # Using csv.reader for more control over potentially irregular CSV structures
    try:
        if PRESTIGE_CLASSES_CSV_PATH and 'YOUR_PATH_TO_CSV' not in PRESTIGE_CLASSES_CSV_PATH and os.path.exists(PRESTIGE_CLASSES_CSV_PATH):
            with open(PRESTIGE_CLASSES_CSV_PATH, mode='r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                first_line_peek_raw = next(reader, None)
                if first_line_peek_raw and first_line_peek_raw[0].startswith('\ufeff'): # Handle BOM
                    first_line_peek_raw[0] = first_line_peek_raw[0][1:]
                if first_line_peek_raw: raw_rows_list.append(first_line_peek_raw)
                for row_content in reader: raw_rows_list.append(row_content) # Read rest of the file
            source_type = f"File: {PRESTIGE_CLASSES_CSV_PATH}"
        else:
            print(f"Warning: Prestige Class CSV file path not set or placeholder used ({PRESTIGE_CLASSES_CSV_PATH}).")
            save_json_data([], PRESTIGE_CLASSES_JSON_PATH, "Prestige Classes"); return
        print(f"Successfully read {len(raw_rows_list)} raw lines from {source_type}.")
    except FileNotFoundError: print(f"Error: Prestige Class CSV file not found at '{PRESTIGE_CLASSES_CSV_PATH}'."); save_json_data([], PRESTIGE_CLASSES_JSON_PATH, "Prestige Classes"); return
    except Exception as e: print(f"Error reading Prestige Class CSV: {e}"); save_json_data([], PRESTIGE_CLASSES_JSON_PATH, "Prestige Classes"); return

    processed_classes = []
    current_class_obj = None
    main_header_map = {} 
    parsing_state = "EXPECTING_MAIN_HEADER" 
    # More comprehensive prerequisite column names based on typical CSV variations
    prereq_column_names = ["TRAINED SKILL PREREQUISITE", "SKILL FOCUS PREREQ.", "FEAT PREREQUISITE", "TALENT PREREQUISITE", "OTHER PREREQUISITE", "PREREQUISITES"]

    for i, row_list_raw in enumerate(raw_rows_list):
        row_list = [clean_value(cell) for cell in row_list_raw] # Clean each cell

        if parsing_state == "EXPECTING_MAIN_HEADER":
            # Check for key header columns to identify the main header row
            if "CLASS" in row_list and "HP" in row_list and any(prc in row_list for prc in ["PREREQUISITES", "TRAINED SKILL PREREQUISITE", "FEAT PREREQUISITE"]):
                main_header_map.clear() 
                for idx, header_text in enumerate(row_list):
                    main_header_map[header_text.strip()] = idx # Map header text to column index
                parsing_state = "EXPECTING_CLASS_DATA"
                print(f"Found Prestige Class main headers at row {i}: {list(main_header_map.keys())}")
                continue
        
        is_new_class_row = False
        if main_header_map and (parsing_state == "EXPECTING_CLASS_DATA" or parsing_state == "PARSING_SUBSECTION_DATA"): # Ensure headers are mapped
            book_idx = main_header_map.get('BOOK', -1); class_idx = main_header_map.get('CLASS', -1)
            if book_idx != -1 and class_idx != -1 and \
               len(row_list) > max(book_idx, class_idx) and \
               row_list[book_idx] and row_list[class_idx]: # Check if Book and Class fields have data
                 is_new_class_row = True
        
        is_subsection_header_row = len(row_list) > 2 and row_list[2] and "Can use the following talent trees" in row_list[2] # Identifies the talent tree header
        is_empty_line = all(not cell for cell in row_list)

        if is_new_class_row:
            if current_class_obj: processed_classes.append(current_class_obj) # Save previous class
            combined_prereq_text = get_prerequisite_text_from_row_list(row_list, main_header_map, prereq_column_names)
            
            # Safely get values using mapped indices, providing defaults or None if column not found
            current_class_obj = {
                "name": row_list[main_header_map.get('CLASS', 2)] if main_header_map.get('CLASS', -1) < len(row_list) else "Unknown Class",
                "source_book": row_list[main_header_map.get('BOOK', 0)] if main_header_map.get('BOOK', -1) < len(row_list) else "Unknown Source",
                "page": str(row_list[main_header_map.get('PAGE', 1)]) if main_header_map.get('PAGE', -1) < len(row_list) else "N/A",
                "hit_points_die": row_list[main_header_map.get('HP', 3)] if main_header_map.get('HP', -1) < len(row_list) else "N/A",
                "force_points_per_level": clean_value(row_list[main_header_map.get('Force Points', 4)]) if main_header_map.get('Force Points', -1) < len(row_list) else "N/A",
                "defense_bonuses": {
                    "reflex": clean_value(row_list[main_header_map.get('Ref',5)]) if main_header_map.get('Ref',-1) < len(row_list) else "N/A", 
                    "fortitude": clean_value(row_list[main_header_map.get('Fort',6)]) if main_header_map.get('Fort',-1) < len(row_list) else "N/A", 
                    "will": clean_value(row_list[main_header_map.get('Will',7)]) if main_header_map.get('Will',-1) < len(row_list) else "N/A"
                },
                "minimum_character_level_text": row_list[main_header_map.get('Min lvl', 8)] if main_header_map.get('Min lvl', -1) < len(row_list) else None,
                "prerequisites_summary": {
                    key: (row_list[main_header_map[key]] if main_header_map.get(key, -1) < len(row_list) and main_header_map.get(key, -1) != -1 else None) 
                    for key in prereq_column_names if main_header_map.get(key) is not None # Only include existing prereq columns
                },
                "prerequisites_structured": parse_prerequisites_from_text(combined_prereq_text),
                "group_heading": (row_list[main_header_map['Group Heading']] if main_header_map.get('Group Heading', -1) < len(row_list) and main_header_map.get('Group Heading', -1) != -1 else None),
                "available_talent_trees": [], "level_progression": []}
            parsing_state = "EXPECTING_SUBSECTION_HEADER"
        
        elif parsing_state == "EXPECTING_SUBSECTION_HEADER" and is_subsection_header_row:
            parsing_state = "PARSING_SUBSECTION_DATA" # Transition to parsing talent trees and level progression
            
        elif parsing_state == "PARSING_SUBSECTION_DATA" and current_class_obj:
            if is_empty_line: # Empty line might signify end of section or transition
                try: # Peek ahead to see if the next line is a new class
                    next_row_peek_raw = raw_rows_list[i+1] if (i+1) < len(raw_rows_list) else None
                    if next_row_peek_raw:
                        next_row_peek_cleaned = [clean_value(c) for c in next_row_peek_raw]
                        peek_book_idx = main_header_map.get('BOOK', -1); peek_class_idx = main_header_map.get('CLASS', -1)
                        if peek_book_idx != -1 and peek_class_idx != -1 and \
                           len(next_row_peek_cleaned) > max(peek_book_idx, peek_class_idx) and \
                           next_row_peek_cleaned[peek_book_idx] and next_row_peek_cleaned[peek_class_idx]:
                            parsing_state = "EXPECTING_CLASS_DATA" # Next line is a new class
                    else: parsing_state = "EXPECTING_CLASS_DATA" # End of file
                except IndexError: parsing_state = "EXPECTING_CLASS_DATA" # End of file
                continue 

            # Column indices for talent trees and level progression (relative to start of row_list)
            tt_name_idx, tt_source_idx = 2, 4 # Talent Tree Name, Talent Tree Source
            lvl_idx, bab_idx, talent_marker_idx, class_feature_idx_actual, special_abil_idx_actual = 6, 7, 8, 9, 10

            talent_tree_name = row_list[tt_name_idx] if len(row_list) > tt_name_idx else ''
            talent_tree_source_raw = row_list[tt_source_idx] if len(row_list) > tt_source_idx else ''
            if talent_tree_name:
                final_talent_tree_source = talent_tree_source_raw.strip()
                if final_talent_tree_source.upper() == 'PRC' and current_class_obj: # If source is "PRC", use class name
                    final_talent_tree_source = current_class_obj["name"]
                current_class_obj["available_talent_trees"].append({"tree_name": talent_tree_name.strip(), "source_description": final_talent_tree_source})

            level_val_str = row_list[lvl_idx] if len(row_list) > lvl_idx else ''
            if level_val_str.isdigit(): # Check if it's a valid level number
                level_val_int = int(level_val_str)
                current_class_obj["level_progression"].append({
                    "level": level_val_int,
                    "bab": (row_list[bab_idx].strip() if len(row_list) > bab_idx else ''),
                    "gains_talent_choice": ((row_list[talent_marker_idx].strip().lower() == 'x') if len(row_list) > talent_marker_idx else False),
                    "class_feature": (row_list[class_feature_idx_actual].strip() or None if len(row_list) > class_feature_idx_actual else None),
                    "special_abilities": (row_list[special_abil_idx_actual].strip() or None if len(row_list) > special_abil_idx_actual else None)
                })
    
    if current_class_obj: processed_classes.append(current_class_obj) # Append the last processed class
    if not processed_classes: print("Warning: No prestige classes were successfully parsed.")
    save_json_data(processed_classes, PRESTIGE_CLASSES_JSON_PATH, "Prestige Classes")

def process_droids_csv(): # New function for Droid Chassis
    print("Processing Droid Chassis...")
    raw_data = read_csv_data(DROID_CHASSIS_CSV_PATH)
    processed_droids = []

    if not raw_data:
        save_json_data(processed_droids, DROID_CHASSIS_JSON_PATH, "Droid Chassis")
        return

    for row_idx, row_dict_raw in enumerate(raw_data):
        # Clean all values in the row initially
        row = {k: clean_value(v) for k, v in row_dict_raw.items()}

        name = row.get('DROID', '')
        book = row.get('BOOK', '')
        page_str = str(row.get('PAGE', '')) # Ensure page is a string for ID generation

        if not name or not book or not page_str: # Check page_str instead of page
            print(f"Warning (Droids): Skipping row {row_idx + 2} due to missing Droid Name, Book, or Page.")
            continue

        # Generate ID: make it robust against special characters
        id_base = f"{name}_{book}_{page_str}".lower()
        id_base = re.sub(r'[^a-z0-9_]+', '_', id_base) # Replace non-alphanumeric (excluding underscore) with underscore
        droid_id = re.sub(r'_+', '_', id_base).strip('_') # Remove multiple underscores and leading/trailing


        droid_obj = {
            "id": droid_id,
            "name": name,
            "primary_source": {
                "source_book": book,
                "page": page_str, # Store original page string
                "reference_type": "primary_definition" 
            },
            "full_text_description": None, 
            "manufacturer": row.get('MANUFACTURER', None),
            "cl": attempt_numeric_conversion(row.get('CL (correct)'), name, 'CL (correct)', 'Droid'),
            "cl_source_original": attempt_numeric_conversion(row.get('CL (Source)'), name, 'CL (Source)', 'Droid'),
            "size_category_text": species_parse_size(row.get('Size', '')), 
            "degree": attempt_numeric_conversion(row.get('Degree'), name, 'Degree', 'Droid'),
            "typical_class_levels_summary": _parse_droid_class_levels(row), # Use the new helper
            "stat_block_details": { 
                "initiative_modifier": None, "senses_perception_modifier": None, "senses_special_qualities": [],
                "defenses": {"reflex_defense_total": None, "reflex_defense_flat_footed": None, "fortitude_defense_total": None, "will_defense_total": None, "armor_bonus_to_reflex": None, "damage_reduction_dr_value": None, "shield_rating_sr_total": None},
                "hit_points_total": None, "damage_threshold_base": None, "speed_systems": [], "fighting_space": None, "reach": None, "base_attack_bonus": None, "grapple_modifier": None,
                "ability_scores": {"strength": None, "dexterity": None, "intelligence": None, "wisdom": None, "charisma": None},
                "skills": [], "feats": [], "talents": [], "base_equipment_and_systems": [], "special_qualities_summary": []
            },
            "availability_cost_info": {
                "availability_code": row.get('Availability', None),
                "cost_new_credits": attempt_numeric_conversion(row.get('Cost (new)'), name, 'Cost (new)', 'Droid'),
                "cost_used_credits": attempt_numeric_conversion(row.get('Cost (used)'), name, 'Cost (used)', 'Droid'),
                "cost_notes": None 
            },
            "additional_notes_and_modifications": row.get('COMMENTS & MODIFICATIONS', None),
            "tags": [], 
            "image_url": None,
            "additional_source_references": []
        }
        processed_droids.append(droid_obj)

    save_json_data(processed_droids, DROID_CHASSIS_JSON_PATH, "Droid Chassis")


# --- 4. MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting SAGA Index CSV to JSON Conversion Process (V4 - Full Integration)...\n")
    if PROCESS_CONFIG.get("species", False): process_species_csv()
    if PROCESS_CONFIG.get("skills", False): process_skills_csv()
    if PROCESS_CONFIG.get("feats", False): process_feats_csv()
    if PROCESS_CONFIG.get("talents", False): process_talents_csv()
    if PROCESS_CONFIG.get("techniques", False): process_techniques_csv()
    if PROCESS_CONFIG.get("secrets", False): process_secrets_csv()
    if PROCESS_CONFIG.get("regimens", False): process_regimens_csv()
    if PROCESS_CONFIG.get("starship_maneuvers", False): process_starship_maneuvers_csv()
    if PROCESS_CONFIG.get("force_powers", False): process_force_powers_csv()
    if PROCESS_CONFIG.get("prestige_classes", False): process_prestige_classes_csv()
    if PROCESS_CONFIG.get("droids", False): process_droids_csv() # Added call for droid processing
    print("\nConfigured CSV processing complete.")