import json
import csv
import io
import re
import os

# --- 1. CONFIGURATION ---
LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'

# Input CSV Paths for Item Elements
ARMOR_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Armor.csv')
MELEE_WEAPONS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Melee.csv')
RANGED_WEAPONS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Ranged.csv')
ACCESSORIES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Accessories.csv')
DEFENSES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Defenses.csv') # For Defensive Items like mines
EQUIPMENT_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Equipment.csv')
VEHICLES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Vehicles.csv')
STARSHIPS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Starships.csv')
EXPLOSIVES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Explosives.csv')
TECHSPEC_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-TechSpec.csv')
TEMPLATES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Templates.csv')
DROID_SYSTEMS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Droid Systems.csv')
HAZARDS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Hazards.csv')


# Output JSON Paths for Item Elements
ARMOR_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\armor.json')
MELEE_WEAPONS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\melee_weapons.json')
RANGED_WEAPONS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\ranged_weapons.json')
ACCESSORIES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\accessories.json')
DEFENSIVE_ITEMS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\defensive_items.json')
EQUIPMENT_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\equipment_general.json')
VEHICLES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\vehicles.json')
STARSHIPS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\starships.json')
EXPLOSIVES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\explosives.json')
TECHSPEC_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\tech_specialist_upgrades.json')
TEMPLATES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\templates.json')
DROID_SYSTEMS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\droid_systems.json')
HAZARDS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\hazards.json')


# --- SCRIPT EXECUTION CONFIGURATION ---
PROCESS_CONFIG = {
    "armor": False,
    "melee_weapons": False,
    "ranged_weapons": False,
    "accessories": False,
    "defensive_items": False,
    "equipment_general": False,
    "vehicles": False,
    "starships": False,
    "explosives": False,
    "tech_specialist_upgrades": False,
    "templates": False,
    "droid_systems": False,
    "hazards": True,
}

# --- 2. GENERIC HELPER FUNCTIONS ---

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

def read_csv_data(file_path, string_data_var_name=None, known_delimiter=None, use_direct_reader=False):
    content = None; source_type = "None"; reader_obj = None
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
            if use_direct_reader:
                print(f"Using direct csv.reader for {source_type}.")
                return list(csv.reader(io.StringIO(cleaned_content)))
            if known_delimiter:
                reader_obj = csv.DictReader(io.StringIO(cleaned_content), delimiter=known_delimiter)
                print(f"Using specified delimiter '{known_delimiter}' for {source_type}.")
            else: # Try to sniff
                try:
                    sample_for_sniffing = "\n".join(cleaned_content.splitlines()[:20])
                    if not sample_for_sniffing.strip(): sample_for_sniffing = cleaned_content
                    if len(sample_for_sniffing.strip()) <=1 and '\n' not in sample_for_sniffing and cleaned_content.count(cleaned_content.splitlines()[0] if cleaned_content.splitlines() else "") <=1 :
                         raise csv.Error("Sample too small or uniform to sniff accurately, trying defaults.")
                    dialect = csv.Sniffer().sniff(sample_for_sniffing)
                    reader_obj = csv.DictReader(io.StringIO(cleaned_content), dialect=dialect)
                    print(f"Sniffed delimiter '{dialect.delimiter}' for {source_type}.")
                    temp_io_check = io.StringIO(cleaned_content)
                    peek_reader = csv.DictReader(temp_io_check, dialect=dialect)
                    first_row_peek_check = next(peek_reader, None)
                    del peek_reader; del temp_io_check
                    first_raw_line = cleaned_content.splitlines()[0] if cleaned_content.splitlines() else ""
                    if first_row_peek_check and len(first_row_peek_check.keys()) < 2 and \
                       (first_raw_line.count(',') > len(first_row_peek_check.keys()) or \
                        first_raw_line.count('\t') > len(first_row_peek_check.keys()) or \
                        first_raw_line.count(';') > len(first_row_peek_check.keys())):
                        print(f"Warning: Sniffed delimiter '{dialect.delimiter}' resulted in few fields. Attempting common fallbacks for {source_type}.")
                        reader_obj = None
                except csv.Error as e_sniff:
                    print(f"Warning: CSV Sniffer failed for {source_type} ({e_sniff}). Trying common delimiters.")
                if not reader_obj:
                    for delim_try in [',', '\t', ';']:
                        try:
                            temp_io = io.StringIO(cleaned_content)
                            temp_reader = csv.DictReader(temp_io, delimiter=delim_try)
                            first_row_check = next(temp_reader, None)
                            del temp_reader; del temp_io
                            if first_row_check and len(first_row_check.keys()) > 1:
                                print(f"Successfully prepared to read from {source_type} using '{delim_try}' delimiter.")
                                reader_obj = csv.DictReader(io.StringIO(cleaned_content), delimiter=delim_try)
                                break
                        except Exception: continue
                    if not reader_obj:
                        print(f"Warning: Could not confidently determine delimiter for {source_type}. Defaulting to comma for DictReader.")
                        reader_obj = csv.DictReader(io.StringIO(cleaned_content))
            if reader_obj: return list(reader_obj)
            else: print(f"Warning: Could not create a CSV reader for {source_type}."); return []
        else: print(f"Warning: No data source configured or found for {file_path or string_data_var_name}."); return []
    except FileNotFoundError: print(f"Error: CSV file not found at '{file_path}'."); return []
    except Exception as e: print(f"Error reading or parsing CSV data from {source_type}: {e}"); return []

