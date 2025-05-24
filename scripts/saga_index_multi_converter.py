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
TECHSPEC_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-TechSpec.csv')
TEMPLATES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Templates.csv')
EXPLOSIVES_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Explosives.csv')


# Output JSON Paths for Item Elements
ARMOR_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\armor.json')
MELEE_WEAPONS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\melee_weapons.json')
RANGED_WEAPONS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\ranged_weapons.json')
ACCESSORIES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\accessories.json')
DEFENSIVE_ITEMS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\defensive_items.json')
EQUIPMENT_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\equipment_general.json')
TECHSPEC_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\tech_specialist_upgrades.json')
TEMPLATES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\templates.json')
EXPLOSIVES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\explosives.json')


# --- SCRIPT EXECUTION CONFIGURATION ---
PROCESS_CONFIG = {
    "armor": True,
    "melee_weapons": True,
    "ranged_weapons": True,
    "accessories": True, 
    "defensive_items": True, 
    "equipment_general": True,
    "tech_specialist_upgrades": False, 
    "templates": False, 
    "explosives": False, 
}

# --- 2. GENERIC HELPER FUNCTIONS ---

def clean_value(value):
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

def read_csv_data(file_path, string_data_var_name=None, known_delimiter=None):
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
                    del peek_reader 
                    del temp_io_check

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
                            del temp_reader 
                            del temp_io
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


def save_json_data(data, output_path, data_type_name):
    if not data: print(f"No data to save for {data_type_name}."); data_to_save = []
    else: data_to_save = sorted(data, key=lambda x: x.get("name", ""))
    final_output = {f"{data_type_name.lower().replace(' ', '_')}_data": {"description": f"Compilation of {data_type_name} for Star Wars SAGA Edition.", f"{data_type_name.lower().replace(' ', '_')}_list": data_to_save}}
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
    known_non_numeric = ['varies', 'none', 's', '∞', '?', '-', 'see text', 'see description', 'n/a', '']
    cleaned_value_for_check = clean_value(str(value_str)).lower()
    if cleaned_value_for_check in known_non_numeric: return None
    cleaned_str = str(value_str).replace(',', '')
    if cleaned_str.lower().endswith('x') and field_name_for_warning.lower() in ['cost', 'weight', 'cost_credits', 'weight_kg']: 
        cleaned_str = cleaned_str[:-1].strip()
    if '/m' in cleaned_str.lower(): return value_str 
    if ' or ' in cleaned_str: return value_str 
    if '*' in cleaned_str: cleaned_str = cleaned_str.replace('*', '').strip()
    try:
        if '.' in cleaned_str: return float(cleaned_str)
        else: return int(cleaned_str)
    except ValueError:
        if len(str(original_value_for_warning)) < 50 : 
             print(f"Warning ({data_type_for_warning}): Could not convert '{field_name_for_warning}' to number for '{item_name_for_warning}'. Original CSV value: '{original_value_for_warning}'. Storing as None.")
        return None 

# --- ITEM-SPECIFIC HELPER FUNCTIONS ---
def parse_damage_string(damage_str):
    if not damage_str: return None
    original_text = damage_str.strip()
    if not original_text or original_text.lower() == 'none': return None
    if '/' in original_text:
        parts = original_text.split('/')
        if len(parts) == 2: return {"primary": parse_damage_string(parts[0]), "secondary": parse_damage_string(parts[1]), "text": original_text}
    match = re.fullmatch(r"(?:(\d*)d(\d+))?(?:\s*([+-])\s*(\d+))?|([+-]?\d+)", original_text, re.IGNORECASE)
    if match:
        dice_count_str, die_type_str, sign, bonus_val_str, simple_bonus_or_value_str = match.groups()
        parsed_damage = {"text": original_text, "dice_count": 0, "die_type": 0, "bonus": 0}
        if dice_count_str or die_type_str:
            parsed_damage["dice_count"] = int(dice_count_str) if dice_count_str else 1
            parsed_damage["die_type"] = int(die_type_str) if die_type_str else 0
            if bonus_val_str:
                bonus = int(bonus_val_str)
                if sign == '-': bonus *= -1
                parsed_damage["bonus"] = bonus
            return parsed_damage
        elif simple_bonus_or_value_str:
            try:
                parsed_damage["bonus"] = int(simple_bonus_or_value_str)
                return parsed_damage
            except ValueError:
                dice_only_match = re.fullmatch(r"d(\d+)", simple_bonus_or_value_str, re.IGNORECASE)
                if dice_only_match:
                    parsed_damage["dice_count"] = 1; parsed_damage["die_type"] = int(dice_only_match.group(1))
                    return parsed_damage
    return {"text": original_text, "notes": "Could not fully parse damage string."}

