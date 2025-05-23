# Star Wars SAGA Edition - Structured JSON Data Repository

## Project Goal

The primary goal of this project is to convert the comprehensive "SAGA Character Index version 4.0" (and potentially other SAGA Edition resources) from its original CSV-like format into a structured, machine-readable JSON database. This database is intended to serve as a knowledge base for applications, particularly a Game Master AI, to reference and utilize Star Wars SAGA Edition RPG rules and content.

## Data Source

The initial and primary data source for this repository is the **SAGA Character Index version 4.0**, originally compiled by Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM). Future additions may incorporate data from other SAGA Edition sourcebooks.

All content is derived from the official Star Wars SAGA Edition rulebooks published by Wizards of the Coast. This repository is a fan-made project and is not affiliated with or endorsed by Wizards of the Coast or Lucasfilm Ltd.

## Current Status

*Work in Progress*

Conversion and structuring efforts are ongoing for various game elements.

## Repository Structure

The repository is organized as follows (root path: `D:\OneDrive\Documents\GitHub\SagaIndex\`):

SagaIndex/
├── README.md                 # This file: Project overview and guidelines
│├── schemas/                  # JSON Schema files to define and validate data structures
│   ├── species.schema.json
│   ├── skills.schema.json
│   ├── feats.schema.json
│   ├── talents.schema.json
│   ├── force_techniques.schema.json
│   ├── force_secrets.schema.json
│   ├── training_regimens.schema.json
│   ├── force_powers.schema.json      # New
│   ├── prestige_classes.schema.json  # New
│   └── (more schemas to be added)
│├── data/                     # Root directory for all JSON data files
│   ││   ├── meta_info/            # General metadata about the dataset
│   │   ├── source_books.json   # Abbreviations and full names of sourcebooks
│   │   └── (game_definitions.json - planned for common terms)
│   ││   ├── character_elements/
│   │   ├── species.json
│   │   ├── skills.json
│   │   ├── feats.json
│   │   ├── talents.json
│   │   ├── force_techniques.json
│   │   ├── force_secrets.json
│   │   ├── training_regimens.json
│   │   ├── force_powers.json         # New
│   │   ├── prestige_classes.json     # New
│   │   └── (classes.json - planned for base classes)
│   ││   └── index_elements/        # For equipment, weapons, vehicles, etc.
│       ├── starship_maneuvers.json
│       └── (weapons.json - planned)
│       └── (armor.json - planned)
│       └── (equipment_general.json - planned)
│└── scripts/                  # Python scripts used for data conversion and validation
├── csv/                  # Source CSV files are expected here
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
│   ├── Character-ForcePowers.csv     # New
│   └── Character-Prestige.csv        # New
└── saga_multi_csv_converter_v4.py  # Main conversion script
└── (char_creation_csv_to_json.py - For the Character Creation PDF/CSV)
## Data Format

All data is stored in JSON format. Key considerations include:

* **Naming Convention:** All JSON keys use `snake_case`.
* **Structured Data:** Information is broken down into logical components.
* **Source Information:** Each significant data entry includes `source_book` and `page`.
* **Structured Effects:** For elements like species traits, feats, talents, and powers, an `effects` array provides a structured representation of game mechanics alongside the full textual description. This includes parsing for DC progressions.
* **Structured Prerequisites:** Prerequisites are parsed into a structured list where possible, in addition to preserving the original text.

## How to Use the Data

This data can be used for:
* GM AI Development
* Character Builders
* Digital Compendiums
* Game Aids

Applications will parse the JSON files. The `schemas/` directory provides formal definitions.

## Scripts

The `scripts/` directory contains Python scripts for conversion.
* **Source CSVs:** Place source CSVs into `scripts/csv/`.
* **Main Script:** `saga_multi_csv_converter_v4.py` processes most game elements.
* `char_creation_csv_to_json.py` is intended for the specific Character Creation rules CSV.

## Schemas

The `schemas/` directory houses JSON Schema files for data validation and structure definition.

## Contributing (Placeholder)

*(This section can be expanded if you plan to accept contributions from others.)*

## Disclaimer

This project is a fan-created resource. Star Wars, SAGA Edition are trademarks of Lucasfilm Ltd. and/or Wizards of the Coast. This project is not affiliated with, endorsed, sponsored, or approved by Lucasfilm Ltd. or Wizards of the Coast. Please support official releases.

## Acknowledgements

* **Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM)** for the SAGA Character Index v4.0.
* The Star Wars SAGA Edition community.

---

*This README is a living document and will be updated as the project progresses.*