def save_json_data(data, output_path, data_type_name):
    if not data: print(f"No data to save for {data_type_name}."); data_to_save = []
    else: data_to_save = sorted(data, key=lambda x: x.get("name", "Unnamed Item"))

    list_key_name = f"{data_type_name.lower().replace(' ', '_').replace('-', '_')}_list"
    wrapper_key_name = f"{data_type_name.lower().replace(' ', '_').replace('-', '_')}_data"

    # Special handling for errata in hazards schema
    if data_type_name.lower() == "hazards":
        final_output = {
            wrapper_key_name: {
                "description": f"Compilation of {data_type_name} for Star Wars SAGA Edition.",
                list_key_name: data_to_save,
                "errata_applied": [] # Add errata_applied field as per schema for hazards
            }
        }
    else:
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

def attempt_numeric_conversion(value_str, item_name_for_warning, field_name_for_warning, data_type_for_warning):
    original_value_for_warning = value_str
    if value_str is None or value_str == '': return None
    if isinstance(value_str, (int, float)): return value_str
    known_non_numeric = ['varies', 'none', 's', '∞', '?', '-', 'see text', 'see description', 'n/a']
    cleaned_value_for_check = clean_value(str(value_str)).lower() # Uses the corrected clean_value
    if cleaned_value_for_check in known_non_numeric:
        if cleaned_value_for_check == "-" and field_name_for_warning.lower().startswith("cost"): return None
        return None

    cleaned_str = str(value_str).replace(',', '')
    if cleaned_str.lower().endswith('x') and field_name_for_warning.lower() in ['cost', 'weight', 'cost_credits', 'weight_kg', 'cargo (tons)']:
        cleaned_str = cleaned_str[:-1].strip()
    if '/m' in cleaned_str.lower(): return value_str
    if ' or ' in cleaned_str: return value_str
    if '*' in cleaned_str: cleaned_str = cleaned_str.replace('*', '').strip()
    try:
        if '.' in cleaned_str: return float(cleaned_str)
        else: return int(cleaned_str)
    except ValueError:
        return None

# --- ITEM-SPECIFIC HELPER FUNCTIONS ---
def parse_damage_string(damage_str):
    if not damage_str: return None
    original_text = damage_str.strip()
    if not original_text or original_text.lower() == 'none': return None
    multiplier_match = re.search(r"x([25])", original_text)
    multiplier = None
    if multiplier_match:
        multiplier = int(multiplier_match.group(1))
        damage_str = original_text[:multiplier_match.start()].strip()
    else: damage_str = original_text
    if '/' in damage_str:
        parts = damage_str.split('/')
        if len(parts) == 2: return {"primary_damage": parse_damage_string(parts[0]), "secondary_damage": parse_damage_string(parts[1]), "text_original": original_text, "damage_multiplier": multiplier}
    match = re.fullmatch(r"(?:(\d*)d(\d+))?(?:\s*([+-])\s*(\d+))?|([+-]?\d+)(?!\s*d)", original_text, re.IGNORECASE)
    if match:
        dice_count_str, die_type_str, sign, bonus_val_str, simple_bonus_or_value_str = match.groups()
        parsed_damage = {"text_original": original_text, "dice_count": 0, "die_type": 0, "bonus_modifier": 0, "damage_multiplier": multiplier}
        if dice_count_str or die_type_str:
            parsed_damage["dice_count"] = int(dice_count_str) if dice_count_str else 1
            parsed_damage["die_type"] = int(die_type_str) if die_type_str else 0
            if bonus_val_str:
                bonus = int(bonus_val_str)
                if sign == '-': bonus *= -1
                parsed_damage["bonus_modifier"] = bonus
            return parsed_damage
        elif simple_bonus_or_value_str:
            try:
                parsed_damage["bonus_modifier"] = int(simple_bonus_or_value_str)
                return parsed_damage
            except ValueError:
                dice_only_match = re.fullmatch(r"d(\d+)", simple_bonus_or_value_str, re.IGNORECASE)
                if dice_only_match:
                    parsed_damage["dice_count"] = 1; parsed_damage["die_type"] = int(dice_only_match.group(1))
                    return parsed_damage
    return {"text_original": original_text, "notes": "Could not fully parse damage string.", "damage_multiplier": multiplier}

