# SWSE AI Gamemaster Toolkit

This repository is a comprehensive toolkit and structured data resource for powering an AI Gamemaster (AI GM) for the Star Wars Saga Edition roleplaying game. It aims to provide a detailed, machine-readable, and community-vetted representation of game rules, lore, and entities from the Core Rulebook and various supplements.

Beyond a simple index, this project includes:
* **Structured Game Data:** JSON files detailing abilities, skills, species, feats, Force powers, talents, heroic classes, prestige classes, combat mechanics, equipment, vehicles, droids, hazards, and more. These are designed for easy parsing and use by AI systems.
* **Core Rule Definitions:** Centralized JSON files for fundamental game mechanics, system rules, and glossaries.
* **Lore Archives:** Organized lore information, such as era descriptions, Force traditions, etc., to enrich AI storytelling.
* **Gamemaster Resources:** Principles and guidelines for adventure design, campaign management, and encounter building.
* **Schemas & Validation:** JSON schemas to ensure data integrity and consistency.
* **Tools & Utilities:** Scripts and instructions for maintaining and utilizing the dataset, such as the `json_updater.py` for applying batch edits.
* **Guidance Documents:** Instructions for contributing, formatting data (like NPC profiles), and understanding the project's current state.

The goal is to create a robust foundation that can be used to develop intelligent GM tools, AI-driven narratives, and other applications for enhancing the Star Wars Saga Edition experience.

## Project Overview

The SWSE AI Gamemaster Toolkit is an open-source initiative to systematically digitize the rules and content of the Star Wars Saga Edition RPG. By converting the game's elements into a structured, machine-readable format (primarily JSON), we aim to:
* Enable the development of sophisticated AI Gamemaster applications.
* Provide a comprehensive and easily searchable database for players and GMs.
* Facilitate the creation of third-party tools and utilities for the Saga Edition system.
* Preserve and make accessible the rich content of this beloved game.

This project emphasizes accuracy, with data derived directly from official sourcebooks and errata, and clarity, through well-defined JSON schemas and consistent data structures.

## Features

* **Comprehensive Data Sets:** Covering a wide array of game elements:
    * Character Elements: Abilities, Skills, Species, Feats, Talents, Heroic Classes, Prestige Classes.
    * Force Elements: Force Powers, Force Talents, Force Techniques, Force Secrets, Force Traditions.
    * Index Elements: Equipment (Weapons, Armor, Accessories, Explosives, General Gear), Vehicles (Planetary), Starships, Droids (Chassis, Systems), Templates, Defensive Items, Hazards.
    * Combat Mechanics and detailed game rules.
* **Structured Core Rules:** General game mechanics, system definitions, and glossaries stored in dedicated JSON files within `data/core_rules/` and `data/meta_info/` (e.g., `ability_system_rules.json`, `skill_rules.json`, `combat_rules.json`, `environmental_rules.json`, `encounter_building_rules.json`).
* **Gamemaster Resources:** Principles and guidelines for adventure design, campaign management, and narrative structure stored in `data/gamemaster_resources/`.
* **Rich Lore Information:** Contextual lore for eras, Force traditions, and other aspects of the Star Wars universe, located in the `data/lore/` directory.
* **JSON Schemas:** Validation schemas in the `schemas/` directory to ensure data consistency and integrity across all JSON files.
* **Automated Update Tool:** A Python script (`scripts/apps/json_updater.py`) designed to apply batch edits to the JSON data files, ensuring accurate and efficient maintenance. 
* **Detailed Documentation:**
    * This README file.
    * Instructions for using the `json_updater.py` script (see "Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles" in the `docs/` folder).
    * Guidelines for data formatting (e.g., NPC Profile JSON structure - see "Instructions for AI: Generating and Maintaining Character Profile JSON").
    * Summaries of the project's current processing state.

## Repository Structure

The repository is organized as follows:

* **`data/`**: Contains all the structured JSON data.
    * **`character_elements/`**: Core data for player/character building blocks (e.g., `abilities.json`, `skills.json`, `species.json`, `feats.json`, `talents.json`, `classes.json`, `prestige_classes.json`, `droid_chassis.json`).
    * **`index_elements/`**: Data for game items and entities (e.g., `equipment_general.json`, `ranged_weapons.json`, `vehicles.json`, `starships.json`, `droid_systems.json`, `hazards.json`, `templates.json`).
    * **`core_rules/`**: JSON files for general system rules (e.g., `ability_system_rules.json`, `skill_rules.json`, `combat_rules.json`, `droid_rules.json`, `environmental_rules.json`, `encounter_building_rules.json`, `prestige_classes_rules.json`).
    * **`gamemaster_resources/`**: JSON files containing principles and guidelines for GMs/AI GM (e.g., `adventure_design_principles.json`, `campaign_management_principles.json`).
    * **`meta_info/`**: Supporting metadata files (e.g., `source_books.json`, `game_definitions.json`, `abbreviations_glossary.json`).
    * **`lore/`**: Files containing narrative and contextual information (e.g., `eras_overview.json`, `force_traditions_lore.json`).