def parse_weapon_category_code(code_str, is_ranged=False):
    if not code_str: return "Unknown"
    code = code_str.strip().upper()
    if is_ranged: mapping = {'P': "Pistols", 'R': "Rifles", 'H': "Heavy Weapons", 'E': "Exotic Ranged Weapons", 'S': "Simple Ranged Weapons"}
    else: mapping = {'S': "Simple Melee Weapons", 'AM': "Advanced Melee Weapons", 'L': "Lightsabers", 'E': "Exotic Melee Weapons", 'U': "Unarmed"}
    return mapping.get(code, f"Unknown Code ({code})")

def parse_item_size_code(code_str):
    if not code_str: return "Medium"
    code = code_str.strip().upper()
    mapping = {'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge", 'G': "Gargantuan", 'C': "Colossal"}
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
            bonus_match = re.search(r"\+([0-9]+)\s*(?:equipment|circumstance|bonus)?\s*(?:to|on)\s*([\w\s]+?)(?: checks)?(?: against [\w\s]+)?$", prop_cleaned, re.IGNORECASE)
            if bonus_match:
                effects.append({"type": "bonus", "value": int(bonus_match.group(1)), "target": bonus_match.group(2).strip(), "description": prop_cleaned})
            else: effects.append({"type": "narrative_property", "description": prop_cleaned})
    return effects if effects else [{"type": "narrative_property", "description": mtr_explanations(text_block)}]
    
def parse_accessory_type_code(code_str):
    if not code_str: return "Unknown"
    cleaned_code_str = clean_value(code_str).strip()
    mapping_values_title_case = [v.title() for v in ["Armor Upgrade", "Weapon Upgrade (Ranged)", "Weapon Upgrade (Melee)", "Lightsaber Upgrade", "Universal Upgrade", "Cybernetic Prosthesis Upgrade", "Tools", "Medical Gear", "Survival Gear", "Communications Devices", "Detection and Surveillance Devices", "Computers and Storage Devices", "Weapon and Armor Accessories", "Life Support", "Cybernetics", "Implants", "Artifacts", "Biotech"]]
    if cleaned_code_str.title() in mapping_values_title_case: return cleaned_code_str.title()
    code_upper = cleaned_code_str.upper()
    mapping = {'A': "Armor Upgrade", 'R': "Weapon Upgrade (Ranged)", 'M': "Weapon Upgrade (Melee)", 'L': "Lightsaber Upgrade", 'ANY': "Universal Upgrade", '*': "Cybernetic Prosthesis Upgrade"}
    return mapping.get(code_upper, f"Unknown Type ({code_str})")

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

# --- 3. PROCESSING FUNCTIONS FOR EACH ITEM CSV TYPE ---

def process_armor_csv():
    print("Processing Armor...")
    raw_data = read_csv_data(ARMOR_CSV_PATH)
    processed_armor_list = []
    if not raw_data: save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('ITEM', ''))
        book = clean_value(row.get('BOOK', ''))
        page = clean_value(row.get('PAGE', ''))
        if not name or not book or not page or len(name) > 60 or "see page" in name.lower() or name.startswith(','):
            continue
        desc_text = clean_value(row.get('Desc.', '')); armor_cat = parse_armor_category_from_desc(desc_text, name)
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else []
        spd_6sq = clean_value(row.get('Spd 6sq', '')); spd_4sq = clean_value(row.get('Spd 4sq', ''))
        speed_penalty_text = []
        if spd_6sq: speed_penalty_text.append(f"6sq Base: {spd_6sq}")
        if spd_4sq: speed_penalty_text.append(f"4sq Base: {spd_4sq}")
        helmet_p_val_raw = row.get('Helmet P.', ''); helmet_p_val_cleaned = clean_value(helmet_p_val_raw)
        armor_item = {"name": name, "full_text_description": desc_text or None, "armor_category": armor_cat, "armor_check_penalty": attempt_numeric_conversion(clean_value(row.get('ACP', '')), name, 'ACP', 'Armor'), "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost', '')), name, 'Cost', 'Armor'), "reflex_defense_bonus": attempt_numeric_conversion(clean_value(row.get('Ref bonus', '')), name, 'Ref bonus', 'Armor'), "fortitude_defense_bonus": attempt_numeric_conversion(clean_value(row.get('Fort bonus', '')), name, 'Fort bonus', 'Armor'), "max_dex_bonus": attempt_numeric_conversion(clean_value(row.get('Max Dex', '')), name, 'Max Dex', 'Armor'), "speed_penalty_text": ", ".join(speed_penalty_text) if speed_penalty_text else None, "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Armor'), "availability": clean_value(row.get('Avail.', '')), "upgrade_slots_text": clean_value(row.get('U. Slots', '')) or None, "has_helmet_package": helmet_p_val_cleaned.lower() == 'x' if isinstance(helmet_p_val_cleaned, str) else False, "special_properties_text": comments_text or None, "parsed_properties": parsed_props, "skill_bonuses_text": f"Skill: {row.get('Skill','N/A')}, Bonus: {row.get('Skillbonus','N/A')}" if row.get('Skill') else None, "ability_bonuses_text": f"Ability: {row.get('Ability','N/A')}, Bonus: {row.get('Abilitybonus','N/A')}" if row.get('Ability') else None, "used_by_text": clean_value(row.get('Used By', '')) or None, "source_book": book, "page": str(page)}
        processed_armor_list.append(armor_item)
    save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor")

def process_melee_weapons_csv():
    print("Processing Melee Weapons...")
    raw_data = read_csv_data(MELEE_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('WEAPON', ''))
        if not name or not clean_value(row.get('BOOK', '')) or not clean_value(row.get('PAGE', '')) or len(name) > 60 or "see page" in name.lower() or name.startswith(','): continue
        proficiency_code = clean_value(row.get('Wpn Type', ''))
        damage_type_raw_text = clean_value(row.get('Dmg Type', '')); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        damage_text = clean_value(row.get(' Damage', row.get('Damage','')))
        stun_text = clean_value(row.get('Stun', ''))
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else []
        weapon = {"name": name, "full_text_description": clean_value(row.get('Desc.', '')) or None, "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=False), "size_category": parse_item_size_code(clean_value(row.get('Size', ''))), "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost','')), name, 'Cost', 'Melee'), "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text), "stun_damage_text": stun_text or None, "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None, "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight','')), name, 'Weight', 'Melee'), "damage_types": damage_types_list, "availability": clean_value(row.get('Avail.', '')), "reach_or_thrown_info": clean_value(row.get('Thrown / Reach', '')) or None, "extra_cost_note": clean_value(row.get(' Extra cost', row.get('Extra cost',''))) or None, "build_dc_note": clean_value(row.get(' Build DC', row.get('Build DC',''))) or None, "special_properties_text": comments_text or None, "parsed_properties": parsed_props, "used_by_text": clean_value(row.get('Used by', '')) or None, "source_book": clean_value(row.get('BOOK', '')), "page": str(clean_value(row.get('PAGE', '')))}
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons")

