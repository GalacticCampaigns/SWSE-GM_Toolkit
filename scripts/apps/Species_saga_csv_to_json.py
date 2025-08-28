import json
import csv
import io
import re # For more complex string parsing
import os # For os.path and os.makedirs

# --- 1. CONFIGURATION: SET CSV DATA SOURCE ---

# Local root path for the project
LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex'

# Default paths set to your provided locations, constructed using the root path
SPECIES_CSV_FILE_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Species.csv')
TRAITS_CSV_FILE_PATH = os.path.join(LOCAL_ROOT_PATH, r'scripts\csv\Character-Traits.csv')
OUTPUT_JSON_FILE_PATH = os.path.join(LOCAL_ROOT_PATH, r'data\character_elements\species.json')


# OPTION B: Paste CSV content directly as strings (Alternative)
# If using this option, set the file paths above to None or empty strings.
"""
SPECIES_CSV_FILE_PATH = None
TRAITS_CSV_FILE_PATH = None

SPECIES_CSV_STRING_DATA = \"""PASTE YOUR SPECIES CSV CONTENT HERE, STARTING WITH THE HEADER ROW
BOOK,PAGE,WEB,NPC or PC?,SPECIES,Str,Dex,Con,Int,Wis,Cha,Size,Spd,Vis,Ref,Fort,Will,CONDITIONAL FEAT,SKILLS,TRAITS,SPECIES,PERSONALITY,JEDI, NOBLE, SCOUNDREL,SCOUT, SOLDIER,Basic?,Language 1,Language 2,Language 3,...
L,199,w,N,Advozse,,-2,2,,2,,M,6,L,1,,,,"reroll Perception, mtr",,Advozse,...
... (and so on for all species data)
\"""

TRAITS_CSV_STRING_DATA = \"""PASTE YOUR TRAITS CSV CONTENT HERE, STARTING WITH THE HEADER ROW
BOOK,PAGE,SPECIES,TRAIT,BENEFIT
L,199,Advozse,Heightened Awareness,"You may choose to reroll any Perception check, but you must accept the result of the reroll"
... (and so on for all traits data)
\"""
"""

# --- 2. HELPER FUNCTIONS ---

def mtr_explanations(text):
    if not text:
        return ""
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

