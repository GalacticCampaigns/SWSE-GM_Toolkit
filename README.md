# Star Wars SAGA Edition - Structured JSON Data Repository

## Project Goal

The primary goal of this project is to convert the comprehensive "SAGA Character Index version 4.0" (and potentially other SAGA Edition resources) from its original CSV-like format into a structured, machine-readable JSON database. This database is intended to serve as a knowledge base for applications, particularly a Game Master AI, to reference and utilize Star Wars SAGA Edition RPG rules and content.

## Data Source

The initial and primary data source for this repository is the **SAGA Character Index version 4.0**, originally compiled by Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM). Future additions may incorporate data from other SAGA Edition sourcebooks.

All content is derived from the official Star Wars SAGA Edition rulebooks published by Wizards of the Coast. This repository is a fan-made project and is not affiliated with or endorsed by Wizards of the Coast or Lucasfilm Ltd.

## Current Status

*Work in Progress*

Currently, the focus is on converting core character creation elements, starting with:
* Species & Traits
* (Future sections: Feats, Talents, Skills, Classes, Equipment, etc.)

## Repository Structure

The repository is organized as follows:

saga_rpg_data_repository/├── README.md                 # This file: Project overview and guidelines│├── schemas/                  # JSON Schema files to define and validate data structures│   ├── species.schema.json│   └── (more schemas to be added for feats, items, etc.)│├── data/                     # Root directory for all JSON data files│   ││   ├── meta_info/            # General metadata about the dataset│   │   ├── source_books.json   # Abbreviations and full names of sourcebooks│   │   └── (game_definitions.json - planned for common terms)│   ││   ├── character_elements/│   │   └── species.json          # Structured data for playable species and their traits│   │   └── (feats.json - planned)│   │   └── (talents.json - planned)│   │   └── (skills.json - planned)│   │   └── (classes.json - planned)│   │   └── (force_powers.json - planned)│   ││   └── item_elements/│       └── (weapons.json - planned)│       └── (armor.json - planned)│       └── (equipment_general.json - planned)│       └── (more item categories - planned)│└── scripts/                  # Python scripts used for data conversion and validation└── species_saga_csv_to_json.py # Script for converting Species & Traits CSV to JSON└── (other_conversion_scripts - planned)
## Data Format

All data is stored in JSON format. Key considerations include:

* **Naming Convention:** All JSON keys use `snake_case` (e.g., `ability_modifiers`, `source_book`).
* **Structured Data:** Information is broken down into logical components. For example:
    * Ability modifiers: `{"ability": "Dexterity", "value": 2}`
    * Damage (planned): `{"dice_count": 2, "die_type": 10, "type": "slashing"}`
* **Source Information:** Each significant data entry (e.g., a species, a feat) includes `source_book` (using abbreviations defined in `data/meta_info/source_books.json`) and `page` number.
* **Special Qualities/Traits Effects (Work in Progress):** For elements like species traits, feats, and talents, an `effects` array is being incorporated to provide a more structured representation of game mechanics for easier AI processing, alongside the full textual description. Example:
    ```json
    "special_qualities": [
        {
            "name": "Natural Armor",
            "description": "You gain a +1 natural armor bonus to your Reflex Defense",
            "effects": [
                {"type": "defense_bonus", "defense": "Reflex", "bonus_type": "natural_armor", "value": 1}
            ]
        }
    ]
    ```
* **No Wookieepedia Links:** Wookieepedia links or their types (w, u, etc.) are generally excluded unless a direct, usable hyperlink URL is present in the original source text.

## How to Use the Data

This data can be used for various purposes:

* **GM AI Development:** As a primary knowledge base for an AI designed to assist with or run SAGA Edition games.
* **Character Builders:** To power applications that help players create and manage SAGA Edition characters.
* **Digital Compendiums:** For creating searchable and filterable references for SAGA Edition rules.
* **Game Aids:** To develop tools that automate certain aspects of gameplay.

Applications will typically need to parse the JSON files. The `schemas/` directory will provide formal definitions for these structures to aid in parsing and validation.

## Scripts

The `scripts/` directory contains Python scripts used in the conversion process. Currently, this includes:
* `species_saga_csv_to_json.py`: Converts the Species and Traits data from the SAGA Character Index CSV files into the `species.json` format.

## Schemas

The `schemas/` directory is intended to house JSON Schema files. These schemas will define the structure for each type of data object (e.g., species, feats, items). Using schemas helps ensure data consistency and provides a clear contract for applications consuming this data.
* `species.schema.json` is the first schema being developed.

## Contributing (Placeholder)

*(This section can be expanded if you plan to accept contributions from others.)*

Currently, this project is primarily a personal endeavor. If you are interested in contributing in the future, please [mention how to get in touch or what the process might be].

## Disclaimer

This project is a fan-created resource for the Star Wars SAGA Edition roleplaying game. Star Wars, SAGA Edition, and all associated marks and characters are trademarks of Lucasfilm Ltd. and/or Wizards of the Coast. This project is not affiliated with, endorsed, sponsored, or specifically approved by Lucasfilm Ltd. or Wizards of the Coast.

The data is compiled from publicly available fan-created indexes and official rulebooks for personal use and to facilitate gameplay. Please support the official releases.

## Acknowledgements

* **Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM)** for their incredible work on the SAGA Character Index v4.0, which forms the foundation of this dataset.
* The broader Star Wars SAGA Edition community for their continued passion and resources.

---

*This README is a living document and will be updated as the project progresses.*
Key things I've included based on our discussions:Project Goal: Clearly states the aim of creating a JSON database for a GM AI.Data Source: Credits the original SAGA Index creators.Repository Structure: Reflects the detailed structure we planned.Data Format: Highlights snake_case, structured data examples, source info, and the new effects array for special qualities.How to Use: Suggests potential applications.Scripts & Schemas: Mentions their purpose and current status.Disclaimer & Acknowledgements: Important for a fan project.To use this:Create a file named README.md in the root of your GitHub repository.Copy the content above and paste it into that file.Commit and push the README.md file to your GitHub repository.You can then edit and expand this README directly on GitHub or in your local clone as your project grows.# SagaIndex