def parse_weapon_category_code(code_str, is_ranged=False):
    if not code_str: return "Unknown"
    code = code_str.strip().upper()
    if is_ranged: mapping = {'P': "Pistols", 'R': "Rifles", 'H': "Heavy Weapons", 'E': "Exotic Ranged Weapons", 'S': "Simple Ranged Weapons"}
    else: mapping = {'S': "Simple Melee Weapons", 'AM': "Advanced Melee Weapons", 'L': "Lightsabers", 'E': "Exotic Melee Weapons", 'U': "Unarmed"}
    return mapping.get(code, f"Unknown Code ({code})")

def parse_item_size_code(code_str):
    if not code_str: return "Medium"
    code = code_str.strip().upper()
    mapping = {'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge", 'G': "Gargantuan", 'C': "Colossal", 'D':"Diminutive", 'F':"Fine"}
    return mapping.get(code, code)

def parse_rate_of_fire(rof_str):
    if not rof_str: return []
    parts = [p.strip().upper() for p in rof_str.split(',')]
    rof_map = {'S': "Single", 'A': "Autofire"}
    return [rof_map.get(p, p) for p in parts if p]

def parse_armor_category_from_desc(desc_str, item_name="Unknown Item"):
    if not desc_str: return "Unknown"
    desc_lower = desc_str.lower()
    if "heavy armor" in desc_lower: return "Heavy Armor"
    if "medium armor" in desc_lower: return "Medium Armor"
    if "light armor" in desc_lower: return "Light Armor"
    if "shield" in desc_lower: return "Shield"
    first_line = desc_str.split('\n')[0].strip().lower()
    if "heavy armor" in first_line: return "Heavy Armor"
    if "medium armor" in first_line: return "Medium Armor"
    if "light armor" in first_line: return "Light Armor"
    name_lower = item_name.lower()
    if "shield" in name_lower and "energy shield" not in name_lower : return "Shield"
    if "energy shield" in name_lower: return "Energy Shield"
    return "Unknown Category"

def parse_item_effects(text_block):
    if not text_block: return []
    effects = []
    potential_properties = re.split(r';\s*', text_block)
    for prop in potential_properties:
        prop_cleaned = mtr_explanations(prop.strip())
        if prop_cleaned:
            bonus_match = re.search(r"\+([0-9]+)\s*(?:equipment|circumstance|species|feat|inherent|insight|morale|untyped)?\s*bonus\s*(?:to|on|against)\s*([\w\s]+?)(?: checks)?(?: against [\w\s]+)?$", prop_cleaned, re.IGNORECASE)
            if bonus_match:
                effects.append({"type": "bonus", "value": int(bonus_match.group(1)), "target": bonus_match.group(2).strip(), "description": prop_cleaned})
            elif re.search(r"DR\s*\d+", prop_cleaned, re.IGNORECASE):
                 dr_value_match = re.search(r"DR\s*(\d+)", prop_cleaned, re.IGNORECASE)
                 effects.append({"type": "damage_reduction", "value": int(dr_value_match.group(1)) if dr_value_match else "See description", "description": prop_cleaned})
            elif re.search(r"SR\s*\d+", prop_cleaned, re.IGNORECASE):
                 sr_value_match = re.search(r"SR\s*(\d+)", prop_cleaned, re.IGNORECASE)
                 effects.append({"type": "shield_rating", "value": int(sr_value_match.group(1)) if sr_value_match else "See description", "description": prop_cleaned})
            else: effects.append({"type": "narrative_property", "description": prop_cleaned})
    return effects if effects else [{"type": "narrative_property", "description": mtr_explanations(text_block)}]

def parse_accessory_type_code(code_str):
    if not code_str: return "Unknown"
    cleaned_code_str = clean_value(code_str).strip()
    full_type_mapping = { "TOOLS": "Tools", "MEDICAL GEAR": "Medical Gear", "SURVIVAL GEAR": "Survival Gear", "COMMUNICATIONS DEVICES": "Communications Devices", "DETECTION AND SURVEILLANCE DEVICES": "Detection and Surveillance Devices", "COMPUTERS AND STORAGE DEVICES": "Computers and Storage Devices", "WEAPON AND ARMOR ACCESSORIES": "Weapon and Armor Accessories", "LIFE SUPPORT": "Life Support", "CYBERNETICS": "Cybernetics", "IMPLANTS": "Implants", "ARTIFACTS": "Artifacts", "BIOTECH": "Biotech"}
    if cleaned_code_str.upper() in full_type_mapping: return full_type_mapping[cleaned_code_str.upper()]
    code_upper = cleaned_code_str.upper()
    mapping = {'A': "Armor Upgrade", 'R': "Weapon Upgrade (Ranged)", 'M': "Weapon Upgrade (Melee)", 'L': "Lightsaber Upgrade", 'ANY': "Universal Upgrade", '*': "Cybernetic Prosthesis Upgrade"}
    return mapping.get(code_upper, f"General ({code_str})" if code_str else "Unknown")

def parse_damage_types_string(dmg_type_str):
    if not dmg_type_str: return ["Untyped"]
    normalized = re.sub(r'\s+and\s+', '|', dmg_type_str, flags=re.IGNORECASE)
    normalized = normalized.replace('/', '|').replace(',', '|')
    types = [dt.strip().title() for dt in normalized.split('|') if dt.strip()]
    final_types = []
    for t in types:
        if "Bludgeoning And Energy" == t or "Energy And Bludgeoning" == t: final_types.extend(["Bludgeoning", "Energy"])
        elif "Piercing And Energy" == t or "Energy And Piercing" == t: final_types.extend(["Piercing", "Energy"])
        elif "Slashing And Energy" == t or "Energy And Slashing" == t: final_types.extend(["Slashing", "Energy"])
        elif "Slashing Or Piercing" == t or "Piercing Or Slashing" == t: final_types.extend(["Slashing", "Piercing"])
        else: final_types.append(t)
    return sorted(list(set(final_types))) if final_types else ["Untyped"]

def generate_id_from_name(name, prefix="item"):
    name_part = re.sub(r'[^a-z0-9_]', '', name.lower().replace(' ', '_').replace('/', '_'))
    return f"{prefix}_{name_part}"

def parse_area_of_effect(burst_text):
    if not burst_text: return {"text_original": None}
    text_original = clean_value(burst_text); shape = None; value_squares = None
    unit = "squares"
    if "cone" in text_original.lower(): shape = "cone"
    elif "burst" in text_original.lower(): shape = "burst"
    elif "radius" in text_original.lower(): shape = "radius"
    elif "line" in text_original.lower(): shape = "line"
    match = re.search(r"(\d+)\s*(?:sq|square)", text_original, re.IGNORECASE)
    if match: value_squares = int(match.group(1))
    if value_squares is not None and shape is None:
        if "sq" in text_original: shape = "burst"
    return {"text_original": text_original, "shape": shape, "value_squares": value_squares, "unit": unit if value_squares is not None else None}

def parse_cost_object(cost_str_single, item_name, data_type_name):
    options = []; text_original_cleaned = clean_value(cost_str_single)
    if text_original_cleaned:
        val = attempt_numeric_conversion(text_original_cleaned, item_name, "Cost", data_type_name)
        options.append({
            "type": "fixed_amount" if isinstance(val, (int, float)) else "text_description",
            "value": val if isinstance(val, (int, float)) else text_original_cleaned,
            "description": "Standard",
            "unit_type": "credit" if isinstance(val, (int, float)) else None
        })
    return {
        "text_original": text_original_cleaned or "Not specified",
        "options": options if options else [{"type": "text_description", "value": "Not specified"}],
        "selection_logic": None,
        "notes": None
    }

# --- Helper function for Droid System/Hazard Value Object ---
def _parse_value_object(value_str, item_name_for_warning, field_name_for_warning, data_type_for_warning="Item"):
    if value_str is None or value_str == '':
        return {"base_value": None, "factor_multiplier": None, "factor_basis": None, "text_override": None}

    cleaned_val_str = clean_value(str(value_str)) # Uses the corrected clean_value
    numeric_val = attempt_numeric_conversion(cleaned_val_str, item_name_for_warning, field_name_for_warning, data_type_for_warning)

    if numeric_val is not None:
        return {"base_value": numeric_val, "factor_multiplier": None, "factor_basis": None, "text_override": None}
    else:
        # If not numeric, check for common textual overrides or store the original cleaned string
        if cleaned_val_str.lower() in ["varies", "see text", "see description", "n/a", "-"] or "see " in cleaned_val_str.lower():
            return {"base_value": None, "factor_multiplier": None, "factor_basis": None, "text_override": cleaned_val_str}
        else:
            # If it's a string but not a clear directive, store it as base_value (schema allows string)
            return {"base_value": cleaned_val_str, "factor_multiplier": None, "factor_basis": None, "text_override": None}

# --- Hazard Specific Helper Functions ---
def _parse_hazard_damage_effect(damage_str_full, is_miss_effect_text=False):
    if not damage_str_full or damage_str_full.lower() == 'none':
        return {"damage_dice_text": None, "damage_types": [], "additional_effects_text": None}

    damage_str = damage_str_full.strip()
    dice_text = None
    damage_types = []
    additional_effects_parts = []

    dice_pattern = r"(\b\d*d\d+(?:[xX]\d+)?(?:[+-]\d+)?\b|\b[xX]\d+\b)"
    dice_match = re.search(dice_pattern, damage_str)

    if dice_match:
        dice_text = dice_match.group(1)
        temp_damage_str = damage_str.replace(dice_text, "", 1).strip()
    else:
        temp_damage_str = damage_str

    type_pattern = r"\(([^)]+)\)"
    type_match_list = re.findall(type_pattern, temp_damage_str) # Find all type groups
    
    temp_str_for_effects = temp_damage_str
    if type_match_list:
        for types_content in type_match_list:
            # Split types within parentheses by comma, semicolon, or slash
            current_types = [t.strip().lower() for t in re.split(r'[,;/]\s*', types_content) if t.strip()]
            damage_types.extend(current_types)
            # Remove the processed type group for effect parsing
            temp_str_for_effects = temp_str_for_effects.replace(f"({types_content})", "", 1).strip()
    
    if not damage_types and damage_str_full:
        common_types = ["acid", "fire", "cold", "electricity", "energy", "sonic", "bludgeoning", "piercing", "slashing", "untyped", "poison"]
        for ct in common_types:
            # Check for standalone type words, trying to avoid parts of other words
            if re.search(r'\b' + re.escape(ct) + r'\b', damage_str_full, re.IGNORECASE):
                 if ct not in damage_types: damage_types.append(ct)

    if temp_str_for_effects: # What's left after dice and (types)
        # Split remaining by common delimiters like ' and ', '; ', but be careful not to oversplit
        # For now, let's treat the remainder as a single block, can be refined.
        # Remove "and" if it's just joining two effect phrases
        cleaned_effect_remainder = re.sub(r"^\s*and\s*", "", temp_str_for_effects, flags=re.IGNORECASE).strip()
        if cleaned_effect_remainder:
            additional_effects_parts.append(cleaned_effect_remainder)


    ct_pattern = r"(target moves\s*([+-]?\d+)\s*(?:persistent)?\s*step(?:s)?\s*on(?: the)?\s*(?:ct|condition track)|(?:[+-]?\d+)\s*(?:persistent)?\s*step(?:s)?\s*on\s*ct|(?<!no )ct movement)"
    ct_match = re.search(ct_pattern, damage_str_full, re.IGNORECASE)
    if ct_match:
        ct_effect_text = ct_match.group(0).strip()
        # Avoid duplicating if already captured in general effects
        current_additional_text = " ".join(additional_effects_parts)
        if ct_effect_text.lower() not in current_additional_text.lower():
             additional_effects_parts.append(ct_effect_text)
        if "condition_track_penalty" not in damage_types and "no ct movement" not in ct_effect_text.lower() :
            damage_types.append("condition_track_penalty")
    
    if not dice_text and (damage_types or additional_effects_parts):
        if is_miss_effect_text and not damage_str_full.strip().lower().startswith("see effects"):
            dice_text = "See effects"
        elif not (damage_str_full.lower().startswith("1/2") or damage_str_full.lower().startswith("half")):
             dice_text = "Varies"
    elif not dice_text and not damage_types and not additional_effects_parts and damage_str_full:
        dice_text = damage_str_full

    if is_miss_effect_text and (damage_str_full.lower().startswith("1/2") or damage_str_full.lower().startswith("half")):
        if not dice_text or dice_text in ["See effects", "Varies"]: dice_text = damage_str_full.strip()

    final_additional_effects = "; ".join(filter(None, additional_effects_parts)) if additional_effects_parts else None
    # If dice_text itself contains "and" and effects, separate them if additional_effects is empty
    if dice_text and " and " in dice_text and not final_additional_effects:
        potential_dice_split = dice_text.split(" and ", 1)
        # Check if the first part looks like dice
        if re.match(dice_pattern, potential_dice_split[0]):
            dice_text = potential_dice_split[0]
            final_additional_effects = potential_dice_split[1]
        # else keep dice_text as is

    return {
        "damage_dice_text": dice_text.strip() if dice_text else None,
        "damage_types": sorted(list(set(t for t in damage_types if t))),
        "additional_effects_text": final_additional_effects.strip() if final_additional_effects else None
    }

def _parse_hazard_skill_interaction(skill_str): # Updated version
    if not skill_str or skill_str.lower() == 'none':
        return None

    skill_name_val = "Unknown"
    dc_val = None
    effect_description_val = skill_str
    notes_val = None
    
    # Regex: Skill Name potentially with (details) (DC XX or DC varies [; notes]): Effect
    match = re.match(r"([\w\s\(\/\).-]+?)\s*(?:\(\s*DC\s*([\w\s\d]+)\s*(?:;\s*([^)]+))?\s*\))?:\s*(.+)", skill_str.strip(), re.IGNORECASE)
    
    if match:
        skill_name_val = match.group(1).strip()
        dc_text = match.group(2)
        notes_from_dc_paren = match.group(3).strip() if match.group(3) else None
        effect_description_val = match.group(4).strip()

        if dc_text:
            if dc_text.isdigit():
                dc_val = int(dc_text)
            else: 
                dc_val = None 
                note_prefix = f"DC {dc_text}"
                if notes_from_dc_paren:
                    notes_val = f"{note_prefix}; {notes_from_dc_paren}"
                else:
                    notes_val = note_prefix
        
        if notes_from_dc_paren and not notes_val:
            notes_val = notes_from_dc_paren
    else:
        # Fallback for "Skill: Effect" if no DC part at all or primary regex fails
        fallback_match = re.match(r"([\w\s\(\/\).-]+?):\s*(.+)", skill_str.strip(), re.IGNORECASE)
        if fallback_match:
            skill_name_val = fallback_match.group(1).strip()
            effect_description_val = fallback_match.group(2).strip()
        else:
            print(f"Warning (Hazard Skill): Could not fully parse skill interaction: '{skill_str}'")
            # Return raw string as effect if no pattern matches
            return {"skill_name": "Unknown", "dc": None, "effect_description": skill_str, "notes": "Requires manual review"}

    return {
        "skill_name": skill_name_val,
        "dc": dc_val,
        "effect_description": effect_description_val,
        "notes": notes_val
    }

# --- 3. PROCESSING FUNCTIONS ---
# (Placeholders for functions you've already developed and tested)
def process_armor_csv(): print("Skipping Armor processing.")
def process_melee_weapons_csv(): print("Skipping Melee Weapons processing.")
def process_ranged_weapons_csv(): print("Skipping Ranged Weapons processing.")
def process_accessories_csv(): print("Skipping Accessories processing.")
def process_defensive_items_csv(): print("Skipping Defensive Items processing.")
def process_equipment_general_csv(): print("Skipping General Equipment processing.")
def process_vehicles_csv(): print("Skipping Vehicles processing.")
def process_starships_csv(): print("Skipping Starships processing.")
def process_explosives_csv(): print("Skipping Explosives processing.")

def process_droid_systems_csv():
    print("Processing Droid Systems...")
    raw_data = read_csv_data(DROID_SYSTEMS_CSV_PATH)
    processed_systems = []

    if not raw_data:
        save_json_data(processed_systems, DROID_SYSTEMS_JSON_PATH, "Droid Systems")
        return

    valid_groups = [
        "Locomotion System", "Processor System", "Appendage", "Sensor System",
        "Communications System", "Weapon System", "Armor Plating", "Tool",
        "Integrated Equipment", "Accessory", "Droid Trait Modifier",
        "General Upgrade", "Defensive System"
    ]

    for row_idx, row_dict_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k, v in row_dict_raw.items()}
        name = row.get('DROID SYSTEM', '')
        book = row.get('BOOK', '')
        page_str = str(row.get('PAGE', ''))
        group = row.get('GROUP', '')

        if not name or not book or not page_str or not group:
            print(f"Warning (Droid Systems): Skipping row {row_idx + 2} due to missing Name, Book, Page, or Group.")
            continue

        if group not in valid_groups:
            mapped_group = group
            if group.lower() == "armor": mapped_group = "Armor Plating"
            elif group.lower() == "communications": mapped_group = "Communications System"
            if mapped_group in valid_groups: group = mapped_group
            else: print(f"Warning (Droid Systems): Invalid GROUP '{group}' for item '{name}'. Storing as is.")

        id_base = f"{name}_{book}_{page_str}".lower()
        id_base = re.sub(r'[^a-z0-9_]+', '_', id_base)
        system_id = re.sub(r'_+', '_', id_base).strip('_')

        system_obj = {
            "id": system_id, "name": name,
            "primary_source": {"source_book": book, "page": page_str, "reference_type": "primary_definition", "notes": None},
            "description_text": row.get('Desc.', None), "group": group,
            "cost_details": _parse_value_object(row.get('COST'), name, 'COST', 'Droid System'),
            "weight_details": _parse_value_object(row.get('WEIGHT'), name, 'WEIGHT', 'Droid System'),
            "availability_text": row.get('AVAIL.', None),
            "benefits_and_comments": row.get('COMMENTS & BENEFITS', None),
            "detailed_rules_and_effects": None, "system_type_tags": [], "prerequisites_text": None,
            "installation_dc_mechanics": None, "installation_time_text": None,
            "slots_required": None, "power_consumption_notes": None, "image_url": None,
            "additional_source_references": []
        }
        processed_systems.append(system_obj)
    save_json_data(processed_systems, DROID_SYSTEMS_JSON_PATH, "Droid Systems")

