# Star Wars SAGA Edition - Structured JSON Data Repository

## Project Goal

The primary goal of this project is to convert comprehensive SAGA Edition resources, including the "SAGA Character Index version 4.0" and various item/equipment lists, from their original CSV-like formats into a structured, machine-readable JSON database. This database is intended to serve as a knowledge base for applications, particularly a Game Master AI, to reference and utilize Star Wars SAGA Edition RPG rules and content.

## Data Source

The initial and primary data sources for this repository are:
1.  The **SAGA Character Index version 4.0**, originally compiled by Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM).
2.  Various SAGA Edition index files covering equipment, weapons, armor, and other game elements.

Future additions may incorporate data from other SAGA Edition sourcebooks.

All content is derived from the official Star Wars SAGA Edition rulebooks published by Wizards of the Coast. This repository is a fan-made project and is not affiliated with or endorsed by Wizards of the Coast or Lucasfilm Ltd.

## Current Status

*Work in Progress*

Conversion and structuring efforts are ongoing. Two main Python scripts are in development:
* One for processing **character-related elements** (Species, Skills, Feats, Talents, Force Powers, Prestige Classes, etc.).
* One for processing **item and index-related elements** (Armor, Weapons, Equipment, Tech Upgrades, Templates, Explosives, Vehicles, Starships, etc.).

Several categories for both character and item elements have been successfully processed, and JSON schemas are being created and refined for each.

## Repository Structure

The repository is organized as follows:
```
SagaIndex/
├── README.md                     # This file: Project overview and guidelines
├── schemas/                      # JSON Schema files for data validation
│   ├── species.schema.json
│   ├── skills.schema.json
│   ├── feats.schema.json
│   ├── talents.schema.json
│   ├── force_techniques.schema.json
│   ├── force_secrets.schema.json
│   ├── training_regimens.schema.json
│   ├── force_powers.schema.json
│   ├── prestige_classes.schema.json
│   ├── armor.schema.json
│   ├── melee_weapons.schema.json
│   ├── ranged_weapons.schema.json
│   ├── accessories.schema.json
│   ├── defensive_items.schema.json
│   ├── equipment_general.schema.json
│   ├── tech_specialist_upgrades.schema.json
│   ├── templates.schema.json         # Planned
│   ├── explosives.schema.json        # Planned
│   └── ... (more schemas to be added for vehicles, starships, etc.)
├── data/
│   ├── meta_info/
│   │   └── source_books.json         # Abbreviations and full names of sourcebooks
│   │   └── (game_definitions.json - planned for common terms)
│   ├── character_elements/           # Data for character creation and progression
│   │   ├── species.json
│   │   ├── skills.json
│   │   ├── feats.json
│   │   ├── talents.json
│   │   ├── force_techniques.json
│   │   ├── force_secrets.json
│   │   ├── training_regimens.json
│   │   ├── force_powers.json
│   │   └── prestige_classes.json
│   │   └── (classes.json - planned for base classes)
│   └── index_elements/               # Data for items, equipment, vehicles, etc.
│       ├── starship_maneuvers.json
│       ├── armor.json
│       ├── melee_weapons.json
│       ├── ranged_weapons.json
│       ├── accessories.json
│       ├── defensive_items.json
│       ├── equipment_general.json
│       ├── tech_specialist_upgrades.json
│       ├── templates.json            # Planned
│       ├── explosives.json           # Planned
│       └── ... (more item/vehicle/starship JSONs to be added)
└── scripts/
├── csv/                          # Source CSV files are expected here
│   ├── Character-Species.csv
│   ├── Character-Traits.csv
│   ├── Character-Skills.csv
│   ├── Character-Skill uses 1.8.csv
│   ├── Character-Use.csv
│   ├── Character-Feats.csv
│   ├── Character-Talents.csv
│   ├── Character-Techniques.csv
│   ├── Character-Secrets.csv
│   ├── Character-Regimens.csv
│   ├── Character-Starship Maneuvers.csv
│   ├── Character-ForcePowers.csv
│   ├── Character-Prestige.csv
│   ├── Index-Armor.csv
│   ├── Index-Melee.csv
│   ├── Index-Ranged.csv
│   ├── Index-Accessories.csv
│   ├── Index-Defenses.csv
│   ├── Index-Equipment.csv
│   ├── Index-TechSpec.csv
│   ├── Index-Templates.csv
│   ├── Index-Explosives.csv
│   └── ... (more CSVs for vehicles, starships, etc.)
├── saga_multi_csv_converter_v4.py    # Conversion script for character elements
├── saga_index_elements_converter_v1.py # Conversion script for item/index elements
└── (char_creation_csv_to_json.py - For the Character Creation PDF/CSV, if pursued)
```
## Data Format