def process_ranged_weapons_csv():
    print("Processing Ranged Weapons...")
    raw_data = read_csv_data(RANGED_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('WEAPON', ''))
        if not name or not clean_value(row.get('BOOK', '')) or not clean_value(row.get('PAGE', '')) or len(name) > 70 or "see page" in name.lower() or name.startswith(','):
            continue
        proficiency_code = clean_value(row.get('Wpn Type', ''))
        damage_type_raw_text = clean_value(row.get('Dmg Type', '')); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        damage_text = clean_value(row.get(' Damage', row.get('Damage',''))); stun_text = clean_value(row.get('Stun', ''))
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else []
        classification_tags = []
        if clean_value(row.get("Pistol", clean_value(row.get("Pistol\nRifle", '')))): classification_tags.append("Pistol")
        if clean_value(row.get("Rifle", clean_value(row.get("Pistol\nRifle", '')))): 
             if "rifle" in str(row.get("Pistol\nRifle", "")).lower() : classification_tags.append("Rifle")
        if clean_value(row.get("Heavy", clean_value(row.get("Heavy\nExotic", '')))): classification_tags.append("Heavy Weapon")
        if clean_value(row.get("Exotic", clean_value(row.get("Heavy\nExotic", '')))):
            if "exotic" in str(row.get("Heavy\nExotic", "")).lower() : classification_tags.append("Exotic Weapon")
        if clean_value(row.get("Simple", '') ): classification_tags.append("Simple Weapon")
        if clean_value(row.get("Accurate", clean_value(row.get("Accurate\nInaccurate", '')))): classification_tags.append("Accurate")
        if clean_value(row.get("Inaccurate", clean_value(row.get("Accurate\nInaccurate", '')))):
             if "inaccurate" in str(row.get("Accurate\nInaccurate", "")).lower(): classification_tags.append("Inaccurate")
        classification_tags = sorted(list(set(t for t in classification_tags if t)))
        weapon = {"name": name, "full_text_description": clean_value(row.get('Desc.', '')) or None, "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=True), "size_category": parse_item_size_code(clean_value(row.get('Size', ''))), "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost','')), name, 'Cost', 'Ranged'), "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text), "stun_damage_text": stun_text or None, "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None, "rate_of_fire_text": clean_value(row.get('Fire Rate', '')), "rate_of_fire_structured": parse_rate_of_fire(clean_value(row.get('Fire Rate', ''))), "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight','')), name, 'Weight', 'Ranged'), "damage_types": damage_types_list, "availability": clean_value(row.get('Avail.', '')), "area_effect_text": clean_value(row.get('Area', '')) or None, "ammunition_shots": attempt_numeric_conversion(clean_value(row.get('Shots','')), name, 'Shots', 'Ranged'), "ammunition_cost_text": clean_value(row.get(' Ammo Cost', row.get('Ammo Cost',''))) or None, "accuracy_note": clean_value(row.get(' Accuracy', row.get('Accuracy',''))) or None, "special_properties_text": comments_text or None, "parsed_properties": parsed_props, "classification_tags": classification_tags, "used_by_text": clean_value(row.get('Used By', '')) or None, "source_book": clean_value(row.get('BOOK', '')), "page": str(clean_value(row.get('PAGE', '')))}
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons")