def process_hazards_csv():
    print("Processing Hazards...")
    raw_data = read_csv_data(HAZARDS_CSV_PATH)
    processed_hazards = []

    if not raw_data:
        save_json_data(processed_hazards, HAZARDS_JSON_PATH, "Hazards")
        return

    for row_idx, row_dict_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k, v in row_dict_raw.items()} # Clean values once

        name = row.get('HAZARD', '')
        book = row.get('BOOK', '')
        page_str = str(row.get('PAGE', ''))

        if not name or not book or not page_str:
            print(f"Warning (Hazards): Skipping row {row_idx + 2} due to missing Name, Book, or Page.")
            continue

        id_base = f"{name}_{book}_{page_str}".lower()
        id_base = re.sub(r'[^a-z0-9_]+', '_', id_base)
        hazard_id = re.sub(r'_+', '_', id_base).strip('_')

        hazard_type_tags = [tag.strip() for tag in row.get('Type', '').split(';') if tag.strip()]
        typical_locations = [loc.strip() for loc in row.get('Location', '').split(',') if loc.strip() and loc.strip().lower() != 'none']

        damage_full_str = row.get('Damage (type; failure)', '')
        hit_part_str = damage_full_str
        miss_part_str = None

        # Updated splitting logic for damage string
        split_keywords = ["; 1/2", "; half"] 
        found_split_kw = False
        for kw in split_keywords:
            # Find case-insensitive keyword
            kw_match_idx = -1
            try:
                kw_match_idx = damage_full_str.lower().rfind(kw) # search from right
            except AttributeError: # if damage_full_str is not a string (e.g. None)
                pass

            if kw_match_idx != -1:
                 # Ensure it's a logical split point (not at the very beginning, and possibly preceded by space/paren)
                if kw_match_idx > 0 and (damage_full_str[kw_match_idx-1].isspace() or damage_full_str[kw_match_idx-1] == ')' or damage_full_str[kw_match_idx-1].isalnum()):
                    hit_part_str = damage_full_str[:kw_match_idx].strip()
                    # Get the original casing for the keyword part
                    miss_part_str = damage_full_str[kw_match_idx:].replace(";", "", 1).strip()
                    found_split_kw = True
                    break
        if not found_split_kw and ";" in damage_full_str:
            # More careful split on semicolon, ensuring it's not inside parentheses
            # This regex finds the first semicolon NOT inside parentheses
            match_semicolon_split = re.match(r"([^(;]*?(?:\([^)]*\)[^(;]*?)*?);(.*)", damage_full_str)
            if match_semicolon_split:
                hit_part_str = match_semicolon_split.group(1).strip()
                miss_part_str = match_semicolon_split.group(2).strip()
            # else: hit_part_str remains damage_full_str, miss_part_str remains None

        damage_on_hit_data = _parse_hazard_damage_effect(hit_part_str)
        damage_on_miss_data = _parse_hazard_damage_effect(miss_part_str, is_miss_effect_text=True) if miss_part_str else \
                              {"damage_dice_text": None, "damage_types": [], "additional_effects_text": None}

        skill_interactions = []
        for skill_col_key in ['Skill 1', 'Skill 2', 'Skill 3']:
            skill_detail_str = row.get(skill_col_key, '')
            if skill_detail_str and skill_detail_str.lower() not in ['none', 'n/a', '']:
                parsed_interaction = _parse_hazard_skill_interaction(skill_detail_str)
                if parsed_interaction:
                    skill_interactions.append(parsed_interaction)
        
        defense_targeted_raw = row.get('Defense') # Already cleaned by row = {...}
        valid_defenses_map = {"reflex": "Reflex", "fortitude": "Fortitude", "will": "Will", "ref": "Reflex", "fort": "Fortitude"}
        defense_targeted = None
        if defense_targeted_raw:
            defense_targeted_lower = defense_targeted_raw.lower()
            if defense_targeted_lower in valid_defenses_map:
                defense_targeted = valid_defenses_map[defense_targeted_lower]
            elif "/" in defense_targeted_raw:
                print(f"Warning (Hazards): Defense '{defense_targeted_raw}' for '{name}' has multiple types. Setting to null. CSV: '{row_dict_raw.get('Defense')}'.")
            elif defense_targeted_lower not in ['none', 'n/a', '']:
                print(f"Warning (Hazards): Unrecognized Defense '{defense_targeted_raw}' for '{name}'. Setting to null. CSV: '{row_dict_raw.get('Defense')}'.")

        hazard_obj = {
            "id": hazard_id, "name": name,
            "primary_source": {"source_book": book, "page": page_str, "reference_type": "primary_definition", "notes": None},
            "hazard_type_tags": hazard_type_tags,
            "typical_locations": typical_locations if typical_locations else None,
            "cl": attempt_numeric_conversion(row.get('CL'), name, 'CL', 'Hazard'),
            "trigger_description": row.get('Trigger') or None,
            "attack_details": {"bonus_text": row.get('Attack') or None, "defense_targeted": defense_targeted, "notes": None},
            "damage_on_hit": damage_on_hit_data,
            "damage_on_miss_or_save": damage_on_miss_data,
            "recurrence_description": row.get('Recurrence') or None,
            "special_qualities_and_rules": row.get('Special') or None,
            "skill_interactions": skill_interactions if skill_interactions else None,
            "full_text_description_from_book": None,
            "cost_details": _parse_value_object(row.get('COST'), name, 'COST', 'Hazard'), # COST might not be typical for hazards
            "weight_details": _parse_value_object(row.get('WEIGHT'), name, 'WEIGHT', 'Hazard'), # WEIGHT might not be typical
            "availability_text": row.get('AVAIL.') or None, # AVAIL. might not be typical
            "additional_source_references": []
        }
        processed_hazards.append(hazard_obj)
    save_json_data(processed_hazards, HAZARDS_JSON_PATH, "Hazards")

# --- 4. MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting SAGA Index Elements CSV to JSON Conversion Process...\n")
    if PROCESS_CONFIG.get("armor", False): process_armor_csv()
    if PROCESS_CONFIG.get("melee_weapons", False): process_melee_weapons_csv()
    if PROCESS_CONFIG.get("ranged_weapons", False): process_ranged_weapons_csv()
    if PROCESS_CONFIG.get("accessories", False): process_accessories_csv()
    if PROCESS_CONFIG.get("defensive_items", False): process_defensive_items_csv()
    if PROCESS_CONFIG.get("equipment_general", False): process_equipment_general_csv()
    if PROCESS_CONFIG.get("vehicles", False): process_vehicles_csv()
    if PROCESS_CONFIG.get("starships", False): process_starships_csv()
    if PROCESS_CONFIG.get("explosives", False): process_explosives_csv()
    if PROCESS_CONFIG.get("droid_systems", False): process_droid_systems_csv()
    if PROCESS_CONFIG.get("hazards", False): process_hazards_csv()

    print("\nConfigured item/index element CSV processing complete.")