All data is stored in JSON format. Key considerations include:

* **Naming Convention:** All JSON keys use `snake_case`.
* **Structured Data:** Information is broken down into logical components.
* **Source Information:** Each significant data entry includes `source_book` (abbreviation) and `page` number.
* **Structured Effects:** For elements like species traits, feats, talents, powers, and item special properties, an `effects` (or `structured_effects`) array aims to provide a structured representation of game mechanics alongside the full textual description. This includes parsing for DC progressions where applicable.
* **Structured Prerequisites:** Prerequisites are parsed into a structured list (e.g., `prerequisites_structured`) where possible, in addition to preserving the original text.
* **Unified Cost Object:** For all items with a cost, a `cost` object provides a consistent structure. This object includes the `text_original` from the CSV and an `options` array detailing parsed cost components (e.g., `fixed_amount`, `percentage_of_item_value`, `base_item_multiplier`, `additive_amount`, `percentage_delta`, `set_to_percentage_of_base`, `text_description`) and any `selection_logic` (e.g., `whichever_is_more`).

## How to Use the Data

This data can be used for:
* Game Master AI Development
* Digital Character Builders and Sheets
* Online SAGA Edition Compendiums
* Custom Game Aids and Tools

Applications will typically parse the relevant JSON files. The `schemas/` directory provides formal JSON Schema definitions which can be used for validation and understanding the data structure.

## Scripts

The `scripts/` directory contains Python scripts used for data conversion.

* **Source CSVs:** Place all source CSV files into the `scripts/csv/` subdirectory.
* **Main Conversion Scripts:**
    * `saga_multi_csv_converter_v4.py`: Processes character-related elements (species, feats, talents, etc.).
    * `saga_index_elements_converter_v1.py`: Processes item and index-related elements (armor, weapons, equipment, tech upgrades, etc.).
* **Configuration:** Both scripts contain a `PROCESS_CONFIG` dictionary at the top, allowing selective processing of different CSV files by setting their respective flags to `True` or `False`.
* **Path Configuration:** Ensure the `LOCAL_ROOT_PATH` variable at the top of each script correctly points to the root of your `SagaIndex` repository.

## Schemas

The `schemas/` directory houses JSON Schema files. These files formally define the expected structure, data types, and constraints for each generated JSON data file, aiding in validation and data integrity.

## Contributing (Placeholder)

*(This section can be expanded if the project aims to accept contributions from others, detailing guidelines for CSV formatting, script updates, schema creation, and pull requests.)*

## Disclaimer

This project is a fan-created resource intended for personal use and to facilitate playing Star Wars SAGA Edition. Star Wars, SAGA Edition, and all associated properties are trademarks of Lucasfilm Ltd. and/or Wizards of the Coast (a subsidiary of Hasbro). This project is not affiliated with, endorsed, sponsored, or approved by Lucasfilm Ltd., Wizards of the Coast, or Hasbro. Please support official Star Wars SAGA Edition releases.

## Acknowledgements

* **Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM)** for their monumental work on the SAGA Character Index v4.0, which forms a significant basis for the character elements in this project.
* The wider Star Wars SAGA Edition community for their continued passion and creation of resources for the game.

---

*This README is a living document and will be updated as the project progresses and new data categories are integrated.*
