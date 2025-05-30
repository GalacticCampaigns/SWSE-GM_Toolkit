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
STARSHIPS_CSV_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Index-Starships.csv') # Added
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
VEHICLES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\vehicles.json') 
STARSHIPS_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\starships.json') # Added
TECHSPEC_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\tech_specialist_upgrades.json')
TEMPLATES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\templates.json')
EXPLOSIVES_JSON_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\index_elements\explosives.json')


# --- SCRIPT EXECUTION CONFIGURATION ---
PROCESS_CONFIG = {
    "armor": False, # Set to True to process
    "melee_weapons": False,
    "ranged_weapons": False,
    "accessories": False, 
    "defensive_items": False, 
    "equipment_general": False,
    "vehicles": False, 
    "starships": True, # Enable starship processing
    "tech_specialist_upgrades": False, 
    "templates": False, 
    "explosives": False, 
}

# --- 2. GENERIC HELPER FUNCTIONS ---

def clean_value(value):
    if isinstance(value, str):
        value = re.sub(r"\[source:\s*\d+\]", "", value) 
        temp_value = value.strip()
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
    if cleaned_str.lower().endswith('x') and field_name_for_warning.lower() in ['cost', 'weight', 'cost_credits', 'weight_kg', 'cargo (tons)']: 
        cleaned_str = cleaned_str[:-1].strip()
    if '/m' in cleaned_str.lower(): return value_str 
    if ' or ' in cleaned_str: return value_str 
    if '*' in cleaned_str: cleaned_str = cleaned_str.replace('*', '').strip()
    try:
        if '.' in cleaned_str: return float(cleaned_str)
        else: return int(cleaned_str)
    except ValueError:
        if len(str(original_value_for_warning)) < 50 : 
             # print(f"Warning ({data_type_for_warning}): Could not convert '{field_name_for_warning}' to number for '{item_name_for_warning}'. Original CSV value: '{original_value_for_warning}'. Storing as None.")
             pass
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
        if len(parts) == 2: return {"primary": parse_damage_string(parts[0]), "secondary": parse_damage_string(parts[1]), "text": original_text, "damage_multiplier": multiplier}
    match = re.fullmatch(r"(?:(\d*)d(\d+))?(?:\s*([+-])\s*(\d+))?|([+-]?\d+)", damage_str, re.IGNORECASE)
    if match:
        dice_count_str, die_type_str, sign, bonus_val_str, simple_bonus_or_value_str = match.groups()
        parsed_damage = {"text": original_text, "dice_count": 0, "die_type": 0, "bonus_modifier": 0, "damage_multiplier": multiplier}
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
    return {"text": original_text, "notes": "Could not fully parse damage string.", "damage_multiplier": multiplier}

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