def parse_trait_effects(description):
    effects = []
    desc_lower = description.lower()
    skill_defense_bonus_match = re.search(r"gain(?:s)? a \+(\d+)\s*(species|natural armor|armor|shield|equipment|circumstance|feat|inherent|insight|morale|size|dodge|racial|untyped)?\s*bonus (?:on|to|against)\s*([\w\s\(\)]+?)\s*(?:checks|defense|defense against|threshold|damage threshold)", desc_lower)
    if skill_defense_bonus_match:
        value = int(skill_defense_bonus_match.group(1))
        bonus_type = skill_defense_bonus_match.group(2).strip() if skill_defense_bonus_match.group(2) else "untyped"
        target_text = skill_defense_bonus_match.group(3).strip()
        effect = {"value": value, "bonus_type": bonus_type, "target": target_text}
        if "defense" in target_text or "defence" in target_text:
            defense_map = {"reflex": "Reflex", "fortitude": "Fortitude", "will": "Will", "all": "All"}
            found_def = "Unknown"
            for key, val_map in defense_map.items():
                if key in target_text:
                    found_def = val_map
                    break
            effect["type"] = "defense_bonus"
            effect["defense"] = found_def
        elif "damage threshold" in target_text:
            effect["type"] = "damage_threshold_bonus"
        else:
            effect["type"] = "skill_bonus"
            effect["skill"] = target_text.replace("checks", "").strip()
        effects.append(effect)
    feat_grant_match = re.search(r"gain(?:s)? ([\w\s\(\)]+?) as a bonus feat", desc_lower)
    if feat_grant_match:
        feat_name = feat_grant_match.group(1).strip()
        if "skill focus" in feat_name and "(" in feat_name and ")" in feat_name:
             actual_feat = feat_name[feat_name.find("(")+1:feat_name.find(")")]
             effects.append({"type": "feat_grant", "feat_name": f"Skill Focus ({actual_feat.title()})"})
        else:
            effects.append({"type": "feat_grant", "feat_name": feat_name.title()})
    dr_match = re.search(r"(?:DR|damage reduction)\s*(\d+)", description, re.IGNORECASE)
    if dr_match:
        effects.append({"type": "damage_reduction", "value": int(dr_match.group(1))})
    natural_weapon_match = re.search(r"(claws?|teeth|bite|horns?|tail|tentacles?)(?:.*?dealing)?\s*(\d+d\d+)\s*(\w+)?\s*(?:damage)?", desc_lower)
    if natural_weapon_match:
        effects.append({"type": "natural_weapon", "weapon_name": natural_weapon_match.group(1).strip(), "damage_dice": natural_weapon_match.group(2).strip(), "damage_type": natural_weapon_match.group(3).strip() if natural_weapon_match.group(3) else "unspecified"})
    reroll_match = re.search(r"reroll (?:any |one |a )?([\w\s]+?)(?: check)?(?:, (keeping|but must accept|but must take))?", desc_lower)
    if reroll_match:
        check_type = reroll_match.group(1).strip()
        condition = reroll_match.group(2).strip() if reroll_match.group(2) else "unspecified"
        if "must accept" in condition or "must take" in condition: condition = "must take result"
        elif "keeping" in condition: condition = "keep better/specified result"
        effects.append({"type": "reroll", "check_type": check_type, "condition": condition})
    class_skill_match = re.findall(r"([\w\s]+?)\s*(?:is|are)\s*(?:always considered a |a )?class skill", desc_lower)
    for skill_match in class_skill_match:
        skills = [s.strip() for s in re.split(r'\s+and\s+|\s*,\s*', skill_match)]
        for skill in skills:
            if skill and len(skill) > 2 : effects.append({"type": "class_skill", "skill": skill.title()})
    if not effects and description: effects.append({"type": "narrative_only", "summary": "Mechanics are described textually."})
    return effects

def parse_ability_modifiers(row_dict):
    modifiers = []
    ability_map = {"Str": "Strength", "Dex": "Dexterity", "Con": "Constitution", "Int": "Intelligence", "Wis": "Wisdom", "Cha": "Charisma"}
    species_csv_traits_text = row_dict.get('TRAITS', '').strip()
    if "add +2 to one ability" in species_csv_traits_text and "Str " in species_csv_traits_text:
        modifiers.append({"ability": "Choice", "value": "+2 to one ability score"})
        return modifiers
    if "one +2, one -2" in species_csv_traits_text:
        modifiers.append({"ability": "Choice", "value": "One ability score +2, one ability score -2"})
        return modifiers
    for csv_col, full_name in ability_map.items():
        val_str = row_dict.get(csv_col, "").strip()
        if val_str:
            cleaned_val_str = val_str.replace('*', '')
            try: modifiers.append({"ability": full_name, "value": int(cleaned_val_str)})
            except ValueError: print(f"Warning: Non-integer ability value '{val_str}' for {full_name} in species '{row_dict.get('SPECIES', 'Unknown')}'.")
    return modifiers

def parse_size(size_char):
    if not size_char: return "Unknown"
    size_map = {'S': "Small", 'M': "Medium", 'L': "Large", 'D': "Diminutive", 'T': "Tiny", 'H':"Huge", 'G':"Gargantuan", 'C':"Colossal"}
    return size_map.get(size_char.strip().upper(), size_char.strip())

def parse_speed(spd_str):
    if not spd_str: return 0
    try: return int(spd_str.split('/')[0].strip())
    except ValueError: return 0

def parse_languages(row_dict):
    languages = set()
    basic_q = row_dict.get('Basic?', '').strip().upper()
    lang1_val = row_dict.get('Language 1', '').strip()
    if basic_q == 'Y': languages.add("Basic (Understand only)" if "understand" in lang1_val.lower() else "Basic")
    elif basic_q and "understand" in basic_q.lower(): languages.add("Basic (Understand only)")
    for key in ['Language 1', 'Language 2', 'Language 3']:
        lang = row_dict.get(key, '').strip()
        if lang:
            if "basic" in lang.lower() and "understand" in lang.lower():
                if "Basic" in languages: languages.remove("Basic")
                languages.add("Basic (Understand only)")
            elif lang.lower() == "basic":
                if "Basic (Understand only)" not in languages: languages.add("Basic")
            elif lang: languages.add(lang)
    return sorted(list(languages))