* **`schemas/`**: Contains JSON schemas used for validating the data files (e.g., `starships.schema.json`, `droid_rules.schema.json`).
* **`scripts/`**: Contains utility scripts, including:
    * `apps/`: Python scripts like `json_updater.py` and various CSV to JSON converters.
    * `csv/`: Source CSV files used for initial data population.
    * `txt/`: Source text files like `CoreRulebook.v2.txt`.
* **`docs/`**: Contains detailed instructions for JSON updating, data entry guidelines, and project documentation.

## Getting Started / How to Use

1.  **Clone the Repository:**
    ```bash
    git clone [URL_to_your_repository]
    ```
2.  **Explore the Data:** Navigate the `data/` directory to find the JSON files relevant to your needs. Refer to the schemas in the `schemas/` directory for understanding the structure of each file.
3.  **Using the `json_updater.py` Script:**
    * This script is likely located in the `scripts/apps/` directory.
    * It processes edit request files (formatted as JSON arrays of update/add/remove actions) to modify the data files. 
    * Refer to "Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles" (available in `docs/`) for detailed instructions on formatting edit requests and running the script.

## Data Format & Schemas

* All game data is structured in JSON format.
* Field names within the JSON objects consistently use `snake_case`.
* All primary data files (e.g., `species.json`, `feats.json`, rule files like `combat_rules.json`) should have a single top-level key named using the pattern: `{filename_base}_data` (e.g., `species_data`, `combat_rules_data`).
* For list-based files, the `*_data` object must contain a key named `{filename_base}_list` (e.g., `species_list`), the value of which is an array of individual record objects.
* Each individual record within list-based files must have a unique `"id"` field as its first key, typically generated as `snake_case(name)_source_book_abbreviation_page`.
* Data types strictly adhere to the JSON schemas defined in the `schemas/` directory for their respective data categories. Please refer to these schemas when contributing or interpreting data.
* Updates to the data should be made using the JSON edit request format detailed in the relevant instructional documents.

## Rule on Multiple Sources

This dataset aims to be comprehensive. When adding or updating information:
* Data from the **Star Wars Saga Edition Core Rulebook (CR)** serves as the primary baseline.
* Content from other **official SAGA Edition sourcebooks** will be incorporated to expand upon, provide alternatives to, or offer errata for existing entries.
* All additions or modifications must clearly cite their `source_book` (using the abbreviations defined in `data/meta_info/source_books.json`) and `page` number, typically within a `primary_source` object or `source_details` objects for granular citations.
* The `json_updater.py` tool is designed to facilitate these updates while maintaining data integrity.
* Where errata has been applied, relevant JSON files will contain an `errata_applied` field at the root of their main data object, listing the incorporated corrections.

## Current Status & Next Steps

**Current Status (as of May 31, 2025):**
* Processing of the **Core Rulebook (CRB)** is significantly advanced.
* **Completed/Largely Completed CRB Sections:**
    * Character Fundamentals: Abilities, Species, Heroic Classes, Skills, Feats (Data & Rules).
    * The Force: Rules, Powers, Talents, Techniques, Secrets, Traditions Lore (Significant portions complete).
    * Equipment: Rules and comprehensive data for Melee Weapons, Ranged Weapons, Armor, Accessories, Explosives, and General Equipment.
    * Vehicles: Planetary Vehicles (rules & data), Starships (data & schema). Rules for Vehicle Combat and General Vehicle operation.
    * Droids: Droid Rules, Droid Chassis (CRB entries updated), Droid Systems (CRB entries updated).
    * Prestige Classes: Prestige Class Rules and all 12 CRB Prestige Classes (data updated).
    * Hazards: CRB Hazard data updated in `hazards.json`.
    * Gamemastering Foundations: `environmental_rules.json`, `encounter_building_rules.json`, `adventure_design_principles.json`, `campaign_management_principles.json` created with CRB content.
    * Meta Files: `source_books.json`, `abbreviations_glossary.json`, `game_definitions.json`, `eras_overview.json` are in place.
    * Templates & Defensive Items: Initial data processed.
    * Errata: Applied across relevant updated CRB sections.