def parse_vehicle_starship_size_code(code_str):
    if not code_str: return "Unknown"
    code = code_str.strip().upper()
    mapping = {'F': "Fine", 'D': "Diminutive", 'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge", 'G': "Gargantuan", 'C': "Colossal", 'CS': "Colossal (station)", 'CF': "Colossal (frigate)", 'CC': "Colossal (cruiser)" }
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

def parse_starship_classification(class_code_csv, starship_name, manufacturer_csv): # Renamed from map_vehicle_class_terrain_to_classification
    primary = "Unknown Starship Type"; secondary = None; model = starship_name
    class_code_upper = class_code_csv.strip().upper() if class_code_csv else ""
    name_lower = starship_name.lower()
    # Starship specific class codes (Sf, ST, CS etc.)
    if class_code_upper == "SF": primary = "Starfighter"
    elif class_code_upper == "ST": primary = "Space Transport"
    elif class_code_upper == "CS": primary = "Capital Ship"
    elif class_code_upper == "SS": primary = "Space Station"
    # Fallback to name parsing if class_code is not specific enough
    elif "fighter" in name_lower or "interceptor" in name_lower: primary = "Starfighter"
    elif "transport" in name_lower or "freighter" in name_lower or "shuttle" in name_lower or "yacht" in name_lower or "liner" in name_lower: primary = "Space Transport"
    elif any(cs_type in name_lower for cs_type in ["cruiser", "destroyer", "frigate", "dreadnought", "battleship", "carrier", "capital"]): primary = "Capital Ship"
    
    if primary == "Space Transport":
        if "light freighter" in name_lower: secondary = "Light Freighter"
        elif "medium freighter" in name_lower: secondary = "Medium Freighter"
        elif "bulk freighter" in name_lower: secondary = "Bulk Freighter"
        elif "shuttle" in name_lower: secondary = "Shuttle"
        elif "yacht" in name_lower: secondary = "Yacht"
        elif "liner" in name_lower: secondary = "Liner"
    elif primary == "Starfighter":
        if "interceptor" in name_lower: secondary = "Interceptor"
        elif "bomber" in name_lower: secondary = "Bomber"
        elif "heavy starfighter" in name_lower: secondary = "Heavy Starfighter"
    elif primary == "Capital Ship":
        if "corvette" in name_lower: secondary = "Corvette"; model = name 
        elif "frigate" in name_lower: secondary = "Frigate"; model = name
        elif "destroyer" in name_lower: secondary = "Destroyer"; model = name
        elif "cruiser" in name_lower: secondary = "Cruiser"; model = name
        elif "carrier" in name_lower: secondary = "Carrier"; model = name
        elif "dreadnought" in name_lower: secondary = "Dreadnaught"; model = name
        elif "battleship" in name_lower: secondary = "Battleship"; model = name
    
    # Extract model from name if possible (e.g. "T-65B X-wing")
    model_match = re.search(r"([\w\d/-]+)\s+(?:class|series)?\s*(?:starfighter|transport|cruiser|etc.)", starship_name, re.IGNORECASE)
    if model_match: model = model_match.group(1).strip()
    elif " " in starship_name and any(char.isdigit() for char in starship_name.split(" ")[0]): # Heuristic: starts with model code
        model = starship_name.split(" ")[0]


    return {"type_primary": primary, "type_secondary": secondary, "class_name_model": model, "manufacturer": manufacturer_csv or None}

def parse_starship_size_details(size_code_csv, starship_name):
    size_text = "Unknown"; size_modifier = None
    size_map_code_to_text = {'F': "Fine", 'D': "Diminutive", 'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge", 'G': "Gargantuan", 'C': "Colossal", 'CS': "Colossal (station)", 'CF': "Colossal (frigate)", 'CC': "Colossal (cruiser)" }
    size_map_text_to_mod = {"Fine": 8, "Diminutive": 5, "Tiny": 2, "Small": 1, "Medium": 0, "Large": -1, "Huge": -2, "Gargantuan": -5, "Colossal": -10, "Colossal (station)": -10, "Colossal (frigate)": -10, "Colossal (cruiser)": -10}
    cleaned_size_code = size_code_csv.strip().upper()
    size_text = size_map_code_to_text.get(cleaned_size_code, size_code_csv) 
    if size_text in size_map_text_to_mod: size_modifier = size_map_text_to_mod[size_text]
    elif cleaned_size_code in size_map_code_to_text: 
        size_modifier = size_map_text_to_mod.get(size_map_code_to_text[cleaned_size_code])
    name_l = starship_name.lower() 
    if size_text == "Gargantuan":
        if "starfighter" in name_l or "fighter" in name_l: size_text = "Gargantuan (starfighter)"
        elif "transport" in name_l or "freighter" in name_l: size_text = "Gargantuan (transport)"
    elif size_text == "Colossal":
        if "frigate" in name_l: size_text = "Colossal (frigate)"
        elif "cruiser" in name_l: size_text = "Colossal (cruiser)"
        elif "transport" in name_l or "freighter" in name_l: size_text = "Colossal (transport)"
        elif "station" in name_l or "platform" in name_l: size_text = "Colossal (station)"
    return size_text, size_modifier

def parse_starship_hyperdrive(hyperdrive_str, backup_hyperdrive_str, comments_str): # Added comments_str
    primary_rating = hyperdrive_str.strip() or None
    backup_rating = backup_hyperdrive_str.strip() or None
    nav_notes = None
    nav_computer_type = "Standard" # Default

    if comments_str: # Try to parse nav computer notes from comments
        nav_match = re.search(r"Navicomputer:\s*([\w\s,-]+)", comments_str, re.IGNORECASE)
        if nav_match:
            nav_notes_text = nav_match.group(1).strip()
            if "limited" in nav_notes_text.lower() and "jump" in nav_notes_text.lower():
                nav_computer_type = "Limited Jump Calculation"
                nav_notes = nav_notes_text
            elif "astromech" in nav_notes_text.lower():
                nav_computer_type = "Astromech Droid Required"
                nav_notes = nav_notes_text
            elif nav_notes_text.lower() == "none":
                nav_computer_type = "None"
                nav_notes = None
            else:
                nav_notes = nav_notes_text # Store whatever was found

    if primary_rating or backup_rating or nav_notes: # Only create object if there's some hyperdrive info
        return {"primary_class_rating_text": primary_rating, 
                "backup_class_rating_text": backup_rating, 
                "nav_computer_type": nav_computer_type, 
                "nav_computer_notes": nav_notes}
    return None

def parse_starship_cost_object(new_cost_str, used_cost_str, item_name):
    options = []
    if new_cost_str:
        val = attempt_numeric_conversion(new_cost_str, item_name, "Cost (new)", "Starship")
        options.append({"type": "fixed_amount" if isinstance(val, (int, float)) else "text_description", "value": val if isinstance(val, (int, float)) else new_cost_str, "description": "New", "unit_type": "credit" if isinstance(val, (int, float)) else None})
    if used_cost_str:
        val = attempt_numeric_conversion(used_cost_str, item_name, "Cost (used)", "Starship")
        options.append({"type": "fixed_amount" if isinstance(val, (int, float)) else "text_description", "value": val if isinstance(val, (int, float)) else used_cost_str, "description": "Used", "unit_type": "credit" if isinstance(val, (int, float)) else None})
    return {"text_original": f"New: {new_cost_str or 'N/A'}, Used: {used_cost_str or 'N/A'}", "options": options if options else [{"type": "text_description", "value": "Not specified"}], "selection_logic": None, "notes": None}

def parse_starship_armament_from_row(row):
    armament_systems = []
    weapon_column_map = {
        "Laser": "Spec.", "Turbolaser": "Spec.", "Autoblaster": "Spec.", 
        "Blaster": "Spec.", "Ion": "Spec.", "Superlaser": "Spec.", 
        "Volcano": "Spec.", "Missiles": None, "Torpedo": None, 
        "Mine": None, "Tractor": "Spec?"
    }
    actual_keys = list(row.keys())
    
    # Find all "Spec" columns and try to associate them with the preceding weapon column
    # This assumes a pattern: WeaponCol, SpecCol, WeaponCol2, SpecCol2...
    # Or WeaponCol, WeaponCol2, ..., SpecCol_for_Weapon1, SpecCol_for_Weapon2 (less likely with DictReader)

    # Let's try to iterate through weapon types and find their corresponding Spec.
    # This is complex because DictReader might rename duplicate "Spec." to "Spec._1", "Spec._2"
    
    # A more direct approach: iterate through the expected weapon types
    # and try to find their count and spec data by looking at a few possible key names
    
    weapon_base_names = ["Laser", "Turbolaser", "Autoblaster", "Blaster", "Ion", "Superlaser", "Volcano", "Missiles", "Torpedo", "Mine", "Tractor"]
    
    parsed_weapon_specs = {} # To avoid double-parsing if "Weaponry" column lists already parsed items

    for i, base_name in enumerate(weapon_base_names):
        count_val_str = clean_value(row.get(base_name, ''))
        
        if count_val_str: # If there's a count or 'x' for this weapon type
            # Try to find the associated "Spec." column.
            # This is heuristic: assumes "Spec." might be "Spec.", "Spec._1", etc.
            # A better CSV would have unique headers like "Laser Spec", "Turbolaser Spec".
            spec_text = ""
            # Try specific key first if it exists
            spec_key_options = [f"Spec._{i}", "Spec.", "Spec?"] # Common variations
            if base_name == "Tractor": spec_key_options = ["Spec?", "Spec._1", "Spec."] # Tractor has "Spec?"

            for key_opt_base in weapon_column_map.get(base_name, [None]): # Get the spec key part
                if key_opt_base: # If a spec column is expected
                    # Try to find the exact key or a numbered variant
                    found_spec_key = None
                    if key_opt_base in row: found_spec_key = key_opt_base
                    else:
                        for k_idx in range(1, 7): # Check Spec._1 to Spec._6
                            if f"{key_opt_base}_{k_idx}" in row: found_spec_key = f"{key_opt_base}_{k_idx}"; break
                    if found_spec_key:
                        spec_text = clean_value(row.get(found_spec_key, ''))
                        break # Found a spec column for this weapon type

            weapon_count = attempt_numeric_conversion(count_val_str, base_name, "Count", "Starship Armament")
            display_name = f"{weapon_count if isinstance(weapon_count, int) and weapon_count > 1 else ''} {base_name}".strip()
            if count_val_str.lower() == 'x': display_name = base_name

            damage_text_from_spec = "See description"
            dmg_match_spec = re.search(r"(\d+d\d+(?:x[25])?(?:[+-]\d+)?)", spec_text)
            if dmg_match_spec: damage_text_from_spec = dmg_match_spec.group(1)
            
            range_text_from_spec = "See description"
            range_keywords = ["Point Blank", "Short", "Medium", "Long", "Extreme"]
            for rk in range_keywords:
                if rk.lower() in spec_text.lower(): range_text_from_spec = rk; break
            
            armament_item = {
                "weapon_name_or_type": display_name,
                "mount_location_arc": spec_text or None, 
                "damage_text": damage_text_from_spec,
                "damage_structured": parse_damage_string(damage_text_from_spec),
                "damage_types": parse_damage_types_string(spec_text),
                "range_category_text_starship_scale": range_text_from_spec,
                "special_notes": spec_text or None
            }
            armament_systems.append(armament_item)
            parsed_weapon_specs[display_name.lower()] = True


    # Process the general "Weaponry" column as a fallback or supplement
    weaponry_text = clean_value(row.get('Weaponry', ''))
    if weaponry_text:
        individual_weapon_entries = [w.strip() for w in weaponry_text.split(',') if w.strip()]
        for entry in individual_weapon_entries:
            entry_name_part = entry.split('(')[0].strip()
            if entry_name_part and entry_name_part.lower() not in parsed_weapon_specs:
                dmg_match = re.search(r"(\d+d\d+(?:x[25])?(?:[+-]\d+)?)", entry)
                dmg_text = dmg_match.group(1) if dmg_match else "See description"
                armament_systems.append({
                    "weapon_name_or_type": entry_name_part,
                    "mount_location_arc": entry,
                    "damage_text": dmg_text,
                    "damage_structured": parse_damage_string(dmg_text),
                    "damage_types": parse_damage_types_string(entry),
                    "range_category_text_starship_scale": "See description", # Needs parsing from entry
                    "special_notes": entry
                })
    return armament_systems


def parse_starship_special_qualities(comments_str, starship_name):
    if not comments_str: return []
    qualities = []
    text = re.sub(r"(?:Armament|Weapons?):\s*([\s\S]+?)(?=\n\n|\Z|Crew:|Passengers:|Cargo:|Systems:)", "", comments_str, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"Crew:\s*([\s\S]+?)(?=\n\n|\Z|Passengers:|Cargo:|Systems:)", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"Passengers:\s*([\s\S]+?)(?=\n\n|\Z|Cargo:|Systems:)", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"Cargo:\s*([\s\S]+?)(?=\n\n|\Z|Systems:)", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"Hyperdrive:\s*([\s\S]+?)(?=\n\n|\Z)", "", text, flags=re.IGNORECASE | re.MULTILINE)
    parts = [p.strip() for p in text.split(';') if p.strip()]
    for part in parts:
        if part and len(part) > 5:
            qualities.append({"name": part.split(':')[0].strip() if ':' in part and len(part.split(':')[0]) < 40 else "Special Quality/System", "description": mtr_explanations(part), "source_citation_detail": None})
    return qualities

def parse_starship_skill_modifiers(skills_str):
    if not skills_str: return None
    # Example: "Pilot +2 (when X), Use Computer +5 (astrogation)"
    # Regex to find patterns like "Skill Name +X" or "Skill Name -X"
    modifiers = {}
    matches = re.findall(r"([\w\s\(\)]+?)\s*([+-]\d+)", skills_str)
    for match in matches:
        skill_name = match[0].strip().title()
        mod_value = int(match[1])
        modifiers[skill_name] = mod_value
    return modifiers if modifiers else {"raw_text": skills_str} if skills_str else None

# --- Vehicle-specific helpers (can be adapted from starship or remain distinct if needed) ---
def parse_vehicle_armament_from_comments(row, vehicle_name): # Pass full row
    # This will be very basic for vehicles if armament is not in dedicated columns
    # For now, let's assume it might be in a 'Weaponry' column similar to starships or in 'COMMENTS'
    comments_text = clean_value(row.get('COMMENTS', clean_value(row.get('Weaponry', ''))))
    if not comments_text: return []
    
    # Use a simplified version of starship armament parsing
    armament_systems = []
    potential_weapons = re.split(r'\n\s*(?=\S)|;\s*', comments_text)
    for wp_text in potential_weapons:
        wp_text = wp_text.strip()
        if not wp_text or len(wp_text) < 5: continue
        name_part = wp_text.split('(')[0].strip()
        if not name_part: name_part = wp_text.split(',')[0].strip() # Fallback
        if not name_part: name_part = "Weapon System"

        dmg_match = re.search(r"(\d+d\d+(?:x[25])?(?:[+-]\d+)?)", wp_text)
        dmg_text = dmg_match.group(1) if dmg_match else "See description"
        
        armament_systems.append({
            "weapon_name_or_type": name_part,
            "mount_location_arc": wp_text, # Store full text for now
            "damage_text": dmg_text,
            "damage_structured": parse_damage_string(dmg_text),
            "damage_types": parse_damage_types_string(wp_text),
            "special_notes": wp_text
        })
    return armament_systems


def parse_vehicle_special_qualities_from_comments(comments_str, vehicle_name):
    return parse_starship_special_qualities(comments_str, vehicle_name) # Reuse for now

def map_vehicle_class_terrain_to_classification(class_code, terrain_code, vehicle_name):
    # This is similar to starship, but for ground/air vehicles
    classification = {"type_primary": "Unknown Vehicle", "type_secondary": None, "class_name_model": vehicle_name, "manufacturer": None}
    terrain_lower = terrain_code.lower() if terrain_code else ""
    class_lower = class_code.lower() if class_code else ""

    if 'g' in terrain_lower: classification["type_primary"] = "Ground Vehicle"
    elif 'a' in terrain_lower: classification["type_primary"] = "Air Vehicle"
    # No 'S' for space in this context, as it's for vehicles.csv
    
    if class_lower == 'w': classification["type_secondary"] = "Walker"
    elif class_lower == 'sp': classification["type_secondary"] = "Speeder"
    elif class_lower == 'wh': classification["type_secondary"] = "Wheeled"
    elif class_lower == 'tr': classification["type_secondary"] = "Tracked"
    elif class_lower == 'rep': classification["type_secondary"] = "Repulsorlift"
    # Add more specific vehicle types if present in 'Class' column
    elif "bike" in vehicle_name.lower(): classification["type_secondary"] = "Speeder Bike"
    elif "swoop" in vehicle_name.lower(): classification["type_secondary"] = "Swoop"
    elif "landspeeder" in vehicle_name.lower(): classification["type_secondary"] = "Landspeeder"
    elif "airspeeder" in vehicle_name.lower(): classification["type_secondary"] = "Airspeeder"

    return classification

def parse_vehicle_size_text_and_modifier(size_str, vehicle_name):
    # Reuse starship size parser as it's more comprehensive
    return parse_starship_size_details(size_str, vehicle_name)

def parse_vehicle_skill_modifiers(skills_text):
    return parse_starship_skill_modifiers(skills_text) # Reuse for now

def parse_cost_object(new_cost_str, used_cost_str, item_name): # Generic cost object parser
    options = []
    if new_cost_str:
        val = attempt_numeric_conversion(new_cost_str, item_name, "Cost (new)", "Item")
        options.append({"type": "fixed_amount" if isinstance(val, (int, float)) else "text_description", "value": val if isinstance(val, (int, float)) else new_cost_str, "description": "New", "unit_type": "credit" if isinstance(val, (int, float)) else None})
    if used_cost_str:
        val = attempt_numeric_conversion(used_cost_str, item_name, "Cost (used)", "Item")
        options.append({"type": "fixed_amount" if isinstance(val, (int, float)) else "text_description", "value": val if isinstance(val, (int, float)) else used_cost_str, "description": "Used", "unit_type": "credit" if isinstance(val, (int, float)) else None})
    return {"text_original": f"New: {new_cost_str or 'N/A'}, Used: {used_cost_str or 'N/A'}", "options": options if options else [{"type": "text_description", "value": "Not specified"}], "selection_logic": None, "notes": None}


# --- 3. PROCESSING FUNCTIONS (Armor, Melee, Ranged, Accessories, Defenses, Equipment are above) ---
# ... (Existing processing functions: process_armor_csv, process_melee_weapons_csv, etc. remain here) ...
def process_armor_csv():
    print("Processing Armor...")
    raw_data = read_csv_data(ARMOR_CSV_PATH)
    processed_armor_list = []
    if not raw_data: save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('ITEM', ''))
        book = clean_value(row.get('BOOK', ''))
        page = clean_value(row.get('PAGE', ''))
        if not name or not book or not page or len(name) > 60 or "see page" in name.lower() or name.startswith(','): continue
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
        if not name or not book or not page or len(name) > 70 or name.startswith(',') or \
           (book and (',' in book or len(book) > 5)) or \
           (page and not re.match(r"^\d+(-?\d*)?$", page) and page.lower() != 'various'):
            continue
        desc_text = clean_value(row.get('Desc.', ''))
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_effects = parse_item_effects(comments_text) if comments_text else []
        item = {"name": name, "full_text_description": desc_text or None, "equipment_category_code": clean_value(row.get('TYPE', '')), "equipment_category_description": parse_accessory_type_code(clean_value(row.get('TYPE', ''))), "cost_credits": attempt_numeric_conversion(clean_value(row.get('Cost', '')), name, 'Cost', 'Equipment'), "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Equipment'), "uses_text": clean_value(row.get('Uses', '')) or None, "use_cost_text": clean_value(row.get(' Use Cost', row.get('Use Cost', ''))) or None, "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects, "source_book": book, "page": str(page)}
        processed_items.append(item)
    save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment")

def process_vehicles_csv():
    print("Processing Vehicles...")
    raw_data = read_csv_data(VEHICLES_CSV_PATH) 
    processed_vehicles = []
    if not raw_data: save_json_data(processed_vehicles, VEHICLES_JSON_PATH, "Vehicles"); return

    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('VEHICLE', ''))
        book = clean_value(row.get('BOOK', ''))
        page_str = clean_value(row.get('PAGE', ''))

        if not name or not book or not page_str or len(name) > 70 or "see page" in name.lower() or name.startswith(','):
            continue
        
        vehicle_id = generate_id_from_name(name, prefix="vehicle") + f"_{book.lower()}{page_str.replace(' ','')}"
        
        classification = map_vehicle_class_terrain_to_classification(
            clean_value(row.get('Class','')), clean_value(row.get('Terrain','')), name
        )
        classification["manufacturer"] = clean_value(row.get('MANUFACTURER','')) or None

        size_text_raw = clean_value(row.get('Size',''))
        size_text, size_mod = parse_vehicle_size_text_and_modifier(size_text_raw, name)
        
        comments = clean_value(row.get('COMMENTS',''))
        armament_systems = parse_vehicle_armament_from_comments(row, name) 
        special_qualities = parse_vehicle_special_qualities_from_comments(comments, name)

        vehicle_item = {
            "id": vehicle_id, "name": name, "source_book": book,
            "page": attempt_numeric_conversion(page_str, name, 'PAGE', 'Vehicle'),
            "full_text_description": clean_value(row.get('Desc.', '')) or None, 
            "cl": attempt_numeric_conversion(clean_value(row.get('CL', '')), name, 'CL', 'Vehicle'),
            "cl_base_ship": attempt_numeric_conversion(clean_value(row.get('Ship CL', '')), name, 'Ship CL', 'Vehicle'), # Schema uses cl_base_ship
            "vehicle_classification": classification,
            "physical_characteristics": {
                "size_category_text": size_text,
                "size_modifier_applies_to_reflex_initiative_pilot": size_mod,
                "length_m": None, "width_m": None, "height_m": None, 
                "visual_description_brief": None
            },
            "performance_characteristics": {
                "initiative_vehicle_modifier_total": attempt_numeric_conversion(clean_value(row.get('Pilot (Init)','')), name, 'Pilot (Init)', 'Vehicle'),
                "senses_perception_vehicle_modifier": None, 
                "speed_details": {
                    "character_scale_max_squares_per_move": attempt_numeric_conversion(clean_value(row.get('Speed (C)','')), name, 'Speed (C)', 'Vehicle'),
                    "starship_scale_max_squares_per_move": attempt_numeric_conversion(clean_value(row.get('Speed (S)','')), name, 'Speed (S)', 'Vehicle'),
                    "max_velocity_kph_text": clean_value(row.get('Max\nVelocity', row.get('Max Velocity',''))) or None,
                    "operational_altitude_text": None 
                },
                "hyperdrive_system": None 
            },
            "core_combat_stats": {
                "strength_score": attempt_numeric_conversion(clean_value(row.get('STR','')), name, 'STR', 'Vehicle'),
                "dexterity_score": attempt_numeric_conversion(clean_value(row.get('DEX','')), name, 'DEX', 'Vehicle'),
                "intelligence_score": attempt_numeric_conversion(clean_value(row.get('INT','')), name, 'INT', 'Vehicle'),
                "hit_points_total": attempt_numeric_conversion(clean_value(row.get('HP','')), name, 'HP', 'Vehicle'),
                "damage_threshold_base": attempt_numeric_conversion(clean_value(row.get('Threshold','')), name, 'Threshold', 'Vehicle'),
                "defenses": {"reflex_defense_total": attempt_numeric_conversion(clean_value(row.get('RefDef','')), name, 'RefDef', 'Vehicle'), "reflex_defense_flat_footed": None, "fortitude_defense_total": attempt_numeric_conversion(clean_value(row.get('FortDef','')), name, 'FortDef', 'Vehicle'), "equipment_armor_bonus_to_reflex": attempt_numeric_conversion(clean_value(row.get('Armor','')), name, 'Armor Bonus', 'Vehicle'), "armor_dr_value": attempt_numeric_conversion(clean_value(row.get('DR','')), name, 'DR', 'Vehicle'), "shield_rating_sr_total": attempt_numeric_conversion(clean_value(row.get('SR','')), name, 'SR', 'Vehicle')},
                "base_attack_bonus_vehicle": attempt_numeric_conversion(clean_value(row.get('Attack','')), name, 'Attack', 'Vehicle'),
                "grapple_modifier_vehicle": attempt_numeric_conversion(clean_value(row.get('Grapple','')), name, 'Grapple', 'Vehicle')
            },
            "operational_crew_and_capacity": {"crew_complement_text": f"{clean_value(row.get('Crew',''))} ({clean_value(row.get('C. Quality',''))})" if clean_value(row.get('Crew','')) else None, "passengers_capacity_text": clean_value(row.get('Passeng.','')) or None, "cargo_capacity_metric_tons": attempt_numeric_conversion(clean_value(row.get('Cargo (tons)','')), name, 'Cargo (tons)', 'Vehicle'), "consumables_duration_text": clean_value(row.get('Consumables','')) or None, "carried_craft_description": None, "astromech_slots": attempt_numeric_conversion(clean_value(row.get('Astromech','')), name, 'Astromech Slots', 'Vehicle')},
            "armament_systems": armament_systems,
            "availability_cost": {"restriction_text": clean_value(row.get('Availability','')) or None, "cost_credits_object": parse_cost_object(clean_value(row.get('Cost (new)','')), clean_value(row.get('Cost (used)','')), name)},
            "special_qualities_systems": special_qualities,
            "vehicle_skill_modifiers_provided": parse_vehicle_skill_modifiers(clean_value(row.get('Skills','')))
        }
        processed_vehicles.append(vehicle_item)
    save_json_data(processed_vehicles, VEHICLES_JSON_PATH, "Vehicles")

