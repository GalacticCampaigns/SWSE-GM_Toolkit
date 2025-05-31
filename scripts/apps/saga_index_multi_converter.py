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
DEFENSES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Defenses.csv')
EQUIPMENT_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Equipment.csv')
VEHICLES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Vehicles.csv')
STARSHIPS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Starships.csv')
EXPLOSIVES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Explosives.csv')
TECHSPEC_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-TechSpec.csv')
TEMPLATES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Templates.csv')
DROID_SYSTEMS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Droid Systems.csv') # Added Droid Systems CSV Path

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
DROID_SYSTEMS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\droid_systems.json') # Added Droid Systems JSON Path


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
    "droid_systems": True, # Added Droid Systems
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

def mtr_explanations(text): # From saga_index_multi_converter.py
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

def read_csv_data(file_path, string_data_var_name=None, known_delimiter=None, use_direct_reader=False): # From saga_index_multi_converter.py
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
            else:
                try:
                    sample_for_sniffing = "\n".join(cleaned_content.splitlines()[:20])
                    if not sample_for_sniffing: sample_for_sniffing = cleaned_content
                    if len(sample_for_sniffing.strip()) <= 1 and '\n' not in sample_for_sniffing:
                         raise csv.Error("Sample too small to sniff after cleaning, trying defaults.")
                    dialect = csv.Sniffer().sniff(sample_for_sniffing)
                    reader_obj = csv.DictReader(io.StringIO(cleaned_content), dialect=dialect)
                    print(f"Sniffed delimiter '{dialect.delimiter}' for {source_type}.")
                    temp_io_check = io.StringIO(cleaned_content)
                    peek_reader = csv.DictReader(temp_io_check, dialect=dialect)
                    first_row_peek_check = next(peek_reader, None)
                    del peek_reader; del temp_io_check
                    first_raw_line = cleaned_content.splitlines()[0] if cleaned_content.splitlines() else ""
                    if first_row_peek_check and len(first_row_peek_check.keys()) < 3 and \
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
                            if first_row_check and len(first_row_check.keys()) > 2:
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


def save_json_data(data, output_path, data_type_name): # From saga_index_multi_converter.py
    if not data: print(f"No data to save for {data_type_name}."); data_to_save = []
    else: data_to_save = sorted(data, key=lambda x: x.get("name", "Unnamed Item")) # Default for items

    list_key_name = f"{data_type_name.lower().replace(' ', '_').replace('-', '_')}_list"
    wrapper_key_name = f"{data_type_name.lower().replace(' ', '_').replace('-', '_')}_data"

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

def attempt_numeric_conversion(value_str, item_name_for_warning, field_name_for_warning, data_type_for_warning): # From saga_index_multi_converter.py
    original_value_for_warning = value_str
    if value_str is None or value_str == '': return None
    if isinstance(value_str, (int, float)): return value_str
    known_non_numeric = ['varies', 'none', 's', '∞', '?', '-', 'see text', 'see description', 'n/a', '']
    cleaned_value_for_check = clean_value(str(value_str)).lower()
    if cleaned_value_for_check in known_non_numeric:
        if cleaned_value_for_check == "-" and field_name_for_warning.lower().startswith("cost"): return None
        return None # Treat other known non-numerics as not a number for conversion purposes

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
# (parse_damage_string, parse_weapon_category_code, etc. ... these are from the original saga_index_multi_converter.py)
# ... (Assuming all existing helpers from saga_index_multi_converter.py are here)
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
    if not code_str: return "Medium" # Default for items
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

def parse_item_effects(text_block): # This is a key helper from index script
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

def parse_cost_object(cost_str_single, item_name, data_type_name): # Simplified for single cost string
    options = []; text_original_cleaned = clean_value(cost_str_single)
    if text_original_cleaned:
        val = attempt_numeric_conversion(text_original_cleaned, item_name, "Cost", data_type_name)
        options.append({
            "type": "fixed_amount" if isinstance(val, (int, float)) else "text_description",
            "value": val if isinstance(val, (int, float)) else text_original_cleaned,
            "description": "Standard", # Default description
            "unit_type": "credit" if isinstance(val, (int, float)) else None
        })
    return {
        "text_original": text_original_cleaned or "Not specified",
        "options": options if options else [{"type": "text_description", "value": "Not specified"}],
        "selection_logic": None,
        "notes": None
    }

