import json
import csv
import io
import re
import os

# --- 1. CONFIGURATION ---
LOCAL_ROOT_PATH = r'D:\OneDrive\Documents\GitHub\SagaIndex' # User should update this if necessary

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
    "tech_specialist_upgrades": True, 
    "templates": True, 
    "explosives": True, 
}

# --- 2. GENERIC HELPER FUNCTIONS ---

def clean_value(value):
    """Removes [source:X] tags and leading/trailing whitespace, including quotes."""
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
    """Handles 'mtr' (must take re-roll) explanations in text."""
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
                print(f"Using known delimiter '{known_delimiter}' for {source_type}.")
                reader_obj = csv.DictReader(io.StringIO(cleaned_content), delimiter=known_delimiter)
            else:
                try:
                    sample_for_sniffing = "\n".join(cleaned_content.splitlines()[:20]); 
                    if not sample_for_sniffing: sample_for_sniffing = cleaned_content
                    if len(sample_for_sniffing.strip()) <= 1 and '\n' not in sample_for_sniffing: raise csv.Error("Sample too small.")
                    dialect = csv.Sniffer().sniff(sample_for_sniffing)
                    print(f"Sniffed delimiter '{dialect.delimiter}' for {source_type}.")
                    reader_obj = csv.DictReader(io.StringIO(cleaned_content), dialect=dialect)
                except csv.Error as e_sniff: 
                    print(f"Sniffer failed for {source_type} ({e_sniff}). Trying fallbacks.")
                    pass 
                
                if not reader_obj: # Fallback if sniffer failed or if reader_obj is still None
                    for delim_try in [',', '\t', ';']:
                        try:
                            temp_io = io.StringIO(cleaned_content); temp_reader = csv.DictReader(temp_io, delimiter=delim_try)
                            first_row_check = next(temp_reader, None) 
                            if first_row_check and len(first_row_check.keys()) > 1: 
                                reader_obj = csv.DictReader(io.StringIO(cleaned_content), delimiter=delim_try)
                                print(f"Used fallback delimiter '{delim_try}' for {source_type}.")
                                break 
                        except Exception: continue
                    if not reader_obj: 
                        reader_obj = csv.DictReader(io.StringIO(cleaned_content)) # Absolute fallback to comma
                        print(f"Warning: Defaulting to comma delimiter for {source_type} after all attempts.")
            
            if reader_obj: return list(reader_obj)
            else: print(f"Warning: Could not create CSV reader for {source_type}."); return []
        else: print(f"Warning: No data source for {file_path or string_data_var_name}."); return []
    except FileNotFoundError: print(f"Error: CSV file not found: '{file_path}'."); return []
    except Exception as e: print(f"Error reading CSV {source_type}: {e}"); return []

def save_json_data(data, output_path, data_type_name):
    if not data: data_to_save = []
    else: data_to_save = sorted(data, key=lambda x: x.get("name", ""))
    final_output = {f"{data_type_name.lower().replace(' ', '_')}_data": {"description": f"Compilation of {data_type_name} for Star Wars SAGA Edition.", f"{data_type_name.lower().replace(' ', '_')}_list": data_to_save}}
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
        with open(output_path, 'w', encoding='utf-8') as f: json.dump(final_output, f, indent=2, ensure_ascii=False) 
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
    if cleaned_str.lower().endswith('x') and field_name_for_warning.lower() in ['weight', 'weight_kg']: cleaned_str = cleaned_str[:-1].strip()
    if '/m' in cleaned_str.lower(): return value_str 
    if '*' in cleaned_str: cleaned_str = cleaned_str.replace('*', '').strip() 
    try:
        if '.' in cleaned_str: return float(cleaned_str)
        else: return int(cleaned_str)
    except ValueError: return None 

def parse_complex_cost(cost_string):
    if cost_string is None: cost_string = "" 
    cost_string_cleaned = clean_value(str(cost_string))
    cost_obj = {"text_original": cost_string_cleaned, "options": [], "selection_logic": None}
    if not cost_string_cleaned: cost_obj["options"].append({"type": "text_description", "description": "None Specified"}); return cost_obj
    known_text_costs = ['varies', 'none', 'see text', 'see description', 'n/a', 'special']
    if cost_string_cleaned.lower() in known_text_costs: cost_obj["options"].append({"type": "text_description", "description": cost_string_cleaned.capitalize()}); return cost_obj
    text_lower = cost_string_cleaned.lower(); processed_text = cost_string_cleaned 
    if "whichever is more" in text_lower or "greater of" in text_lower or "whichever is higher" in text_lower:
        cost_obj["selection_logic"] = "whichever_is_more" 
        processed_text = re.sub(r",?\s*whichever is (?:more|higher)", "", processed_text, flags=re.IGNORECASE).strip()
        processed_text = re.sub(r"(?:greater|higher) of\s*", "", processed_text, flags=re.IGNORECASE).strip()
    elif "whichever is less" in text_lower or "lesser of" in text_lower or "whichever is lower" in text_lower:
        cost_obj["selection_logic"] = "whichever_is_less" 
        processed_text = re.sub(r",?\s*whichever is (?:less|lower)", "", processed_text, flags=re.IGNORECASE).strip()
        processed_text = re.sub(r"(?:lesser|lower) of\s*", "", processed_text, flags=re.IGNORECASE).strip()
    elif "player's choice" in text_lower or "player choice" in text_lower:
        cost_obj["selection_logic"] = "player_choice"
        processed_text = re.sub(r",?\s*player'?s choice", "", processed_text, flags=re.IGNORECASE).strip()
    potential_options_raw = []
    if " or " in processed_text: potential_options_raw = [opt.strip() for opt in processed_text.split(" or ")]
    elif " and " in processed_text and cost_obj["selection_logic"] and "credits" not in processed_text.split(" and ")[0].lower(): potential_options_raw = [opt.strip() for opt in processed_text.split(" and ")]
    else: potential_options_raw = [processed_text.strip()]
    potential_options = [opt for opt in potential_options_raw if opt] 
    if not potential_options and processed_text: potential_options = [processed_text]
    is_choice_component = (cost_obj["selection_logic"] is not None) or (len(potential_options) > 1 and " or " in cost_string_cleaned.lower())
    for option_str_raw in potential_options:
        option_str = option_str_raw.strip(); parsed_this_option = False; current_parse_str = option_str
        if not option_str: continue
        if is_choice_component and option_str.startswith('+'):
            temp_stripped = option_str[1:].lstrip()
            if re.fullmatch(r"(\d+\.?\d*)\s*%", temp_stripped) or re.fullmatch(r"(\d[\d,]*\.?\d*)(?:\s*(credits|cr))?", temp_stripped, re.IGNORECASE):
                current_parse_str = temp_stripped
        if not is_choice_component or option_str.startswith('-'):
            signed_percentage_match = re.fullmatch(r"([+-])\s*(\d+\.?\d*)\s*%", option_str)
            if signed_percentage_match:
                sign = signed_percentage_match.group(1); value = float(signed_percentage_match.group(2)) / 100.0
                if sign == '-': value *= -1
                cost_obj["options"].append({"type": "percentage_delta", "value": value}); parsed_this_option = True; continue
            if not parsed_this_option:
                signed_amount_match = re.fullmatch(r"([+-])\s*(\d[\d,]*\.?\d*)(?:\s*(credits|cr))?", option_str, re.IGNORECASE)
                if signed_amount_match:
                    sign = signed_amount_match.group(1); value_part = signed_amount_match.group(2).replace(',', ''); value = int(value_part)
                    if sign == '+': cost_obj["options"].append({"type": "additive_amount", "value": value})
                    elif sign == '-': cost_obj["options"].append({"type": "subtractive_amount", "value": value}) 
                    parsed_this_option = True; continue
        if not parsed_this_option:
            percentage_match = re.fullmatch(r"(\d+\.?\d*)\s*%", current_parse_str)
            if percentage_match: cost_obj["options"].append({"type": "set_to_percentage_of_base", "value": float(percentage_match.group(1)) / 100.0}); parsed_this_option = True; continue
            if not parsed_this_option:
                mult_match_prefix_x = re.fullmatch(r"x\s*(\d+\.?\d*)", current_parse_str, re.IGNORECASE)
                if mult_match_prefix_x: cost_obj["options"].append({"type": "base_item_multiplier", "value": float(mult_match_prefix_x.group(1))}); parsed_this_option = True; continue
                mult_match_suffix_x = re.fullmatch(r"(\d+\.?\d*)\s*x", current_parse_str, re.IGNORECASE)
                if mult_match_suffix_x: cost_obj["options"].append({"type": "base_item_multiplier", "value": float(mult_match_suffix_x.group(1))}); parsed_this_option = True; continue
            if not parsed_this_option:
                fixed_amount_match = re.fullmatch(r"(\d[\d,]*\.?\d*)(?:\s*(credits|cr))?", current_parse_str, re.IGNORECASE)
                if fixed_amount_match: value_part = fixed_amount_match.group(1).replace(',', ''); cost_obj["options"].append({"type": "fixed_amount", "value": int(value_part)}); parsed_this_option = True; continue
        if not parsed_this_option:
            if "used sale price" in option_str.lower(): cost_obj["options"].append({"type": "set_to_used_price", "description": option_str})
            else: cost_obj["options"].append({"type": "text_description", "description": option_str})
    if not cost_obj["options"] and cost_string_cleaned: cost_obj["options"].append({"type": "text_description", "description": cost_string_cleaned})
    elif len(cost_obj["options"]) == 0 and not cost_string_cleaned: cost_obj["options"].append({"type": "text_description", "description": "None"})
    return cost_obj