def process_starships_csv():
    print("Processing Starships...")
    raw_data = read_csv_data(STARSHIPS_CSV_PATH)
    processed_starships = []
    if not raw_data: save_json_data(processed_starships, STARSHIPS_JSON_PATH, "Starships"); return

    for idx, row in enumerate(raw_data):
        name_raw = clean_value(row.get('STARSHIP', ''))
        book = clean_value(row.get('BOOK', ''))
        page_str = clean_value(row.get('PAGE', ''))
        if not name_raw or not book or not page_str or len(name_raw) > 80 or "see page" in name_raw.lower() or name_raw.startswith(','):
            continue
        
        starship_id = generate_id_from_name(name_raw, prefix="starship") + f"_{book.lower()}{page_str.replace(' ','')}"
        classification = parse_starship_classification(clean_value(row.get('Class','')), name_raw, clean_value(row.get('MANUFACTURER','')))
        size_text_raw = clean_value(row.get('Size','')); size_text, size_mod = parse_starship_size_details(size_text_raw, name_raw)
        comments = clean_value(row.get('COMMENTS',''))
        armament_systems = parse_starship_armament_from_row(row)
        special_qualities = parse_starship_special_qualities(comments, name_raw)

        starship_item = {
            "id": starship_id, "name": name_raw, "source_book": book,
            "page": attempt_numeric_conversion(page_str, name_raw, 'PAGE', 'Starship'),
            "full_text_description": clean_value(row.get('Desc.', '')) or None, 
            "cl": attempt_numeric_conversion(clean_value(row.get('CL', '')), name_raw, 'CL', 'Starship'),
            "cl_base_ship": attempt_numeric_conversion(clean_value(row.get('Ship CL', '')), name_raw, 'Ship CL', 'Starship'),
            "starship_classification": classification,
            "physical_characteristics": {"size_category_text": size_text, "size_modifier_applies_to_reflex_initiative_pilot": size_mod, "length_m": None, "width_m": None, "height_m": None, "visual_description_brief": None},
            "performance_characteristics": {
                "initiative_starship_modifier_total": attempt_numeric_conversion(clean_value(row.get('Pilot (Init)','')), name_raw, 'Pilot (Init)', 'Starship'),
                "senses_perception_starship_modifier": None, 
                "speed_details": {
                    "starship_scale_max_squares_per_move": attempt_numeric_conversion(clean_value(row.get('Speed (S)','')), name_raw, 'Speed (S)', 'Starship'),
                    "character_scale_max_squares_per_move": attempt_numeric_conversion(clean_value(row.get('Speed (C)','')), name_raw, 'Speed (C)', 'Starship'),
                    "max_velocity_kph_atmosphere": None, 
                    "max_velocity_sublight_space": clean_value(row.get(' Max Velocity', row.get('Max Velocity',''))) or None
                },
                "hyperdrive_system": parse_starship_hyperdrive(clean_value(row.get('Hyperdrive','')), clean_value(row.get('Backup Hyperdrive','')), comments)
            },
            "core_combat_stats": {
                "strength_score": attempt_numeric_conversion(clean_value(row.get('STR','')), name_raw, 'STR', 'Starship'),
                "dexterity_score": attempt_numeric_conversion(clean_value(row.get('DEX','')), name_raw, 'DEX', 'Starship'),
                "intelligence_score": attempt_numeric_conversion(clean_value(row.get('INT','')), name_raw, 'INT', 'Starship'),
                "hit_points_total": attempt_numeric_conversion(clean_value(row.get('HP','')), name_raw, 'HP', 'Starship'),
                "damage_threshold_base": attempt_numeric_conversion(clean_value(row.get('Threshold','')), name_raw, 'Threshold', 'Starship'),
                "defenses": {"reflex_defense_total": attempt_numeric_conversion(clean_value(row.get('RefDef','')), name_raw, 'RefDef', 'Starship'), "reflex_defense_flat_footed": None, "fortitude_defense_total": attempt_numeric_conversion(clean_value(row.get('FortDef','')), name_raw, 'FortDef', 'Starship'), "equipment_armor_bonus_to_reflex": attempt_numeric_conversion(clean_value(row.get('Armor','')), name_raw, 'Armor Bonus', 'Starship'), "armor_dr_value": attempt_numeric_conversion(clean_value(row.get('DR','')), name_raw, 'DR', 'Starship'), "shield_rating_sr_total": attempt_numeric_conversion(clean_value(row.get('SR','')), name_raw, 'SR', 'Starship')},
                "base_attack_bonus_starship": attempt_numeric_conversion(clean_value(row.get('Attack','')), name_raw, 'Attack', 'Starship'),
                "grapple_modifier_starship": attempt_numeric_conversion(clean_value(row.get('Grapple','')), name_raw, 'Grapple', 'Starship')
            },
            "operational_crew_and_capacity": {
                "crew_complement_text": f"{clean_value(row.get('Crew',''))} ({clean_value(row.get('C. Quality',''))})" if clean_value(row.get('Crew','')) else None,
                "passengers_capacity_text": clean_value(row.get('Passeng.','')) or None,
                "cargo_capacity_metric_tons": attempt_numeric_conversion(clean_value(row.get('Cargo (tons)','')), name_raw, 'Cargo (tons)', 'Starship'),
                "consumables_duration_text": clean_value(row.get('Consumables','')) or None,
                "carried_craft_description": None, 
                "astromech_slots": attempt_numeric_conversion(clean_value(row.get('Astromech','')), name_raw, 'Astromech Slots', 'Starship')
            },
            "armament_systems": armament_systems,
            "availability_cost": {"restriction_text": clean_value(row.get('Availability','')) or None, "cost_credits_object": parse_starship_cost_object(clean_value(row.get('Cost (new)','')), clean_value(row.get('Cost (used)','')), name_raw)},
            "special_qualities_systems": special_qualities,
            "starship_skill_modifiers_provided": parse_starship_skill_modifiers(clean_value(row.get('Skills','')))
        }
        processed_starships.append(starship_item)
    save_json_data(processed_starships, STARSHIPS_JSON_PATH, "Starships")


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
    
    print("\nConfigured item/index element CSV processing complete.")