# --- Helper function for Droid System Value Object (Moved here) ---
def _parse_value_object(value_str, item_name_for_warning, field_name_for_warning, data_type_for_warning="Droid System"):
    if value_str is None or value_str == '':
        return {"base_value": None, "factor_multiplier": None, "factor_basis": None, "text_override": None}

    cleaned_val_str = clean_value(str(value_str)) # Ensure it's cleaned

    numeric_val = attempt_numeric_conversion(cleaned_val_str, item_name_for_warning, field_name_for_warning, data_type_for_warning)

    if numeric_val is not None:
        return {"base_value": numeric_val, "factor_multiplier": None, "factor_basis": None, "text_override": None}
    else:
        if cleaned_val_str.lower() in ["varies", "see text", "see description", "n/a", "-"] or "see " in cleaned_val_str.lower():
            return {"base_value": None, "factor_multiplier": None, "factor_basis": None, "text_override": cleaned_val_str}
        else:
            return {"base_value": cleaned_val_str, "factor_multiplier": None, "factor_basis": None, "text_override": None}

# --- 3. PROCESSING FUNCTIONS ---
# ... (Existing Armor, Weapons, Accessories, etc. processing functions)
def process_armor_csv():
    print("Processing Armor...")
    raw_data = read_csv_data(ARMOR_CSV_PATH)
    processed_armor_list = []
    if not raw_data: save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor"); return
    for idx, row_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('ITEM', '')
        book = row.get('BOOK', '')
        page = row.get('PAGE', '')
        if not name or not book or not page or len(name) > 60 or "see page" in name.lower() or name.startswith(','): continue
        desc_text = row.get('Desc.', ''); armor_cat = parse_armor_category_from_desc(desc_text, name)
        comments_text = row.get('COMMENTS', ''); parsed_props = parse_item_effects(comments_text) if comments_text else []
        spd_6sq = row.get('Spd 6sq', ''); spd_4sq = row.get('Spd 4sq', '')
        speed_penalty_text = []
        if spd_6sq: speed_penalty_text.append(f"6sq Base: {spd_6sq}")
        if spd_4sq: speed_penalty_text.append(f"4sq Base: {spd_4sq}")
        helmet_p_val_raw = row.get('Helmet P.', ''); helmet_p_val_cleaned = clean_value(helmet_p_val_raw)
        armor_item = {"name": name, "full_text_description": desc_text or None, "armor_category": armor_cat,
                      "armor_check_penalty": attempt_numeric_conversion(row.get('ACP', ''), name, 'ACP', 'Armor'),
                      "cost_credits": attempt_numeric_conversion(row.get('Cost', ''), name, 'Cost', 'Armor'),
                      "reflex_defense_bonus": attempt_numeric_conversion(row.get('Ref bonus', ''), name, 'Ref bonus', 'Armor'),
                      "fortitude_defense_bonus": attempt_numeric_conversion(row.get('Fort bonus', ''), name, 'Fort bonus', 'Armor'),
                      "max_dex_bonus": attempt_numeric_conversion(row.get('Max Dex', ''), name, 'Max Dex', 'Armor'),
                      "speed_penalty_text": ", ".join(speed_penalty_text) if speed_penalty_text else None,
                      "weight_kg": attempt_numeric_conversion(row.get('Weight', ''), name, 'Weight', 'Armor'),
                      "availability": row.get('Avail.', ''), "upgrade_slots_text": row.get('U. Slots', '') or None,
                      "has_helmet_package": helmet_p_val_cleaned.lower() == 'x' if isinstance(helmet_p_val_cleaned, str) else False,
                      "special_properties_text": comments_text or None, "parsed_properties": parsed_props,
                      "skill_bonuses_text": f"Skill: {row.get('Skill','N/A')}, Bonus: {row.get('Skillbonus','N/A')}" if row.get('Skill') else None,
                      "ability_bonuses_text": f"Ability: {row.get('Ability','N/A')}, Bonus: {row.get('Abilitybonus','N/A')}" if row.get('Ability') else None,
                      "used_by_text": row.get('Used By', '') or None, "source_book": book, "page": str(page)}
        processed_armor_list.append(armor_item)
    save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor")

