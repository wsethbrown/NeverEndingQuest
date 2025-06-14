# DungeonMasterAI

An AI-powered Dungeon Master assistant for running 5th edition campaigns with full campaign generation, interactive gameplay, and comprehensive game management capabilities.

## Overview

DungeonMasterAI uses OpenAI's GPT models to create complete 5th edition campaigns and provide an interactive Dungeon Master experience. The system features:

### Campaign Generation
- **Complete Campaign Builder**: Generate entire campaigns with areas, locations, plots, and NPCs
- **Context-Aware Generation**: Maintains consistency across all generated content
- **Schema-Compliant Output**: All generated files follow strict 5th edition schemas

### Game Management
- Character statistics and inventory tracking
- NPC interactions with personality and goals
- Turn-based combat system with validation
- Location exploration with detailed descriptions
- Plot progression and quest tracking
- Time and world condition management
- Dynamic storytelling based on player actions

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

## Quick Start

### Generate a New Campaign
```
python campaign_builder.py
```
Follow the prompts to create a complete campaign with areas, locations, and plots.

### Play the Game

**Option 1: Terminal Interface**
```
python main.py
```
Load your generated campaign and start playing in the terminal!

**Option 2: Web Interface (Recommended)**
```
python run_web.py
```
Launch the modern web interface with separate panels for game output and debug information. The browser will open automatically.

## Key Features

### Campaign Generation
- **Automated Campaign Builder**: Generate complete campaigns with one command
- **Context Validation**: Ensures consistency across all generated content
- **Customizable Settings**: Control number of areas, locations per area, and complexity
- **Schema Compliance**: All files follow strict 5th edition JSON schemas

### Gameplay Features
- **Interactive Storytelling**: Dynamic narratives respond to player actions
- **Combat System**: Turn-based combat with validation and logging
- **Character Management**: Track stats, inventory, and progression
- **World Exploration**: Navigate detailed locations with connections
- **Plot Management**: Main quests, side quests, and dynamic plot evolution
- **NPC System**: Persistent NPCs with personalities, goals, and attitudes
- **Time Tracking**: Complete world time and condition management

## Project Structure

### Core Systems
- `main.py` - Main game loop and player interaction
- `campaign_builder.py` - Automated campaign generation system
- `campaign_context.py` - Context management for consistent generation
- `combat_manager.py` - Combat system management
- `dm.py` & `dm_wrapper.py` - AI Dungeon Master logic

### Campaign Generation
- `campaign_generator.py` - Campaign overview generation
- `area_generator.py` - Area and map generation
- `location_generator.py` - Detailed location generation
- `plot_generator.py` - Plot and quest generation

### Game Management
- `conversation_utils.py` - Conversation tracking and summarization
- `update_*.py` - Various state update modules
- `player_stats.py` - Character statistics and progression
- `npc_builder.py` - NPC generation system
- `monster_builder.py` - Monster creation tools

### Data Files
- `*_schema.json` - JSON schemas for validation
- `campaigns/` - Generated campaign data
- `*.json` - Character, location, and game state files

## Configuration

The system uses OpenAI GPT models configured in `config.py`:

- `DM_MAIN_MODEL` - Primary model for narration and generation
- `DM_SUMMARIZATION_MODEL` - Conversation and event summarization
- `DM_VALIDATION_MODEL` - Combat and rule validation
- `DM_COMBAT_NARRATOR_MODEL` - Combat narration and description
- Various other specialized models for different tasks

## Requirements

- Python 3.9+
- OpenAI API key
- Required packages listed in `requirements.txt`

## Usage Examples

### Generate a Campaign
```bash
python campaign_builder.py
# Enter campaign name: Keep of Doom
# Number of areas: 3
# Locations per area: 15
# Describe your campaign concept: A dark fantasy adventure...
```

### Start Playing
```bash
python main.py
# The system will load party_tracker.json and begin the adventure
```

## License

This work is licensed under the Creative Commons Attribution 4.0 International License. 
See the LICENSE file for details.

### SRD Attribution

Portions of this work are derived from the System Reference Document 5.2.1 ("SRD 5.2.1") 
by Wizards of the Coast LLC and available at https://dnd.wizards.com/resources/systems-reference-document. 

The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License 
available at https://creativecommons.org/licenses/by/4.0/legalcode.

This work is not affiliated with, endorsed, sponsored, or specifically approved by 
Wizards of the Coast LLC. This is unofficial Fan Content permitted under the 
Creative Commons Attribution 4.0 International License.

## Recent Updates

- **Campaign Path Management**: Implemented `CampaignPathManager` for centralized file path handling
- **Combat System Fixes**: Fixed monster file loading in combat to use campaign directories
- **Directory Structure**: All campaign-specific files now stored in organized campaign folders
- **Legacy Cleanup**: Moved old files to legacy folder, cleaning up root directory
- **Validation System**: Relaxed combat validation to focus on major errors only
- **Equipment Syncing**: Verified arrow transfer sync between character files

## Future Development

- Web interface for easier interaction
- Voice integration for immersive gameplay
- Image generation for scenes and characters
- Additional ruleset support (Pathfinder, etc.)
- Multi-player support
- Campaign sharing and templates

---

*Created by MoonlightByte*
*Contributors: Claude AI Assistant*
