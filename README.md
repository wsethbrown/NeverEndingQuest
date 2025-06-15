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

## How the Campaign World Works

### Location-Based Module System
The game uses a revolutionary **geographic boundary system** instead of traditional campaign chapters:

- **Modules as Geographic Regions**: Each adventure module represents a geographic area network (village + forest + dungeon)
- **Organic World Growth**: The world map expands naturally as you add new modules - no predetermined geography needed
- **Automatic Transitions**: When you travel to a new area, the system automatically detects if you're entering a different module
- **Living World Memory**: Every location remembers your visits and the world evolves based on accumulated decisions

### How Modules Connect
```
Example World Evolution:
Keep_of_Doom: Harrow's Hollow (village) → Gloamwood (forest) → Shadowfall Keep (ruins)
+ Crystal_Peaks: Frostspire Village (mountain town) → Ice Caverns (frozen depths)
= AI Connection: "Mountain paths from Harrow's Hollow lead to Frostspire Village"
```

The AI analyzes area descriptions and themes to suggest natural narrative bridges between modules.

### Adventure Continuity
- **Chronicle System**: When you leave a module, the system generates a beautiful prose summary of your adventure
- **Context Accumulation**: Return visits include full history of previous adventures in that region
- **Character Relationships**: NPCs remember you across modules and adventures continue to evolve
- **Consequence Tracking**: Major decisions affect future adventures and available story paths

### Module Creation & Community
- **Module Builder**: Create new adventure modules with integrated areas, plots, and NPCs
- **Community Modules**: Download and integrate player-created adventures automatically
- **Safety Protocols**: All community modules undergo content safety validation and conflict resolution
- **Organic Integration**: New modules connect naturally to your existing world without manual configuration

## Key Features

### Revolutionary Campaign System
- **Location-Based Transitions**: Cross-module travel happens naturally through AI-driven exploration
- **Automatic Module Detection**: System scans for new modules and integrates them seamlessly
- **Living World Continuity**: Return to any area with full memory of previous adventures
- **Chronicle Generation**: Beautiful elevated fantasy prose summaries of completed adventures
- **Hub-and-Spoke Design**: Central locations become accessible from multiple adventure modules

### Module Generation & Management
- **Complete Module Builder**: Generate entire adventure modules with areas, locations, plots, and NPCs
- **Context-Aware Generation**: Maintains consistency across all generated content
- **Schema Compliance**: All files follow strict 5th edition JSON schemas
- **Community Module Support**: Framework for sharing and auto-integrating downloaded adventures
- **Safety Validation**: Automatic content review and conflict resolution for community modules

### Gameplay Features
- **Interactive Storytelling**: Dynamic narratives respond to accumulated player decisions across modules
- **Combat System**: Turn-based combat with validation and AI simulation
- **Character Management**: Unified character system supporting players, NPCs, and monsters
- **World Exploration**: Navigate detailed locations with dynamic state and cross-module connections
- **Plot Management**: Authoritative module_plot.json tracks main quests, side quests, and progression
- **NPC System**: Persistent NPCs with personalities, goals, and cross-module relationship tracking
- **Time Tracking**: Complete world time and condition management with realistic progression

## Project Structure

### Core Systems
- `main.py` - Main game loop and player interaction
- `module_builder.py` - Automated module generation system
- `module_stitcher.py` - Organic module integration with safety protocols
- `campaign_manager.py` - Location-based hub-and-spoke campaign orchestration
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

## Community Module Safety

The module stitcher includes comprehensive safety protocols for community-created content:

### Automatic Safety Validation
- **Content Review**: AI analyzes all module content for family-friendly appropriateness
- **File Security**: Blocks executable files, oversized content, and malicious patterns
- **Schema Compliance**: Validates JSON structure against 5th edition schemas
- **ID Conflict Resolution**: Automatically resolves duplicate area/location identifiers

### How It Works
```
New module detected → Security scan → Content safety check → Schema validation → Conflict resolution → Integration
```

### For Module Creators
- Use unique area IDs to avoid conflicts (avoid common patterns like HH001)
- Keep files under 10MB and use only JSON/text formats
- Create family-friendly content appropriate for all ages
- Follow provided JSON schemas for compatibility

### For Players
- Download modules from trusted sources
- System provides multiple safety layers automatically
- All community modules undergo validation before integration
- Backup saves before adding new modules as good practice

## Usage Examples

### Generate a Module
```bash
python module_builder.py
# Follow prompts to create areas, locations, plots, and NPCs
# System ensures consistency and schema compliance
```

### Start Playing
```bash
python main.py
# System automatically detects and integrates any new modules
# Begin adventure in your generated or downloaded module
```

### Add Community Modules
```bash
# Simply place module folder in modules/ directory
# System automatically detects, validates, and integrates on next startup
# AI generates narrative connections to existing world
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