def process_melee_weapons_csv():
    print("Processing Melee Weapons...")
    raw_data = read_csv_data(MELEE_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons"); return
    for idx, row_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('WEAPON', '')
        if not name or not row.get('BOOK', '') or not row.get('PAGE', '') or len(name) > 60 or "see page" in name.lower() or name.startswith(','): continue
        proficiency_code = row.get('Wpn Type', '')
        damage_type_raw_text = row.get('Dmg Type', ''); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        damage_text = row.get(' Damage', row.get('Damage',''))
        stun_text = row.get('Stun', '')
        comments_text = row.get('COMMENTS', ''); parsed_props = parse_item_effects(comments_text) if comments_text else []
        weapon = {"name": name, "full_text_description": row.get('Desc.', '') or None,
                  "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=False),
                  "size_category": parse_item_size_code(row.get('Size', '')),
                  "cost_credits": attempt_numeric_conversion(row.get('Cost',''), name, 'Cost', 'Melee'),
                  "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text),
                  "stun_damage_text": stun_text or None, "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None,
                  "weight_kg": attempt_numeric_conversion(row.get('Weight',''), name, 'Weight', 'Melee'),
                  "damage_types": damage_types_list, "availability": row.get('Avail.', ''),
                  "reach_or_thrown_info": row.get('Thrown / Reach', '') or None,
                  "extra_cost_note": row.get(' Extra cost', row.get('Extra cost','')) or None,
                  "build_dc_note": row.get(' Build DC', row.get('Build DC','')) or None,
                  "special_properties_text": comments_text or None, "parsed_properties": parsed_props,
                  "used_by_text": row.get('Used by', '') or None, "source_book": row.get('BOOK', ''), "page": str(row.get('PAGE', ''))}
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons")

def process_ranged_weapons_csv():
    print("Processing Ranged Weapons...")
    raw_data = read_csv_data(RANGED_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons"); return
    for idx, row_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('WEAPON', '')
        if not name or not row.get('BOOK', '') or not row.get('PAGE', '') or len(name) > 70 or "see page" in name.lower() or name.startswith(','):
            continue
        proficiency_code = row.get('Wpn Type', '')
        damage_type_raw_text = row.get('Dmg Type', ''); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        damage_text = row.get(' Damage', row.get('Damage','')); stun_text = row.get('Stun', '')
        comments_text = row.get('COMMENTS', ''); parsed_props = parse_item_effects(comments_text) if comments_text else []
        classification_tags = []
        if row.get("Pistol", row.get("Pistol\nRifle", '')): classification_tags.append("Pistol")
        if row.get("Rifle", row.get("Pistol\nRifle", '')):
             if "rifle" in str(row.get("Pistol\nRifle", "")).lower() : classification_tags.append("Rifle")
        if row.get("Heavy", row.get("Heavy\nExotic", '')): classification_tags.append("Heavy Weapon")
        if row.get("Exotic", row.get("Heavy\nExotic", '')):
            if "exotic" in str(row.get("Heavy\nExotic", "")).lower() : classification_tags.append("Exotic Weapon")
        if row.get("Simple", '' ): classification_tags.append("Simple Weapon")
        if row.get("Accurate", row.get("Accurate\nInaccurate", '')): classification_tags.append("Accurate")
        if row.get("Inaccurate", row.get("Accurate\nInaccurate", '')):
             if "inaccurate" in str(row.get("Accurate\nInaccurate", "")).lower(): classification_tags.append("Inaccurate")
        classification_tags = sorted(list(set(t for t in classification_tags if t)))
        weapon = {"name": name, "full_text_description": row.get('Desc.', '') or None,
                  "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=True),
                  "size_category": parse_item_size_code(row.get('Size', '')),
                  "cost_credits": attempt_numeric_conversion(row.get('Cost',''), name, 'Cost', 'Ranged'),
                  "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text),
                  "stun_damage_text": stun_text or None, "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None,
                  "rate_of_fire_text": row.get('Fire Rate', ''), "rate_of_fire_structured": parse_rate_of_fire(row.get('Fire Rate', '')),
                  "weight_kg": attempt_numeric_conversion(row.get('Weight',''), name, 'Weight', 'Ranged'),
                  "damage_types": damage_types_list, "availability": row.get('Avail.', ''),
                  "area_effect_text": row.get('Area', '') or None,
                  "ammunition_shots": attempt_numeric_conversion(row.get('Shots',''), name, 'Shots', 'Ranged'),
                  "ammunition_cost_text": row.get(' Ammo Cost', row.get('Ammo Cost','')) or None,
                  "accuracy_note": row.get(' Accuracy', row.get('Accuracy','')) or None,
                  "special_properties_text": comments_text or None, "parsed_properties": parsed_props,
                  "classification_tags": classification_tags, "used_by_text": row.get('Used By', '') or None,
                  "source_book": row.get('BOOK', ''), "page": str(row.get('PAGE', ''))}
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons")

def process_accessories_csv():
    print("Processing Accessories...")
    raw_data = read_csv_data(ACCESSORIES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('ACCESSORIES', '')
        if not name or not row.get('BOOK', '') or not row.get('PAGE', '') or len(name) > 70: continue
        desc_text = row.get('Desc.', '')
        comments_text = row.get('COMMENTS', ''); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        weight_text = row.get('Weight', ''); weight_kg = None
        if weight_text:
            if "%" in weight_text: weight_kg = None
            else: weight_kg = attempt_numeric_conversion(weight_text, name, 'Weight', 'Accessory')
        item = {"name": name, "full_text_description": desc_text or None,
                "accessory_type_code": row.get('Type', ''),
                "accessory_type_description": parse_accessory_type_code(row.get('Type', '')),
                "upgrade_points_cost_text": row.get('U. Points', '') or None,
                "availability": row.get('Avail.', ''),
                "cost_credits": attempt_numeric_conversion(row.get('Cost', ''), name, 'Cost', 'Accessory'),
                "weight_text": weight_text or None, "weight_kg": weight_kg,
                "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects,
                "source_book": row.get('BOOK', ''), "page": str(row.get('PAGE', ''))}
        processed_items.append(item)
    save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories")

def process_defensive_items_csv():
    print("Processing Defensive Items (Mines, Emplacements)...")
    raw_data = read_csv_data(DEFENSES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items"); return
    for row_raw in raw_data:
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('WEAPON', '')
        if not name or not row.get('BOOK', '') or not row.get('PAGE', '') or len(name) > 50: continue
        damage_text = row.get('Damage', '')
        damage_type_raw_text = row.get('Type', ''); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        comments_text = row.get('COMMENTS', ''); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        delay_key = "Delay\n(rounds)" if "Delay\n(rounds)" in row_raw else "Delay" # Check raw for multi-line key
        item = {"name": name,
                "cost_credits": attempt_numeric_conversion(row.get('Cost', ''), name, 'Cost', 'Defensive Item'),
                "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text),
                "damage_types": damage_types_list,
                "weight_kg": attempt_numeric_conversion(row.get('Weight', ''), name, 'Weight', 'Defensive Item'),
                "perception_dc_to_detect": attempt_numeric_conversion(row.get('Perception', ''), name, 'Perception DC', 'Defensive Item'),
                "availability": row.get('Avail.', ''),
                "splash_radius_text": row.get('Splash', '') or None,
                "delay_rounds_text": row.get(delay_key, '') or None,
                "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects,
                "source_book": row.get('BOOK', ''), "page": str(row.get('PAGE', ''))}
        processed_items.append(item)
    save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items")

def process_equipment_general_csv():
    print("Processing General Equipment...")
    raw_data = read_csv_data(EQUIPMENT_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment"); return
    for idx, row_raw in enumerate(raw_data):
        row = {k: clean_value(v) for k,v in row_raw.items()}
        name = row.get('ITEM', '')
        book = row.get('BOOK', '')
        page = row.get('PAGE', '')
        if not name or not book or not page or len(name) > 70 or name.startswith(',') or \
           (book and (',' in book or len(book) > 5)) or \
           (page and not re.match(r"^\d+(-?\d*)?$", page) and page.lower() != 'various'):
            continue
        desc_text = row.get('Desc.', '')
        comments_text = row.get('COMMENTS', ''); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        item = {"name": name, "full_text_description": desc_text or None,
                "equipment_category_code": row.get('TYPE', ''),
                "equipment_category_description": parse_accessory_type_code(row.get('TYPE', '')), # Re-use for broad categories
                "cost_credits": attempt_numeric_conversion(row.get('Cost', ''), name, 'Cost', 'Equipment'),
                "weight_kg": attempt_numeric_conversion(row.get('Weight', ''), name, 'Weight', 'Equipment'),
                "uses_text": row.get('Uses', '') or None,
                "use_cost_text": row.get(' Use Cost', row.get('Use Cost', '')) or None,
                "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects,
                "source_book": book, "page": str(page)}
        processed_items.append(item)
    save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment")

# (Vehicle, Starship, Explosives processing functions from original saga_index_multi_converter.py would be here)
# ...
# Placeholder for Vehicles
def process_vehicles_csv(): print("Skipping Vehicles processing (placeholder).")
# Placeholder for Starships
def process_starships_csv(): print("Skipping Starships processing (placeholder).")
# Placeholder for Explosives
def process_explosives_csv(): print("Skipping Explosives processing (placeholder).")


def process_droid_systems_csv(): # Moved here
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
            # Allow if it's a known variant like "Armor" instead of "Armor Plating" but map it.
            if group == "Armor" and "Armor Plating" in valid_groups:
                group = "Armor Plating"
            elif group == "Communications" and "Communications System" in valid_groups:
                group = "Communications System"
            # Add other similar mappings if observed from data
            else:
                print(f"Warning (Droid Systems): Invalid GROUP '{group}' for item '{name}' in row {row_idx + 2}. CSV had '{row_dict_raw.get('GROUP', '')}'. Valid are: {valid_groups}. Storing as is.")


        id_base = f"{name}_{book}_{page_str}".lower()
        id_base = re.sub(r'[^a-z0-9_]+', '_', id_base)
        system_id = re.sub(r'_+', '_', id_base).strip('_')

        system_obj = {
            "id": system_id,
            "name": name,
            "primary_source": {
                "source_book": book,
                "page": page_str,
                "reference_type": "primary_definition",
                "notes": None
            },
            "description_text": row.get('Desc.', None),
            "group": group, # Store the (potentially mapped) group
            "cost_details": _parse_value_object(row.get('COST'), name, 'COST', 'Droid System'),
            "weight_details": _parse_value_object(row.get('WEIGHT'), name, 'WEIGHT', 'Droid System'),
            "availability_text": row.get('AVAIL.', None),
            "benefits_and_comments": row.get('COMMENTS & BENEFITS', None),
            # Consider using parse_item_effects for benefits_and_comments if its structure aligns
            # "parsed_effects": parse_item_effects(row.get('COMMENTS & BENEFITS', '')), # Alternative
            "detailed_rules_and_effects": None,
            "system_type_tags": [],
            "prerequisites_text": None,
            "installation_dc_mechanics": None,
            "installation_time_text": None,
            "slots_required": None,
            "power_consumption_notes": None,
            "image_url": None,
            "additional_source_references": []
        }
        processed_systems.append(system_obj)

    save_json_data(processed_systems, DROID_SYSTEMS_JSON_PATH, "Droid Systems")


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
    # if PROCESS_CONFIG.get("tech_specialist_upgrades", False): process_techspec_csv() # Placeholder
    # if PROCESS_CONFIG.get("templates", False): process_templates_csv() # Placeholder
    if PROCESS_CONFIG.get("droid_systems", False): process_droid_systems_csv() # Added call

    print("\nConfigured item/index element CSV processing complete.")