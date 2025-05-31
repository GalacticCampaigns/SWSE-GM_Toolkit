# SWSE AI Gamemaster Toolkit

This repository is a comprehensive toolkit and structured data resource for powering an AI Gamemaster (AI GM) for the Star Wars Saga Edition roleplaying game. It aims to provide a detailed, machine-readable, and community-vetted representation of game rules, lore, and entities from the Core Rulebook and various supplements.

Beyond a simple index, this project includes:
* **Structured Game Data:** JSON files detailing abilities, skills, species, feats, Force powers, talents, heroic classes, prestige classes, combat mechanics, equipment, vehicles, droids, and more. These are designed for easy parsing and use by AI systems.
* **Core Rule Definitions:** Centralized JSON files for fundamental game mechanics, system rules, and glossaries.
* **Lore Archives:** Organized lore information, such as era descriptions, Force traditions, etc., to enrich AI storytelling.
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
    * Index Elements: Equipment, Weapons, Armor, Vehicles, Droids, etc.
    * Combat Mechanics and detailed game rules.
* **Structured Core Rules:** General game mechanics, system definitions, and glossaries stored in dedicated JSON files within `data/core_rules/` and `data/meta_info/`.
* **Rich Lore Information:** Contextual lore for eras, Force traditions, and other aspects of the Star Wars universe, located in the `data/lore/` directory.
* **JSON Schemas:** Validation schemas in the `schemas/` directory to ensure data consistency and integrity across all JSON files.
* **Automated Update Tool:** A Python script (`tools/json_updater.py`) designed to apply batch edits to the JSON data files, ensuring accurate and efficient maintenance. 
* **Detailed Documentation:**
    * This README file.
    * Instructions for using the `json_updater.py` script (see "Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles").
    * Guidelines for data formatting (e.g., NPC Profile JSON structure - see "Instructions for AI: Generating and Maintaining Character Profile JSON").
    * Summaries of the project's current processing state.

## Repository Structure

The repository is organized as follows:

* **`data/`**: Contains all the structured JSON data.
    * `character_elements/`: Core data for player/character building blocks (abilities, skills, species, feats, talents, classes, prestige classes).
    * `index_elements/`: Data for game items like equipment, weapons, armor, vehicles, droids.
    * `core_rules/`: JSON files for general system rules (e.g., `ability_system_rules.json`, `skill_rules.json`, `combat_rules.json`).
    * `meta_info/`: Supporting metadata files like `source_books.json`, `game_definitions.json`, `abbreviations_glossary.json`.
    * `lore/`: Files containing narrative and contextual information, such as `eras_overview.json` and `force_traditions_lore.json`.
* **`schemas/`**: Contains JSON schemas used for validating the data files.
* **`tools/`**: Includes utility scripts, primarily `json_updater.py`, for dataset maintenance.
* **`docs/`** (or **`instructions/`**): Contains detailed instructions for JSON updating, data entry guidelines (e.g., NPC profile format), and current state summaries.

## Getting Started / How to Use

1.  **Clone the Repository:**
    ```bash
    git clone [URL_to_your_repository]
    ```
2.  **Explore the Data:** Navigate the `data/` directory to find the JSON files relevant to your needs.
3.  **Using the `json_updater.py` Script:**
    * This script is located in the `tools/` directory. 
    * It processes edit request files (formatted as JSON arrays of update/add/delete actions) to modify the data files. 
    * Refer to "Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles" (available in `docs/` or as a separate document) for detailed instructions on formatting edit requests and running the script.

## Data Format & Schemas

* All game data is structured in JSON format.
* Field names within the JSON objects consistently use `snake_case`.
* Data types strictly adhere to the JSON schemas defined in the `schemas/` directory for their respective data categories. Please refer to these schemas when contributing or interpreting data.
* Updates to the data should be made using the JSON edit request format detailed in "Instructions for Generating JSON Edits for SAGA Index Data & Character Profiles".

## Rule on Multiple Sources

This dataset aims to be comprehensive. When adding or updating information:
* Data from the **Star Wars Saga Edition Core Rulebook (CR)** serves as the primary baseline.
* Content from other **official SAGA Edition sourcebooks** will be incorporated to expand upon, provide alternatives to, or offer errata for existing entries.
* All additions or modifications must clearly cite their `source_book` (using the abbreviations defined in `data/meta_info/source_books.json`) and `page` number.
* The `json_updater.py` tool is designed to facilitate these updates while maintaining data integrity.

## Contribution Guidelines

*(This section should be expanded based on your project's collaboration model. For now, it's a placeholder.)*

* **Reporting Issues:** Use the GitHub Issues tracker for the repository.
* **Proposing Changes:** Discuss proposed changes or new data structures via Issues or designated communication channels. Edits should ideally be formatted according to the JSON edit request structure.
* **Data Entry Conventions:** Adhere to the established JSON schemas and naming conventions (`snake_case` for keys, consistent ID generation, structured `effects` arrays, etc.).

## License

The code in this repository is licensed under the MIT License. The data content is licensed under CC BY-SA 4.0."

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