def add_trait_if_new(special_qualities_list, name, description, existing_names_set, defense_types_covered=None):
    name_lower = name.lower()
    if name_lower not in existing_names_set:
        processed_description = mtr_explanations(description)
        trait_effects = parse_trait_effects(processed_description)
        special_qualities_list.append({"name": name, "description": processed_description, "effects": trait_effects})
        existing_names_set.add(name_lower)
        if defense_types_covered is not None:
            for effect in trait_effects:
                if effect.get("type") == "defense_bonus":
                    bonus_target = effect.get("defense", "").lower()
                    if bonus_target == "all":
                        defense_types_covered.update(['reflex', 'fortitude', 'will'])
                        break
                    elif bonus_target in ['reflex', 'fortitude', 'will']:
                        defense_types_covered.add(bonus_target)
            desc_lower = processed_description.lower()
            if "all of your defenses" in desc_lower and re.search(r"\+\d+", desc_lower):
                 defense_types_covered.update(['reflex', 'fortitude', 'will'])
            else:
                if "reflex defense" in desc_lower and re.search(r"\+\d+", desc_lower): defense_types_covered.add('reflex')
                if "fortitude defense" in desc_lower and re.search(r"\+\d+", desc_lower): defense_types_covered.add('fortitude')
                if "will defense" in desc_lower and re.search(r"\+\d+", desc_lower): defense_types_covered.add('will')
        return True
    return False