def parse_prerequisites_structured(text): 
    if not text or text.strip().lower() == 'none': return []
    prereqs = []; normalized_text = re.sub(r'\s*;\s*|\s+and\s+', ', ', text, flags=re.IGNORECASE)
    parts = [p.strip() for p in normalized_text.split(',') if p.strip()]
    for part in parts:
        obj = {"text_description": part} 
        ability_match = re.search(r"(Str|Dex|Con|Int|Wis|Cha|Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s*(\d+)", part, re.IGNORECASE)
        if ability_match: ability_map_short = {"str": "Strength", "dex": "Dexterity", "con": "Constitution", "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}; ability_short = ability_match.group(1).lower()[:3]; obj.update({"type": "ability_score", "ability": ability_map_short.get(ability_short, ability_match.group(1).capitalize()), "value": int(ability_match.group(2))}); prereqs.append(obj); continue
        bab_match = re.search(r"(?:BAB|Base attack bonus)\s*\+\s*(\d+)", part, re.IGNORECASE)
        if bab_match: obj.update({"type": "base_attack_bonus", "value": int(bab_match.group(1))}); prereqs.append(obj); continue
        trained_skill_match = re.search(r"Trained in ([\w\s\(\)]+)", part, re.IGNORECASE)
        if trained_skill_match: obj.update({"type": "skill_trained", "skill_name": trained_skill_match.group(1).strip()}); prereqs.append(obj); continue
        skill_rank_match = re.search(r"([\w\s\(\)]+?)\s*(\d+)\s*ranks?", part, re.IGNORECASE)
        if skill_rank_match: obj.update({"type": "skill_rank", "skill_name": skill_rank_match.group(1).strip(), "ranks": int(skill_rank_match.group(2))}); prereqs.append(obj); continue
        talent_prereq_match = re.search(r"([\w\s\'\’]+)\s*\(([\w\s]+)-([\w\s]+)\)", part)
        if talent_prereq_match: obj.update({"type": "talent_prerequisite", "talent_name": talent_prereq_match.group(1).strip(), "required_class": talent_prereq_match.group(2).strip(), "required_talent_tree": talent_prereq_match.group(3).strip()}); prereqs.append(obj); continue
        class_level_match = re.search(r"(\w+)\s*(?:level)?\s*(\d+)(?:st|nd|rd|th)?", part, re.IGNORECASE)
        if class_level_match:
            known_classes = ["jedi", "noble", "scoundrel", "scout", "soldier"]; class_name_match_lower = class_level_match.group(1).lower()
            if class_name_match_lower in known_classes or any(known_class in class_name_match_lower for known_class in known_classes): obj.update({"type": "class_level", "class_name": class_level_match.group(1).capitalize(), "level": int(class_level_match.group(2))}); prereqs.append(obj); continue
        char_level_match = re.search(r"(?:Character level|Level)\s*(\d+)(?:st|nd|rd|th)?", part, re.IGNORECASE)
        if char_level_match and not any(p['text_description'] == part and p['type'] == 'class_level' for p in prereqs): obj.update({"type": "character_level", "level": int(char_level_match.group(1))}); prereqs.append(obj); continue
        not_feat_match = re.search(r"not possess(?:ed of)? the ([\w\s]+) feat", part, re.IGNORECASE)
        if not_feat_match: obj.update({"type": "restriction_feat", "name": not_feat_match.group(1).strip(), "restriction": "cannot_have"}); prereqs.append(obj); continue
        if not talent_prereq_match: 
            feat_keywords = ["Focus","Proficiency","Mastery","Attack","Shot","Strike","Defense","Talent","Power","Secret","Technique","Combat","Vehicular","Dodge","Maneuver","Specialization","Fighting Style"] 
            if "feat" in part.lower() or any(k.lower() in part.lower() for k in feat_keywords) or (part.count(' ')<5 and sum(1 for c in part if c.isupper())>(1 if part.istitle() else 0) and not re.match(r"^\d+",part) and "rank" not in part.lower() and "level" not in part.lower()):
                feat_name_candidate = re.sub(r'\bfeat\b','',part,flags=re.IGNORECASE).strip()
                feat_name_candidate = re.sub(r'\s*\((General|Combat|Weapon|Armor|Shield|Force|Skill|Starship|Vehicle)\)$','',feat_name_candidate,flags=re.IGNORECASE).strip()
                if feat_name_candidate: obj.update({"type": "feat_or_ability", "name": feat_name_candidate}); prereqs.append(obj); continue
        obj["type"] = "other"; prereqs.append(obj)
    return prereqs

def parse_effects_structured(description, context_skill=None, is_recursive_call=False): 
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
                tier_structured_effects = parse_effects_structured(tier_description_cleaned, context_skill=None, is_recursive_call=True)
                if len(tier_structured_effects) > 1 and tier_structured_effects[0].get("type") == "narrative_only": tier_structured_effects.pop(0)
                elif not tier_structured_effects and tier_description_cleaned: tier_structured_effects = [{"type": "narrative_only", "summary": tier_description_cleaned}]
                tiers.append({"dc": dc_value, "description": tier_description_cleaned, "structured_effects": tier_structured_effects})
            if tiers:
                progression_rule = "cumulative_up_to_achieved_dc" 
                if "only the highest" in description.lower() or "instead of the normal effect" in description.lower(): progression_rule = "highest_achieved_only"
                effects.append({"type": "dc_progression", "check_skill_or_ability": context_skill or "Contextual Skill/Ability Check", "progression_rule": progression_rule, "tiers": sorted(tiers, key=lambda x: x['dc']), "full_progression_text": mtr_explanations(description) }); return effects 
    desc_lower = description.lower()
    bonus_penalty_regex = r"(gain(?:s)?|grants?|adds?|provides?|receives?|suffer(?:s)?|takes?|imposes?|reduces?|increases?)" \
                          r"\s*(?:a|an)?\s*" \
                          r"([+-]?\d+|one|two|three|four|five|half your level|character level|level|STR modifier|DEX modifier|CON modifier|INT modifier|WIS modifier|CHA modifier|Strength modifier|Dexterity modifier|Constitution modifier|Intelligence modifier|Wisdom modifier|Charisma modifier)" \
                          r"\s*" \
                          r"((?:point|step|die|persistent step|natural armor|species|armor|shield|equipment|circumstance|feat|inherent|insight|morale|size|dodge|racial|untyped|enhancement|competence|luck|sacred|profane|alchemical|resistance))?" \
                          r"\s*" \
                          r"((?:bonus|penalty|points of damage|persistent step))?" \
                          r"\s*(?:on|to|against|from|of|in|with|for|by)\s*" \
                          r"([\w\s\(\)\-\,\/\%]+?)" \
                          r"(?:\s*(?:checks|defense|attacks|damage|rolls|speed|track|DC|modifier|penalty|threshold|damage threshold|duration|initiative|skill checks|ability checks|saving throws|attack rolls)|$)"
    for match in re.finditer(bonus_penalty_regex, description, re.IGNORECASE): 
        action = match.group(1).strip(); value_str = match.group(2).strip()
        specific_type_keywords = match.group(3).strip() if match.group(3) else ""; general_indicator = match.group(4).strip() if match.group(4) else ""; target_str = match.group(5).strip()
        effect_type = "generic_modifier"; numeric_value = None
        word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        if value_str.isdigit() or (value_str.startswith(('+','-')) and value_str[1:].isdigit()): numeric_value = int(value_str)
        elif value_str.lower() in word_to_num: numeric_value = word_to_num[value_str.lower()]
        if "penalty" in general_indicator.lower() or (numeric_value is not None and numeric_value < 0) or value_str.startswith('-') or action.lower() in ["suffer", "suffers", "takes", "imposes", "reduces"]: effect_type = "penalty"
        elif "bonus" in general_indicator.lower() or (numeric_value is not None and numeric_value > 0) or value_str.startswith('+') or action.lower() in ["gain", "gains", "grants", "adds", "provides", "increases"]: effect_type = "bonus"
        if "damage" in general_indicator.lower() or "damage" in target_str.lower(): effect_type = "damage_modifier"
        elif "speed" in target_str.lower(): effect_type = "speed_modifier"
        elif "condition track" in target_str.lower() or "persistent step" in general_indicator.lower(): effect_type = "condition_track_change"
        elif "hit points" in target_str.lower() or "hp" in target_str.lower(): effect_type = "hit_points_modifier"
        bonus_or_penalty_category = specific_type_keywords if specific_type_keywords else "untyped"
        if bonus_or_penalty_category == "untyped" and general_indicator and general_indicator.lower() not in ["bonus", "penalty"]: bonus_or_penalty_category = general_indicator 
        effects.append({"type": effect_type, "action_verb": action, "value_description": value_str, "numeric_value_approx": numeric_value, "bonus_or_penalty_type": bonus_or_penalty_category.lower(), "target_description": target_str.strip()})
    feat_grant_match = re.search(r"gain(?:s)? ([\w\s\(\)]+?) as a bonus feat", desc_lower)
    if feat_grant_match:
        feat_name = feat_grant_match.group(1).strip()
        if "skill focus" in feat_name and "(" in feat_name and ")" in feat_name:
            actual_feat_name = feat_name[feat_name.find("(")+1:feat_name.find(")")].strip()
            effects.append({"type": "feat_grant", "feat_name": f"Skill Focus ({actual_feat_name.title()})"})
        else: effects.append({"type": "feat_grant", "feat_name": feat_name.title()}) 
    dr_match = re.search(r"(?:DR|damage reduction)\s*(\d+)", description, re.IGNORECASE) 
    if dr_match: effects.append({"type": "damage_reduction", "value": int(dr_match.group(1))})
    natural_weapon_match = re.search(r"(claws?|teeth|bite|horns?|tail|tentacles?)(?:.*?dealing)?\s*(\d+d\d+)\s*(\w+)?\s*(?:damage)?", desc_lower)
    if natural_weapon_match: effects.append({"type": "natural_weapon", "weapon_name": natural_weapon_match.group(1).strip(), "damage_dice": natural_weapon_match.group(2).strip(), "damage_type": natural_weapon_match.group(3).strip().capitalize() if natural_weapon_match.group(3) else "unspecified"})
    reroll_match = re.search(r"reroll (?:any |one |a )?([\w\s]+?)(?: check)?(?:, (keeping|but must accept|but must take|and take the better result|keeping the better result|must use the second result))?", desc_lower)
    if reroll_match:
        check_type = reroll_match.group(1).strip(); condition_text = reroll_match.group(2).strip() if reroll_match.group(2) else "unspecified"
        condition_logic = "unspecified"
        if "must accept" in condition_text or "must take" in condition_text or "must use the second result" in condition_text: condition_logic = "must_take_reroll_result"
        elif "keeping" in condition_text or "better result" in condition_text : condition_logic = "keep_better_or_specified_result"
        effects.append({"type": "reroll", "check_type": check_type, "condition_text": condition_text, "condition_logic": condition_logic})
    class_skill_match = re.findall(r"([\w\s\(\),]+?)\s*(?:is|are)\s*(?:always considered a |a )?class skill", desc_lower)
    for skill_match_group in class_skill_match:
        skills_text = skill_match_group.replace("and", ",").strip() 
        skills = [s.strip() for s in skills_text.split(',') if s.strip() and len(s.strip()) > 2] 
        for skill in skills: effects.append({"type": "class_skill_grant", "skill_name": skill.title()}) 
    action_match = re.search(r"(once per encounter|once per day|at will)?\s*(?:as a|as an)?\s*(swift|standard|full-round|move|free|reaction)\s*(?:action)?", desc_lower)
    if action_match: effects.append({"type": "special_action_activation", "frequency": action_match.group(1).strip() if action_match.group(1) else "at will (unless specified otherwise)", "action_cost": action_match.group(2).strip()})
    immunity_match = re.findall(r"immune to ([\w\s]+?)(?: effects)?(?:and|or|,|\.|$)", desc_lower)
    for immune_item in immunity_match: effects.append({"type": "immunity", "immune_to": immune_item.strip()})
    if not effects and description: effects.append({"type": "narrative_only", "summary": "Mechanics are described textually."}) 
    elif not effects and not description: effects.append({"type": "narrative_only", "summary": "No description provided."})
    return effects

# --- ITEM-SPECIFIC HELPER FUNCTIONS --- 
def parse_damage_string(damage_str): 
    if not damage_str: return None
    original_text = damage_str.strip()
    if not original_text or original_text.lower() == 'none': return None
    if '/' in original_text:
        parts = original_text.split('/')
        if len(parts) == 2: return {"primary_damage": parse_damage_string(parts[0]), "secondary_damage": parse_damage_string(parts[1]), "text_original": original_text }
        return {"text_original": original_text, "notes": "Complex multi-part damage string not fully parsed."}
    match = re.fullmatch(r"(?:(\d*)d(\d+))?(?:\s*([+-])\s*(\d+))?|([+-]?\d+)", original_text, re.IGNORECASE)
    if match:
        dice_count_str, die_type_str, sign, bonus_val_str, simple_bonus_or_value_str = match.groups()
        parsed_damage = {"text_original": original_text, "dice_count": 0, "die_type": 0, "bonus_modifier": 0}
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
                if dice_only_match: parsed_damage["dice_count"] = 1; parsed_damage["die_type"] = int(dice_only_match.group(1)); return parsed_damage
    return {"text_original": original_text, "notes": "Could not fully parse damage string."}

def parse_weapon_category_code(code_str, is_ranged=False): 
    if not code_str: return "Unknown"
    code = code_str.strip().upper()
    if is_ranged: mapping = {'P': "Pistols", 'R': "Rifles", 'H': "Heavy Weapons", 'E': "Exotic Ranged Weapons", 'S': "Simple Ranged Weapons", 'G': "Grenades"}
    else: mapping = {'S': "Simple Melee Weapons", 'AM': "Advanced Melee Weapons", 'L': "Lightsabers", 'E': "Exotic Melee Weapons", 'U': "Unarmed"}
    return mapping.get(code, f"Unknown Code ({code})")

def parse_item_size_code(code_str): 
    if not code_str: return "Medium" 
    code = code_str.strip().upper()
    mapping = {'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge", 'G': "Gargantuan", 'C': "Colossal", 'F': "Fine", 'D': "Diminutive"}
    return mapping.get(code, code) 

def parse_rate_of_fire(rof_str): 
    if not rof_str: return []
    parts = [p.strip().upper() for p in rof_str.split(',')]
    rof_map = {'S': "Single Shot", 'A': "Autofire"} 
    return [rof_map.get(p, p) for p in parts if p] 

def parse_armor_category_from_desc(desc_str, item_name="Unknown Item"): 
    if not desc_str: return "Unknown"
    desc_lower = desc_str.lower()
    if "heavy armor" in desc_lower: return "Heavy Armor"
    if "medium armor" in desc_lower: return "Medium Armor"
    if "light armor" in desc_lower: return "Light Armor"
    if "shield" in desc_lower and "energy shield" not in desc_lower : return "Shield" 
    if "energy shield" in desc_lower: return "Energy Shield"
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
            if bonus_match: effects.append({"type": "bonus", "value": int(bonus_match.group(1)), "target": bonus_match.group(2).strip(), "description": prop_cleaned})
            else: effects.append({"type": "narrative_property", "description": prop_cleaned})
    return effects if effects else [{"type": "narrative_property", "description": mtr_explanations(text_block)}]

def parse_accessory_type_code(code_str): 
    if not code_str: return "Unknown"
    cleaned_code_str = clean_value(code_str).strip()
    known_types_title_case = ["Armor Upgrade", "Weapon Upgrade (Ranged)", "Weapon Upgrade (Melee)", "Lightsaber Upgrade", "Universal Upgrade", "Cybernetic Prosthesis Upgrade", "Tools", "Medical Gear", "Survival Gear", "Communications Devices", "Detection and Surveillance Devices", "Computers and Storage Devices", "Weapon and Armor Accessories", "Life Support", "Cybernetics", "Implants", "Artifacts", "Biotech", "Droid Accessory", "Weapon Accessory"]
    if cleaned_code_str.title() in known_types_title_case: return cleaned_code_str.title() 
    code_upper = cleaned_code_str.upper()
    mapping = {'A': "Armor Upgrade", 'R': "Weapon Upgrade (Ranged)", 'M': "Weapon Upgrade (Melee)", 'L': "Lightsaber Upgrade", 'ANY': "Universal Upgrade", '*': "Cybernetic Prosthesis Upgrade", 'TOOL': "Tools", 'MED': "Medical Gear", 'SURV': "Survival Gear", 'COMM': "Communications Devices", 'DET': "Detection and Surveillance Devices", 'COMP': "Computers and Storage Devices", 'WPNACC': "Weapon and Armor Accessories", 'LIFE': "Life Support", 'CYB': "Cybernetics", 'IMP': "Implants", 'ART': "Artifacts", 'BIO': "Biotech", 'DROID': "Droid Accessory"}
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

def parse_availability_modification(availability_string):
    """Parses template availability modification string."""
    if not availability_string:
        return {"text_original": None, "set_to": None, "adds_traits": []}
    
    cleaned_avail = clean_value(availability_string)
    common_availabilities = ["Common", "Licensed", "Restricted", "Military", "Illegal", "Rare", "Unique", "Exotic"]
    if cleaned_avail.title() in common_availabilities:
        return {"text_original": cleaned_avail, "set_to": cleaned_avail.title(), "adds_traits": []}
    return {"text_original": cleaned_avail, "set_to": cleaned_avail, "adds_traits": []} 

def parse_template_effects_summary(effect_summary_string):
    """
    Parses the 'EFFECT' summary string from Templates into structured modifications.
    This is a heuristic parser for common patterns.
    """
    if not effect_summary_string: return []
    modifications = []
    parts = [p.strip() for p in effect_summary_string.split(';') if p.strip()]

    for part in parts:
        mod = {"text_description": part} 

        cl_match = re.match(r"CL\s*(\d+)%", part, re.IGNORECASE)
        if cl_match: mod.update({"target_stat": "CL", "change_type": "set_to_percentage_of_base", "value": float(cl_match.group(1)) / 100.0}); modifications.append(mod); continue
        
        hp_percent_match = re.match(r"(?:hp|hit points)\s*([+-])\s*(\d+)%", part, re.IGNORECASE)
        if hp_percent_match:
            sign = hp_percent_match.group(1); value = float(hp_percent_match.group(2)) / 100.0
            if sign == '-': value *= -1
            mod.update({"target_stat": "Hit Points", "change_type": "percentage_delta", "value": value}); modifications.append(mod); continue

        stat_fixed_match = re.match(r"([\w\s]+?)\s*([+-])\s*(\d+)(?!\s*%)", part, re.IGNORECASE) 
        if stat_fixed_match and "dc" not in stat_fixed_match.group(1).lower() and "repair" not in stat_fixed_match.group(1).lower():
            stat_name = stat_fixed_match.group(1).strip(); sign = stat_fixed_match.group(2); value = int(stat_fixed_match.group(3))
            change_type = "additive_amount" if sign == '+' else "subtractive_amount"
            if sign == '-': value = abs(value) 
            mod.update({"target_stat": stat_name.title(), "change_type": change_type, "value": value}); modifications.append(mod); continue
        
        weapon_dmg_match = re.match(r"Weapons?\s*\+\s*(\d+)\s*die(?: damage)?", part, re.IGNORECASE)
        if weapon_dmg_match: mod.update({"target_stat": "Weapon Damage", "change_type": "increase_dice_count", "value": int(weapon_dmg_match.group(1))}); modifications.append(mod); continue

        threshold_match = re.match(r"(?:TH|Threshold)\s*-\s*(\d+)%", part, re.IGNORECASE)
        if threshold_match: mod.update({"target_stat": "Damage Threshold", "change_type": "percentage_delta", "value": -float(threshold_match.group(1)) / 100.0}); modifications.append(mod); continue
            
        atk_bonus_match = re.match(r"(?:ATK Bonus|Attack Bonus)\s*-\s*(\d+)", part, re.IGNORECASE)
        if atk_bonus_match: mod.update({"target_stat": "Attack Bonus", "change_type": "subtractive_amount", "value": int(atk_bonus_match.group(1))}); modifications.append(mod); continue
            
        repairs_dc_match = re.match(r"Repairs\s*\+\s*(\d+)\s*DC", part, re.IGNORECASE)
        if repairs_dc_match: mod.update({"target_stat": "Repairs DC", "change_type": "modify_dc", "value": int(repairs_dc_match.group(1)), "skill": "Mechanics"}); modifications.append(mod); continue

        mod.update({"target_stat": "Unknown", "change_type": "text_rule"}); modifications.append(mod)
    return modifications

def parse_area_of_effect(burst_string):
    """Parses burst/area of effect strings for explosives."""
    if not burst_string: return {"text_original": None, "shape": None, "value_squares": None, "unit": "squares"}
    cleaned_burst = clean_value(burst_string); text_original = cleaned_burst
    shape = None; value_squares = None; unit = "squares" 
    match = re.match(r"(\d+)\s*sq(?:\s*(cone|burst|radius|line))?", cleaned_burst, re.IGNORECASE)
    if match:
        value_squares = int(match.group(1))
        if match.group(2): shape = match.group(2).lower()
        elif "cone" in cleaned_burst.lower(): shape = "cone"
        elif "burst" in cleaned_burst.lower() or "radius" in cleaned_burst.lower(): shape = "burst" 
        else: shape = "burst"
    elif "line" in cleaned_burst.lower(): 
        shape = "line"
        line_match = re.search(r"(\d+)\s*squares", cleaned_burst, re.IGNORECASE)
        if line_match: value_squares = int(line_match.group(1))
    return {"text_original": text_original, "shape": shape, "value_squares": value_squares, "unit": unit}

# --- 3. PROCESSING FUNCTIONS FOR EACH ITEM CSV TYPE --- 

def process_armor_csv(): 
    print("Processing Armor...")
    raw_data = read_csv_data(ARMOR_CSV_PATH)
    processed_armor_list = []
    if not raw_data: save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('ITEM', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', '')) 
        cost_raw = row.get('Cost', '') 
        if not name or not book or not page_raw: continue
        try: page_num = int(page_raw)
        except ValueError: continue
        desc_text = clean_value(row.get('Desc.', '')); armor_cat = parse_armor_category_from_desc(desc_text, name) 
        comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else [] 
        spd_6sq = clean_value(row.get('Spd 6sq', '')); spd_4sq = clean_value(row.get('Spd 4sq', '')); speed_penalty_text_parts = []
        if spd_6sq: speed_penalty_text_parts.append(f"6sq Base: {spd_6sq}")
        if spd_4sq: speed_penalty_text_parts.append(f"4sq Base: {spd_4sq}")
        helmet_p_val_cleaned = clean_value(row.get('Helmet P.', ''))
        armor_item = {"name": name, "cost": parse_complex_cost(cost_raw), "full_text_description": desc_text or None, "armor_category": armor_cat,
            "armor_check_penalty": attempt_numeric_conversion(clean_value(row.get('ACP', '')), name, 'ACP', 'Armor'),
            "reflex_defense_bonus": attempt_numeric_conversion(clean_value(row.get('Ref bonus', '')), name, 'Ref bonus', 'Armor'),
            "fortitude_defense_bonus": attempt_numeric_conversion(clean_value(row.get('Fort bonus', '')), name, 'Fort bonus', 'Armor'),
            "max_dex_bonus": attempt_numeric_conversion(clean_value(row.get('Max Dex', '')), name, 'Max Dex', 'Armor'),
            "speed_penalty_text": ", ".join(speed_penalty_text_parts) if speed_penalty_text_parts else None,
            "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Armor'),
            "availability": clean_value(row.get('Avail.', '')),
            "upgrade_slots_text": clean_value(row.get('U. Slots', '')) or None, 
            "has_helmet_package": helmet_p_val_cleaned.lower() == 'x' if isinstance(helmet_p_val_cleaned, str) else False,
            "special_properties_text": comments_text or None, "parsed_properties": parsed_props, 
            "skill_bonuses_text": f"Skill: {row.get('Skill','N/A')}, Bonus: {row.get('Skillbonus','N/A')}" if row.get('Skill') and row.get('Skill').strip() else None,
            "ability_bonuses_text": f"Ability: {row.get('Ability','N/A')}, Bonus: {row.get('Abilitybonus','N/A')}" if row.get('Ability') and row.get('Ability').strip() else None,
            "used_by_text": clean_value(row.get('Used By', '')) or None, "source_book": book, "page": page_num }
        processed_armor_list.append(armor_item)
    save_json_data(processed_armor_list, ARMOR_JSON_PATH, "Armor")

def process_melee_weapons_csv(): 
    print("Processing Melee Weapons...")
    raw_data = read_csv_data(MELEE_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('WEAPON', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        cost_raw = row.get('Cost','')
        if not name or not book or not page_raw: continue
        try: page_num = int(page_raw)
        except ValueError: continue
        proficiency_code = clean_value(row.get('Wpn Type', '')); damage_type_raw_text = clean_value(row.get('Dmg Type', ''))
        damage_types_list = parse_damage_types_string(damage_type_raw_text); damage_text = clean_value(row.get(' Damage', row.get('Damage',''))) 
        stun_text = clean_value(row.get('Stun', '')); comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else []
        weapon = {"name": name, "cost": parse_complex_cost(cost_raw), "full_text_description": clean_value(row.get('Desc.', '')) or None,
            "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=False), "size_category": parse_item_size_code(clean_value(row.get('Size', ''))),
            "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text), "stun_damage_text": stun_text or None,
            "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None,
            "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight','')), name, 'Weight', 'Melee'), "damage_types": damage_types_list,
            "availability": clean_value(row.get('Avail.', '')), "reach_or_thrown_info": clean_value(row.get('Thrown / Reach', '')) or None,
            "extra_cost_note": clean_value(row.get(' Extra cost', row.get('Extra cost',''))) or None,
            "build_dc_note": clean_value(row.get(' Build DC', row.get('Build DC',''))) or None,
            "special_properties_text": comments_text or None, "parsed_properties": parsed_props, "used_by_text": clean_value(row.get('Used by', '')) or None,
            "source_book": book, "page": page_num }
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, MELEE_WEAPONS_JSON_PATH, "Melee Weapons")

def process_ranged_weapons_csv(): 
    print("Processing Ranged Weapons...")
    raw_data = read_csv_data(RANGED_WEAPONS_CSV_PATH)
    processed_weapons = []
    if not raw_data: save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons"); return
    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('WEAPON', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        cost_raw = row.get('Cost','')
        if not name or not book or not page_raw: continue
        try: page_num = int(page_raw)
        except ValueError: continue
        proficiency_code = clean_value(row.get('Wpn Type', '')); damage_type_raw_text = clean_value(row.get('Dmg Type', ''))
        damage_types_list = parse_damage_types_string(damage_type_raw_text); damage_text = clean_value(row.get(' Damage', row.get('Damage','')))
        stun_text = clean_value(row.get('Stun', '')); comments_text = clean_value(row.get('COMMENTS', '')); parsed_props = parse_item_effects(comments_text) if comments_text else []
        classification_tags = []
        pistol_rifle_col = clean_value(row.get("Pistol\nRifle", row.get("Pistol", ''))); 
        if "pistol" in pistol_rifle_col.lower(): classification_tags.append("Pistol")
        if "rifle" in pistol_rifle_col.lower(): classification_tags.append("Rifle")
        if not pistol_rifle_col: 
            if clean_value(row.get("Pistol", '')): classification_tags.append("Pistol")
            if clean_value(row.get("Rifle", '')): classification_tags.append("Rifle")
        heavy_exotic_col = clean_value(row.get("Heavy\nExotic", row.get("Heavy",''))); 
        if "heavy" in heavy_exotic_col.lower(): classification_tags.append("Heavy Weapon")
        if "exotic" in heavy_exotic_col.lower(): classification_tags.append("Exotic Weapon")
        if not heavy_exotic_col:
            if clean_value(row.get("Heavy", '')): classification_tags.append("Heavy Weapon")
            if clean_value(row.get("Exotic", '')): classification_tags.append("Exotic Weapon")
        if clean_value(row.get("Simple", '') ): classification_tags.append("Simple Weapon")
        accurate_inaccurate_col = clean_value(row.get("Accurate\nInaccurate", row.get("Accurate", ''))); 
        if "accurate" in accurate_inaccurate_col.lower(): classification_tags.append("Accurate")
        if "inaccurate" in accurate_inaccurate_col.lower(): classification_tags.append("Inaccurate")
        if not accurate_inaccurate_col:
            if clean_value(row.get("Accurate", '')): classification_tags.append("Accurate")
            if clean_value(row.get("Inaccurate", '')): classification_tags.append("Inaccurate")
        classification_tags = sorted(list(set(t for t in classification_tags if t)))
        weapon = {"name": name, "cost": parse_complex_cost(cost_raw), "full_text_description": clean_value(row.get('Desc.', '')) or None,
            "weapon_category": parse_weapon_category_code(proficiency_code, is_ranged=True), "size_category": parse_item_size_code(clean_value(row.get('Size', ''))),
            "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text), "stun_damage_text": stun_text or None,
            "stun_damage_structured": parse_damage_string(stun_text) if stun_text else None,
            "rate_of_fire_text": clean_value(row.get('Fire Rate', '')), "rate_of_fire_structured": parse_rate_of_fire(clean_value(row.get('Fire Rate', ''))),
            "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight','')), name, 'Weight', 'Ranged'), "damage_types": damage_types_list,
            "availability": clean_value(row.get('Avail.', '')), "area_effect_text": clean_value(row.get('Area', '')) or None, 
            "ammunition_shots": attempt_numeric_conversion(clean_value(row.get('Shots','')), name, 'Shots', 'Ranged'),
            "ammunition_cost_text": clean_value(row.get(' Ammo Cost', row.get('Ammo Cost',''))) or None,
            "accuracy_note": clean_value(row.get(' Accuracy', row.get('Accuracy',''))) or None, 
            "special_properties_text": comments_text or None, "parsed_properties": parsed_props, "classification_tags": classification_tags,
            "used_by_text": clean_value(row.get('Used By', '')) or None, "source_book": book, "page": page_num }
        processed_weapons.append(weapon)
    save_json_data(processed_weapons, RANGED_WEAPONS_JSON_PATH, "Ranged Weapons")

def process_accessories_csv(): 
    print("Processing Accessories...")
    raw_data = read_csv_data(ACCESSORIES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories"); return
    for row in raw_data:
        name = clean_value(row.get('ACCESSORIES', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        cost_raw = row.get('Cost', '')
        if not name or not book or not page_raw: continue
        try: page_num = int(page_raw)
        except ValueError: continue
        desc_text = clean_value(row.get('Desc.', '')); comments_text = clean_value(row.get('COMMENTS', ''))
        parsed_effects = parse_item_effects(comments_text) if comments_text else [] 
        weight_text_raw = clean_value(row.get('Weight', '')); weight_kg = None
        if weight_text_raw:
            if "%" in weight_text_raw: weight_kg = None 
            else: weight_kg = attempt_numeric_conversion(weight_text_raw, name, 'Weight', 'Accessory')
        item = {"name": name, "cost": parse_complex_cost(cost_raw), "full_text_description": desc_text or None,
            "accessory_type_code": clean_value(row.get('Type', '')), "accessory_type_description": parse_accessory_type_code(clean_value(row.get('Type', ''))), 
            "upgrade_points_cost_text": clean_value(row.get('U. Points', '')) or None, "availability": clean_value(row.get('Avail.', '')),
            "weight_text": weight_text_raw or None, "weight_kg": weight_kg, "comments_and_effects_text": comments_text or None,
            "parsed_effects": parsed_effects, "source_book": book, "page": page_num }
        processed_items.append(item)
    save_json_data(processed_items, ACCESSORIES_JSON_PATH, "Accessories")

def process_defensive_items_csv(): 
    print("Processing Defensive Items (Mines, Emplacements)...")
    raw_data = read_csv_data(DEFENSES_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items"); return
    for row in raw_data:
        name = clean_value(row.get('WEAPON', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        cost_raw = row.get('Cost', '')
        if not name or not book or not page_raw: continue
        try: page_num = int(page_raw)
        except ValueError: continue
        damage_text = clean_value(row.get('Damage', '')); damage_type_raw_text = clean_value(row.get('Type', '')) 
        damage_types_list = parse_damage_types_string(damage_type_raw_text); comments_text = clean_value(row.get('COMMENTS', ''))
        parsed_effects = parse_item_effects(comments_text) if comments_text else []
        delay_key = "Delay\n(rounds)" if "Delay\n(rounds)" in row else "Delay"; delay_text = clean_value(row.get(delay_key, ''))
        item = {"name": name, "cost": parse_complex_cost(cost_raw), "damage_text": damage_text, "damage_structured": parse_damage_string(damage_text),
            "damage_types": damage_types_list, "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Defensive Item'),
            "perception_dc_to_detect": attempt_numeric_conversion(clean_value(row.get('Perception', '')), name, 'Perception DC', 'Defensive Item'),
            "availability": clean_value(row.get('Avail.', '')), "splash_radius_text": clean_value(row.get('Splash', '')) or None, 
            "delay_rounds_text": delay_text or None, "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects,
            "source_book": book, "page": page_num }
        processed_items.append(item)
    save_json_data(processed_items, DEFENSIVE_ITEMS_JSON_PATH, "Defensive Items")

def process_equipment_general_csv(): 
    print("Processing General Equipment...")
    raw_data = read_csv_data(EQUIPMENT_CSV_PATH)
    processed_items = []
    if not raw_data: save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment"); return
    for idx, row in enumerate(raw_data): 
        name = clean_value(row.get('ITEM', '')); book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        cost_raw = row.get('Cost', '')
        if not name or not book or not page_raw or (page_raw and not re.match(r"^\d+(-?\d*)?$", page_raw)): continue
        desc_text = clean_value(row.get('Desc.', '')); comments_text = clean_value(row.get('COMMENTS', ''))
        parsed_effects = parse_item_effects(comments_text) if comments_text else []
        item = {"name": name, "cost": parse_complex_cost(cost_raw), "full_text_description": desc_text or None,
            "equipment_category_code": clean_value(row.get('TYPE', '')), "equipment_category_description": parse_accessory_type_code(clean_value(row.get('TYPE', ''))), 
            "weight_kg": attempt_numeric_conversion(clean_value(row.get('Weight', '')), name, 'Weight', 'Equipment'),
            "uses_text": clean_value(row.get('Uses', '')) or None, "use_cost_text": clean_value(row.get(' Use Cost', row.get('Use Cost', ''))) or None, 
            "comments_and_effects_text": comments_text or None, "parsed_effects": parsed_effects, "source_book": book, "page": str(page_raw) }
        processed_items.append(item)
    save_json_data(processed_items, EQUIPMENT_JSON_PATH, "General Equipment")

def process_techspec_csv(): 
    print("Processing Tech Specialist Upgrades...")
    raw_data = read_csv_data(TECHSPEC_CSV_PATH) 
    processed_tech_upgrades = []
    if not raw_data: save_json_data(processed_tech_upgrades, TECHSPEC_JSON_PATH, "Tech Specialist Upgrades"); return
    for row_idx, row in enumerate(raw_data):
        name = clean_value(row.get('TRAIT', '')); source_book = clean_value(row.get('BOOK', '')); page_raw = clean_value(row.get('PAGE', ''))
        if not name or not source_book or not page_raw:
            print(f"Warning (TechSpec): Skipping row {row_idx + 2} due to missing Name/TRAIT, Book, or Page. Name: '{name}'"); continue
        try: page_num = int(page_raw)
        except ValueError: print(f"Warning (TechSpec): Invalid page number '{page_raw}' for '{name}'. Skipping."); continue
        target_item_type = clean_value(row.get('Type', '')); cost_text_original = row.get('Cost', '') 
        prereq_text_original = clean_value(row.get('Feat', '')); effect_text_original = mtr_explanations(clean_value(row.get('COMMENTS', ''))) 
        parsed_cost_obj = parse_complex_cost(cost_text_original) 
        parsed_prerequisites_list = parse_prerequisites_structured(prereq_text_original)
        parsed_effects_list = parse_effects_structured(effect_text_original, context_skill="Tech Specialist Upgrade") 
        tech_upgrade_item = {"name": name, "target_item_type": target_item_type, "cost": parsed_cost_obj, 
            "prerequisites_text": prereq_text_original if prereq_text_original else None, "prerequisites_structured": parsed_prerequisites_list, 
            "effect_description": effect_text_original, "structured_effects": parsed_effects_list, 
            "source_book": source_book, "page": page_num }
        processed_tech_upgrades.append(tech_upgrade_item)
    save_json_data(processed_tech_upgrades, TECHSPEC_JSON_PATH, "Tech Specialist Upgrades")

# --- NEW PROCESSING FUNCTIONS for Templates and Explosives ---

def process_templates_csv():
    print("Processing Templates...")
    raw_data = read_csv_data(TEMPLATES_CSV_PATH, known_delimiter=',') # Explicitly set delimiter
    processed_templates = []
    if not raw_data:
        save_json_data(processed_templates, TEMPLATES_JSON_PATH, "Templates")
        return

    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('TEMPLATE', ''))
        book = clean_value(row.get('BOOK', ''))
        page_raw = clean_value(row.get('PAGE', ''))

        # More robust check for critical fields
        if not name or not name.strip() or \
           not book or not book.strip() or \
           not page_raw or not page_raw.strip() or \
           not re.fullmatch(r"\d+", page_raw.strip()): # Ensure page_raw is only digits
            print(f"Warning (Templates): Skipping row {idx + 2} due to missing/invalid critical fields. Name: '{name}', Book: '{book}', Page: '{page_raw}'")
            continue
        try:
            page_num = int(page_raw.strip())
        except ValueError: # Should be caught by regex, but as a backup
            print(f"Warning (Templates): Invalid page number '{page_raw}' for '{name}' (ValueError). Skipping.")
            continue
        
        applies_to_type = clean_value(row.get('TYPE', ''))
        full_text_description = clean_value(row.get('Desc.', '')) 
        modifications_summary_text = clean_value(row.get('EFFECT', ''))
        cost_modification_raw = row.get('PRICE', '') 
        availability_raw = clean_value(row.get('AVAILABILITY', ''))

        parsed_cost_modification = parse_complex_cost(cost_modification_raw)
        parsed_availability_modification = parse_availability_modification(availability_raw)
        parsed_structured_modifications = parse_template_effects_summary(modifications_summary_text)
        # Optionally, parse full_text_description for more detailed structured_modifications if summary is insufficient
        # This would require a much more complex parser. For now, summary is primary.

        template_item = {
            "name": name,
            "applies_to_type": applies_to_type or None,
            "full_text_description": full_text_description or None,
            "modifications_summary_text": modifications_summary_text or None,
            "cost_modification": parsed_cost_modification,
            "availability_modification": parsed_availability_modification,
            "structured_modifications": parsed_structured_modifications,
            "source_book": book,
            "page": page_num
        }
        processed_templates.append(template_item)
    
    save_json_data(processed_templates, TEMPLATES_JSON_PATH, "Templates")

def process_explosives_csv():
    print("Processing Explosives...")
    raw_data = read_csv_data(EXPLOSIVES_CSV_PATH, known_delimiter=',') # Explicitly set delimiter
    processed_explosives = []
    if not raw_data:
        save_json_data(processed_explosives, EXPLOSIVES_JSON_PATH, "Explosives")
        return

    for idx, row in enumerate(raw_data):
        name = clean_value(row.get('WEAPON', '')) 
        book = clean_value(row.get('BOOK', ''))
        page_raw = clean_value(row.get('PAGE', ''))

        if not name or not name.strip() or \
           not book or not book.strip() or \
           not page_raw or not page_raw.strip() or \
           not re.fullmatch(r"\d+", page_raw.strip()):
            print(f"Warning (Explosives): Skipping row {idx + 2} due to missing/invalid critical fields. Name: '{name}', Book: '{book}', Page: '{page_raw}'")
            continue
        try:
            page_num = int(page_raw.strip())
        except ValueError:
            print(f"Warning (Explosives): Invalid page number '{page_raw}' for '{name}' (ValueError). Skipping.")
            continue

        web_marker = clean_value(row.get('WEB', ''))
        full_text_description = clean_value(row.get('Desc.', ''))
        cost_raw = row.get('Cost', '')
        damage_text = clean_value(row.get('Damage', ''))
        damage_type_raw = clean_value(row.get('Type', ''))
        weight_raw = clean_value(row.get('Weight', ''))
        size_code = clean_value(row.get('Size', ''))
        perception_dc_raw = clean_value(row.get('Perception DC', ''))
        availability_raw = clean_value(row.get('Avail.', ''))
        burst_text_raw = clean_value(row.get('Burst', ''))
        comments_text = mtr_explanations(clean_value(row.get('COMMENTS', '')))

        parsed_cost = parse_complex_cost(cost_raw)
        parsed_damage_structured = parse_damage_string(damage_text)
        parsed_damage_types = parse_damage_types_string(damage_type_raw)
        parsed_weight_kg = attempt_numeric_conversion(weight_raw, name, 'Weight', 'Explosive')
        parsed_size_category = parse_item_size_code(size_code)
        parsed_perception_dc = attempt_numeric_conversion(perception_dc_raw, name, 'Perception DC', 'Explosive')
        parsed_area_of_effect = parse_area_of_effect(burst_text_raw)
        parsed_structured_effects = parse_effects_structured(comments_text, context_skill="Explosive Effect")


        explosive_item = {
            "name": name,
            "web_marker": web_marker or None,
            "full_text_description": full_text_description or None,
            "cost": parsed_cost,
            "damage_text": damage_text or None,
            "damage_structured": parsed_damage_structured,
            "damage_types": parsed_damage_types,
            "weight_kg": parsed_weight_kg,
            "size_category": parsed_size_category,
            "perception_dc_to_detect": parsed_perception_dc,
            "availability": availability_raw or None,
            "area_of_effect": parsed_area_of_effect,
            "special_properties_text": comments_text or None, 
            "structured_effects": parsed_structured_effects,
            "source_book": book,
            "page": page_num
        }
        processed_explosives.append(explosive_item)

    save_json_data(processed_explosives, EXPLOSIVES_JSON_PATH, "Explosives")


# --- 4. MAIN EXECUTION ---
if __name__ == '__main__':
    print("Starting SAGA Index Elements CSV to JSON Conversion Process...\n")
    if PROCESS_CONFIG.get("armor", False): process_armor_csv()
    if PROCESS_CONFIG.get("melee_weapons", False): process_melee_weapons_csv()
    if PROCESS_CONFIG.get("ranged_weapons", False): process_ranged_weapons_csv()
    if PROCESS_CONFIG.get("accessories", False): process_accessories_csv()
    if PROCESS_CONFIG.get("defensive_items", False): process_defensive_items_csv()
    if PROCESS_CONFIG.get("equipment_general", False): process_equipment_general_csv()
    if PROCESS_CONFIG.get("tech_specialist_upgrades", False): process_techspec_csv()
    if PROCESS_CONFIG.get("templates", False): process_templates_csv()
    if PROCESS_CONFIG.get("explosives", False): process_explosives_csv()
    
    print("\nConfigured item/index element CSV processing complete.")

