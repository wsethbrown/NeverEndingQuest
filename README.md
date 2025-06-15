# DungeonMasterAI

An AI-powered Dungeon Master assistant for running 5th edition campaigns with full campaign generation, interactive gameplay, and comprehensive game management capabilities.

## Overview

DungeonMasterAI uses OpenAI's GPT models to create complete 5th edition campaigns and provide an interactive Dungeon Master experience. The system features a revolutionary **Location-Based Hub-and-Spoke Campaign Architecture** that enables seamless multi-module adventures.

### Revolutionary Campaign System
- **Location-Based Modules**: Each geographic area network forms a self-contained adventure module
- **Automatic Module Transitions**: AI-driven cross-module travel with seamless context preservation
- **Living World Continuity**: Return to any visited module with full accumulated adventure history
- **Chronicle Generation**: Elegant prose summaries of completed adventures using elevated fantasy language
- **Hub-and-Spoke Design**: Central hub locations accessible from multiple adventure modules

### Campaign Generation
- **Complete Module Builder**: Generate entire adventure modules with areas, locations, plots, and NPCs
- **Context-Aware Generation**: Maintains consistency across all generated content
- **Schema-Compliant Output**: All generated files follow strict 5th edition schemas
- **Community Module Support**: Framework for sharing and auto-stitching downloaded adventure modules

### Game Management
- Character statistics and inventory tracking with unified character architecture
- NPC interactions with personality and goals across multiple modules
- Turn-based combat system with validation and AI simulation
- Location exploration with detailed descriptions and dynamic state
- Plot progression and quest tracking with authoritative module_plot.json
- Time and world condition management with realistic progression
- Dynamic storytelling that evolves based on accumulated player decisions

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

### Generate a New Module
```
python module_builder.py
```
Follow the prompts to create a complete module with areas, locations, and plots.

### Play the Game

**Option 1: Terminal Interface**
```
python main.py
```
Load your generated module and start playing in the terminal!

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
- `module_builder.py` - Automated module generation system
- `module_context.py` - Context management for consistent generation
- `combat_manager.py` - Combat system management
- `dm.py` & `dm_wrapper.py` - AI Dungeon Master logic

### Campaign Generation
- `module_generator.py` - Module overview generation
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
- `modules/` - Generated module data
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

### Generate a Module
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