# --- 3. MAIN SCRIPT LOGIC ---
def generate_json_from_csv():
    traits_by_species = {}
    traits_data_source_type = "None"
    try:
        traits_csv_content = None
        if TRAITS_CSV_FILE_PATH and 'YOUR_PATH_TO_TRAITS.csv' not in TRAITS_CSV_FILE_PATH : # Check against placeholder
            with open(TRAITS_CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as file: traits_csv_content = file.read()
            traits_data_source_type = f"File: {TRAITS_CSV_FILE_PATH}"
        elif 'TRAITS_CSV_STRING_DATA' in globals() and isinstance(TRAITS_CSV_STRING_DATA, str) and TRAITS_CSV_STRING_DATA.strip().count('\n') > 1:
            traits_csv_content = TRAITS_CSV_STRING_DATA
            traits_data_source_type = "String Data"
        else: print(f"Warning: Traits CSV file path not set or placeholder used ({TRAITS_CSV_FILE_PATH}). Traits section may be incomplete.")
        if traits_csv_content:
            reader = csv.DictReader(io.StringIO(traits_csv_content))
            for row in reader:
                s_name, t_name, ben = row.get('SPECIES','').strip(), row.get('TRAIT','').strip(), row.get('BENEFIT','').strip()
                if s_name and t_name:
                    traits_by_species.setdefault(s_name, []).append({"name": t_name, "description": ben})
            print(f"Successfully loaded traits from {traits_data_source_type}.")
    except FileNotFoundError: print(f"Error: Traits CSV file not found at '{TRAITS_CSV_FILE_PATH}'. Please check the path.")
    except Exception as e: print(f"Error reading traits data from {traits_data_source_type}: {e}")

    all_species_objects = []
    species_data_source_type = "None"
    try:
        species_csv_content = None
        if SPECIES_CSV_FILE_PATH and 'YOUR_PATH_TO_SPECIES.csv' not in SPECIES_CSV_FILE_PATH: # Check against placeholder
            with open(SPECIES_CSV_FILE_PATH, mode='r', encoding='utf-8-sig') as file: species_csv_content = file.read()
            species_data_source_type = f"File: {SPECIES_CSV_FILE_PATH}"
        elif 'SPECIES_CSV_STRING_DATA' in globals() and isinstance(SPECIES_CSV_STRING_DATA, str) and SPECIES_CSV_STRING_DATA.strip().count('\n') > 1:
            species_csv_content = SPECIES_CSV_STRING_DATA
            species_data_source_type = "String Data"
        else:
            print(f"Error: Species CSV file path not set or placeholder used ({SPECIES_CSV_FILE_PATH}). Cannot generate JSON.")
            return
        if species_csv_content:
            cleaned_content = "\n".join([line for line in species_csv_content.splitlines() if line.strip()])
            reader = csv.DictReader(io.StringIO(cleaned_content))
            for row_dict in reader:
                species_name = row_dict.get('SPECIES', '').strip()
                if not species_name or not row_dict.get('BOOK'): continue
                current_species_traits, existing_trait_names_lower, defense_types_covered = [], set(), set()
                base_name = species_name.split('(')[0].strip()
                sources = [species_name] + ([base_name] if base_name != species_name else []) + (["Droid"] if "Droid," in species_name else [])
                for name_check in sources:
                    if name_check in traits_by_species:
                        for trait in traits_by_species[name_check]:
                            add_trait_if_new(current_species_traits, trait['name'], trait['description'], existing_trait_names_lower, defense_types_covered)
                vis = row_dict.get('Vis','').strip().upper()
                if vis == 'L': add_trait_if_new(current_species_traits, "Low-Light Vision", "Ignores concealment (but not total concealment) from darkness.", existing_trait_names_lower, defense_types_covered)
                elif vis == 'D': add_trait_if_new(current_species_traits, "Darkvision", "Ignores concealment (including total concealment) from darkness.", existing_trait_names_lower, defense_types_covered)
                defense_map = {'Ref': ('reflex', 'Reflex Defense'), 'Fort': ('fortitude', 'Fortitude Defense'), 'Will': ('will', 'Will Defense')}
                for col, (key, name) in defense_map.items():
                    val = row_dict.get(col,'').strip()
                    if val:
                        try:
                            bonus = int(val)
                            if key not in defense_types_covered:
                                add_trait_if_new(current_species_traits, f"Species Bonus to {name}", f"Gains a +{bonus} species bonus to {name}.", existing_trait_names_lower, defense_types_covered)
                        except ValueError: print(f"Warning: Non-integer defense bonus '{val}' for {col} in '{species_name}'.")
                all_species_objects.append({
                    "name": species_name, "pc_or_npc": row_dict.get('NPC or PC?','').strip(),
                    "ability_modifiers": parse_ability_modifiers(row_dict), "size": parse_size(row_dict.get('Size','')),
                    "speed_squares": parse_speed(row_dict.get('Spd','')),
                    "special_qualities": sorted(current_species_traits, key=lambda x: x['name']),
                    "automatic_languages": parse_languages(row_dict),
                    "source_book": row_dict.get('BOOK','').strip(), "page": row_dict.get('PAGE','').strip()})
            print(f"Successfully processed species from {species_data_source_type}.")
    except FileNotFoundError: print(f"Error: Species CSV file not found at '{SPECIES_CSV_FILE_PATH}'.")
    except Exception as e: print(f"Error reading species data from {species_data_source_type}: {e}")

    final_json_output = {"species_data": {"description": "Compilation of species data including their abilities, physical characteristics, and special racial qualities. Traits are primarily sourced from a dedicated Traits listing.", "species_list": sorted(all_species_objects, key=lambda x: x['name'])}}
    try:
        output_dir = os.path.dirname(OUTPUT_JSON_FILE_PATH)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir); print(f"Created output directory: {output_dir}")
        with open(OUTPUT_JSON_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(final_json_output, f, indent=2)
        print(f"\nSuccessfully generated JSON output to: {OUTPUT_JSON_FILE_PATH}")
    except Exception as e: print(f"Error writing JSON to file: {e}")

if __name__ == '__main__':
    print("Starting SAGA Species JSON generation (Paths Updated, Effects Parsing, Corrected Indentation)...")
    generate_json_from_csv()
    print("Script finished.")