* **Schemas**: Schemas for most existing CRB data categories are defined or have been recently updated.

**Next Major Steps:**
* **Complete CRB Digitization:**
    * **Galactic Gazetteer (CRB Chapter 13):** Create and populate `planets.json`.
    * **Allies and Opponents (CRB Chapter 16):** Create and populate `beasts.json`; update `species.json` with the "Other Species"; populate NPC data files with Nonheroic Character archetypes.
    * **Heroic Traits (CRB Chapter 7):** Digitize Destiny mechanics into `destiny_rules.json`.
    * **Main Characters (CRB Chapter 15):** Process stat blocks into NPC data files.
    * **Talents (`talents.json`):** Full population of all individual talents from CRB and subsequently other books. This is a large undertaking.
    * Review and complete any remaining "partial" sections (e.g., ensuring all nuanced combat rules from CRB Chapter 9 are captured).
* **Process Non-CRB Data:**
    * Systematically begin processing data from other sourcebooks (Scum and Villainy, Knights of the Old Republic Campaign Guide, etc.) for all categories (Droids, Starships, Feats, Prestige Classes, etc.), using the established CSVs as a starting point for indexing.
* **Schema Refinement & Creation:** Finalize schemas for all data files and create any missing ones as new data types are processed.
* **Tool Enhancement:** Further development of AI GM tools and utilities based on the structured data.

## Contribution Guidelines

We welcome contributions to help expand and refine this dataset!
* **Reporting Issues & Suggesting Enhancements:** Please use the GitHub Issues tracker for this repository to report any errors, inconsistencies, missing data, or to suggest improvements or new features.
* **Proposing Changes:** For significant changes or new data structures, please open an Issue first to discuss the proposal.
* **Submitting Data:**
    * The preferred method for submitting corrections or new data is by generating JSON payloads compatible with the `json_updater.py` script. Refer to the "Instructions for Generating JSON Edits" document.
    * Ensure all data is sourced from official Star Wars Saga Edition rulebooks or supplements.
    * Cite sources meticulously (`source_book` abbreviation and `page` number).
* **Data Formatting:**
    * Adhere strictly to the JSON schemas located in the `schemas/` directory.
    * All JSON keys must use `snake_case`.
    * Follow the established `id` generation conventions for list items.
* **Code Contributions (Scripts/Tools):** If contributing Python scripts, please follow standard Python coding conventions (e.g., PEP 8).

## License

The code in this repository is licensed under the MIT License. The data content is licensed under CC BY-SA 4.0.

## Disclaimer

This project is a fan-created resource intended for personal use and to facilitate playing Star Wars SAGA Edition. Star Wars, SAGA Edition, and all associated properties are trademarks of Lucasfilm Ltd. and/or Wizards of the Coast (a subsidiary of Hasbro). This project is not affiliated with, endorsed, sponsored, or approved by Lucasfilm Ltd., Wizards of the Coast, or Hasbro. Please support official Star Wars SAGA Edition releases.

## Acknowledgements

This project builds upon the incredible work and passion of many individuals and communities. We extend our sincere gratitude to:

* **The Original Creators of Star Wars Saga Edition:**
    * **Primary Designers:** Christopher Perkins, Owen K.C. Stephens, and Rodney Thompson, for their work on developing the Star Wars Saga Edition system. 
    * **Original Star Wars Roleplaying Game Designers (Wizards of the Coast):** Bill Slavicsek, Andy Collins, and JD Wiker, whose prior work laid foundations for the d20 Star Wars line.
    * **Developer and Editor:** Gary M. Sarli, for his significant contributions to the development and editing of the Saga Edition Core Rulebook.
    * **Publisher:** Wizards of the Coast (a subsidiary of Hasbro), for publishing Star Wars Saga Edition and its supplements.
    * **Lucasfilm Licensing:** Sue Rostoni and Jonathan Rinzler, for their editorial guidance from Lucas Licensing. 

* **The SAGA Index Community & Compilers:**
    * **Shane A. Thelen (ewokontoast) and Staffan Bengtsson (JemyM):** For their monumental work on the "SAGA Character Index version 4.0," which forms a significant basis for many data elements in this project.
    * The wider Star Wars SAGA Edition community for their continued passion, dedication, and creation of resources for the game. Their efforts help keep Saga Edition vibrant and playable.

* **Lucasfilm Ltd.:** For creating and stewarding the Star Wars universe, which provides the rich setting for these adventures.

---

*This README is a living document and will be updated as the project progresses and new data categories are integrated.*