def process_accessories_csv():
    print("Processing Accessories...")
    raw_data = read_csv_data(ACCESSORIES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories"); return
    for row in raw_data:
        name = clean_value(row.get('ACCESSORIES', ''))
        if not name or not clean_value(row.get('BOOK', '')) or not clean_value(row.get('PAGE', '')) or len(name) > 70: continue
        desc_text = clean_value(row.get('Desc.', ''))
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        weight_text = clean_value(row.get('Weight', '')); weight_kg = None
        if weight_text:
            if "%" in weight_text: weight_kg = None 
            else: weight_kg = attempt_numeric_conversion(weight_text, name, 'Weight', 'Accessory')
        item = {"name": name, "full_text_description": desc_text or None, "accessory_type_code": clean_value(row.get('Type', '')), "accessory_type_description": parse_accessory_type_code(clean_value(row.get('Type', ''))), "upgrade_points_cost_text": clean_value(row.get('U. Points', '')) or None, "availability": clean_value(row.get('Avail.', '')), "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost', '')), name, 'Cost', 'Accessory'), "weight_text": weight_text or None, "weight_kg": weight_kg, "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects, "source_book": clean_value(row.get('BOOK', '')), "page": str(clean_value(row.get('PAGE', '')))}
        processed_items.append(item)
    save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories")

def process_defensive_items_csv():
    print("Processing Defensive Items (Mines, Emplacements)...")
    raw_data = read_csv_data(DEFENSES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items"); return
    for row in raw_data:
        name = clean_value(row.get('WEAPON', '')) 
        if not name or not clean_value(row.get('BOOK', '')) or not clean_value(row.get('PAGE', '')) or len(name) > 50: continue
        damage_text = clean_value(row.get('Damage', ''))
        damage_type_raw_text = clean_value(row.get('Type', '')); damage_types_list = parse_damage_types_string(damage_type_raw_text)
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        delay_key = "Delay\n(rounds)" if "Delay\n(rounds)" in row else "Delay"
        item = {"name": name, "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost', '')), name, 'Cost', 'Defensive Item'), "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text), "damage_types": damage_types_list, "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Defensive Item'), "perception_dc_to_detect": attempt_numeric_conversion(clean_value(row.get('Perception', '')), name, 'Perception DC', 'Defensive Item'), "availability": clean_value(row.get('Avail.', '')), "splash_radius_text": clean_value(row.get('Splash', '')) or None, "delay_rounds_text": clean_value(row.get(delay_key, '')) or None, "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects, "source_book": clean_value(row.get('BOOK', '')), "page": str(clean_value(row.get('PAGE', '')))}
        processed_items.append(item)
    save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items")

def process_equipment_general_csv():
    print("Processing General Equipment...")
    raw_data = read_csv_data(EQUIPMENT_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment"); return
    for idx, row in enumerate(raw_data): 
        name = clean_value(row.get('ITEM', ''))
        book = clean_value(row.get('BOOK', ''))
        page = clean_value(row.get('PAGE', ''))
        
        # Stricter row validation for equipment
        if not name or not book or not page or len(name) > 70 or name.startswith(',') or \
           (book and (',' in book or len(book) > 5)) or \
           (page and not re.match(r"^\d+(-?\d*)?$", page)): # Page should be number or number-range
            # print(f"Skipping Equipment row {idx+2}: Name='{name}', Book='{book}', Page='{page}' due to missing/invalid essential fields or suspect name/book/page.")
            continue
            
        desc_text = clean_value(row.get('Desc.', ''))
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        item = {"name": name, "full_text_description": desc_text or None,
                "equipment_category_code": clean_value(row.get('TYPE', '')), 
                "equipment_category_description": parse_accessory_type_code(clean_value(row.get('TYPE', ''))), 
                "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost', '')), name, 'Cost', 'Equipment'),
                "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Equipment'),
                "uses_text": clean_value(row.get('Uses', '')) or None,
                "use_cost_text": clean_value(row.get(' Use Cost', row.get('Use Cost', ''))) or None, 
                "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects,
                "source_book": book, "page": str(page)}
        processed_items.append(item)
    save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment")


# --- 4. MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting SAGA Index Elements CSV to JSON Conversion Process...\n")
    if PROCESS_CONFIG.get("armor", False): process_armor_csv()
    if PROCESS_CONFIG.get("melee_weapons", False): process_melee_weapons_csv()
    if PROCESS_CONFIG.get("ranged_weapons", False): process_ranged_weapons_csv()
    if PROCESS_CONFIG.get("accessories", False): process_accessories_csv()
    if PROCESS_CONFIG.get("defensive_items", False): process_defensive_items_csv()
    if PROCESS_CONFIG.get("equipment_general", False): process_equipment_general_csv()
    
    print("\nConfigured item/index element CSV processing complete.")

