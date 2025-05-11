# DungeonMasterAI

An AI-powered Dungeon Master assistant for running D&D 5e campaigns, designed to interact with players, manage NPC characters, handle combat, track inventory, and progress the storyline.

## Overview

DungeonMasterAI uses OpenAI's GPT models to create an interactive and dynamic Dungeon Master experience. The system manages:

- Character statistics and inventory
- NPC interactions and behavior
- Combat encounters
- Location exploration
- Plot progression
- Time tracking
- Dynamic storytelling

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `config_template.py` to `config.py` and add your OpenAI API key:
   ```
   cp config_template.py config.py
   ```
4. Edit `config.py` to include your actual API key
5. Run the main script:
   ```
   python main.py
   ```

## Features

- **Interactive Storytelling**: Dynamic and responsive narratives based on player actions
- **Combat System**: Turn-based combat encounters with monsters and NPCs
- **Character Management**: Track stats, inventory, and progression
- **World Exploration**: Navigate locations with descriptive elements
- **Plot Management**: Evolving storylines with side quests and main plot
- **NPC Interaction**: Dynamic NPCs with personalities and goals
- **Time Tracking**: In-game time management system

## Project Structure

- `main.py` - Main game loop
- `combat_sim_v2.py` - Combat simulation system
- `conversation_utils.py` - Conversation management utilities
- `plot_update.py` - Plot progression tracking
- `player_stats.py` - Player statistics handling
- `update_*.py` - Various update modules for game state
- `*.json` - Schema and data files

## Configuration

The system uses GPT models which can be configured in the `config.py` file:

- `DM_MAIN_MODEL` - Primary model for game narration
- `DM_SUMMARIZATION_MODEL` - Model for summarizing conversations
- `DM_VALIDATION_MODEL` - Model for validating responses
- And various other specialized models

## Requirements

- Python 3.9+
- OpenAI API key
- Required packages listed in `requirements.txt`

## License

This project is for personal use and experimentation.

## Future Development

- Web interface
- Voice integration
- Image generation for scenes and characters
- Additional ruleset support

---

*Created by MoonlightByte*