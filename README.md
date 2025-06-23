# DungeonMasterAI

An AI-powered Dungeon Master assistant for running 5th edition campaigns with full campaign generation, interactive gameplay, and comprehensive game management capabilities.

## 💝 A Labor of Love for Solo Adventurers

**Created for the love of roleplaying games and the challenge of finding other players.**

This project was born from a passion for D&D and the reality that finding consistent players for regular sessions can be difficult. DungeonMasterAI provides a complete solo RPG experience that captures the magic of tabletop gaming without the scheduling challenges.

### 🎯 Design Philosophy: Freedom Within Structure

**The AI is intentionally flexible and non-restrictive** - you can convince it, negotiate with it, or even "cheat" if you want to. This is by design! The software provides:

- **Rails and Guards**: Prevent data corruption and maintain game continuity
- **Player Freedom**: The AI adapts to your playstyle - strict rules-lawyer or creative storyteller
- **Flexible Interpretation**: Want that magic item? Convince the AI why your character deserves it
- **Your Adventure**: Play the way that's fun for you - the AI won't judge or restrict your choices

The goal is to provide the **structure needed for consistent gameplay** while maintaining the **creative freedom that makes roleplaying games magical**.

## Overview

DungeonMasterAI uses OpenAI's GPT models to create complete 5th edition campaigns and provide an interactive Dungeon Master experience. The system features a revolutionary **Location-Based Hub-and-Spoke Campaign Architecture** that enables seamless multi-module adventures.

### Revolutionary Campaign System
- **Module-Centric Architecture**: Self-contained adventure modules with unified conversation timeline
- **Seamless Module Transitions**: Intelligent conversation segmentation preserving chronological adventure history
- **AI-Powered Conversation Compression**: Full adventure summaries generated from actual gameplay conversations
- **Living World Continuity**: Return to any visited module with complete accumulated adventure context
- **Chronological Timeline Preservation**: Hub-and-spoke model maintaining adventure sequence across modules
- **Automatic Context Archiving**: Campaign summaries stored sequentially with detailed narrative chronicles
- **Smart Boundary Detection**: Two-condition logic for optimal conversation segmentation between modules
- **AI Autonomous Module Creation**: Dynamic module generation based on party history and adventure progression

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

### 🚀 Starting Your Adventure

**New players can start playing immediately!** The game features an **AI-powered startup wizard** that automatically:

1. **Detects all available modules** in your `modules/` directory
2. **Selects the lowest-level module** for new players (typically level 1-2)
3. **Uses AI reasoning** to determine the optimal starting location within that module
4. **Creates your character** through an interactive AI interview process
5. **Sets up the world** with appropriate weather and political climate

Simply run:
```bash
python main.py
```

The system will guide you through character creation and automatically place you in the perfect starting location for your adventure!

### 🎯 How Module Selection Works

The AI startup wizard uses **agentic reasoning** to provide maximum compatibility:

- **Level-Based Progression**: Automatically selects modules with the lowest minimum level requirement
- **AI Location Analysis**: Analyzes module plot, areas, and locations to find the best starting point
- **Context-Aware Setup**: Provides appropriate weather, political climate, and story context
- **Community Module Support**: Works with any properly formatted module you download or create

### 📦 Module Compatibility

**Any module you download will work automatically!** The system:

- **Auto-detects** new modules placed in the `modules/` directory
- **Resolves conflicts** automatically (duplicate area IDs, etc.)
- **Validates safety** through multiple security layers
- **Generates transitions** with AI-powered travel narration between modules
- **Maintains isolation** so modules don't interfere with each other

### 🎮 Starting Your Game

1. **First Time Setup**: Run `python main.py` - the AI will guide you through everything
2. **Character Creation**: Interactive AI interview creates a character that fits the world
3. **Module Selection**: System automatically picks the best starting module for your level
4. **Starting Location**: AI analyzes the module and places you in the most logical location
5. **Begin Adventure**: Start playing immediately with rich context and atmosphere

### 🔍 What Happens When You Start

When you run `python main.py` for the first time, here's exactly what happens:

1. **Module Scanning**: The system scans your `modules/` directory for all available adventures
2. **Level Analysis**: Each module's level range is calculated from its area difficulty ratings
3. **Automatic Selection**: The lowest-level module is selected (perfect for new characters)
4. **AI Location Analysis**: The AI examines:
   - Module plot and story themes
   - All available areas and their descriptions  
   - Location types (taverns, shops, quest-givers)
   - Political climate and story context
5. **Starting Point Selection**: AI selects the most logical starting location (usually a town center or tavern)
6. **World Setup**: Appropriate weather and political atmosphere are generated
7. **Character Creation**: Interactive AI interview creates a character that fits the world
8. **Game Begin**: You start playing with full immersion and context

### 🏗️ Module Architecture

The system includes three progressive adventure modules:

- **The Ranger's Call** (Level 1-2): Starting adventure in Greenwatch Village
- **Keep of Doom** (Level 3-5): Intermediate adventure in Harrow's Hollow  
- **Silver Vein Whispers** (Level 6-8): Advanced adventure in the Sablemoor Reaches

Each module is completely self-contained but connected through AI-generated travel narration, creating a seamless world experience.

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

### 🌍 Community Module Compatibility

**Maximum compatibility with community content!** The system is designed for seamless integration:

- **Universal Module Support**: Any properly formatted module works automatically - no configuration needed
- **Intelligent Conflict Resolution**: Automatically resolves duplicate area IDs, location conflicts, and naming collisions
- **Safety Validation**: Multi-layer content review ensures family-friendly and schema-compliant modules
- **AI Auto-Integration**: Analyzes module themes and generates natural narrative connections to your world
- **Level-Based Discovery**: New modules appear in progression based on your character's advancement
- **Plug-and-Play**: Simply drop modules in the `modules/` directory and they integrate on next startup

### Module Creation & Sharing
- **Module Builder**: Create new adventure modules with integrated areas, plots, and NPCs
- **AI-Assisted Creation**: AI helps generate cohesive module content that integrates seamlessly
- **Community Standards**: Built-in validation ensures your modules work perfectly for other players
- **Organic Integration**: New modules connect naturally to existing worlds without manual configuration

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
- **AI Autonomous Creation**: When current adventures conclude, AI analyzes party history to craft new contextual modules
- **Narrative-Driven Generation**: AI parses rich narrative descriptions to extract module parameters automatically

### Gameplay Features
- **Interactive Storytelling**: Dynamic narratives respond to accumulated player decisions across modules
- **Combat System**: Turn-based combat with validation and AI simulation
- **Character Management**: Unified character system supporting players, NPCs, and monsters
- **World Exploration**: Navigate detailed locations with dynamic state and cross-module connections
- **Plot Management**: Authoritative module_plot.json tracks main quests, side quests, and progression
- **NPC System**: Persistent NPCs with personalities, goals, cross-module relationship tracking, and **party recruitment**
- **Time Tracking**: Complete world time and condition management with realistic progression

### Advanced Player Systems

#### **🏠 Player Housing & Hub System**
- **Establish Hubs**: Transform any location into a permanent base of operations
- **Hub Services**: Rest, storage, gathering, training, research facilities automatically available
- **Ownership Types**: Party-owned, shared arrangements, or individual strongholds
- **Hub Persistence**: Return from any adventure to your established bases
- **Multi-Hub Support**: Maintain multiple bases across different regions and modules

**Hub Types Available:**
- **Strongholds**: Fortified keeps and castles for defensive operations
- **Settlements**: Villages and towns for commerce and community building
- **Taverns**: Social hubs for information gathering and party meetings
- **Specialized Facilities**: Wizard towers, temples, guildhalls with unique services

#### **📦 Player Storage System**
- **Natural Language Storage**: Use intuitive commands like "I store my gold in a chest here"
- **Location-Based Containers**: Create storage at any location using available containers
- **Persistent Storage**: Items remain safely stored across sessions and module transitions
- **Party Accessibility**: All party members can access shared storage by default
- **Automatic Inventory Management**: System handles all inventory transfers with full safety protocols

**Storage Features:**
- **Container Types**: Chests, lockboxes, barrels, crates, strongboxes
- **Smart Organization**: AI helps organize items by type and importance
- **Secure Storage**: Containers tied to specific locations for security
- **Visual Integration**: Storage automatically appears in location descriptions

#### **👥 NPC Party Recruitment System**

**Build your party by recruiting NPCs you meet during your adventures!**

- **Ask Anyone**: Approach any NPC and ask them to join your party
- **AI Evaluation**: The AI considers the NPC's personality, goals, current situation, and relationship with you
- **Natural Roleplay**: Use persuasion, offer payment, complete quests, or appeal to their motivations
- **Persistent Companions**: Recruited NPCs travel with you across modules and remember shared experiences
- **Dynamic Relationships**: Party NPCs develop bonds with each other and react to your decisions
- **Full Character Sheets**: NPCs become full party members with stats, equipment, and progression

**Recruitment Examples:**
- *"Mira, would you like to join us? We could use a skilled healer on our journey."*
- *"Gareth, we're heading to dangerous lands. Your sword arm would be welcome."*
- *"Sage Eldara, your knowledge of ancient magic could help us stop this threat."*

**NPC Party Features:**
- **Combat Participation**: NPCs fight alongside you with full AI tactical decisions
- **Skill Contributions**: NPCs use their unique abilities to solve problems and overcome challenges
- **Story Integration**: Party NPCs contribute to roleplay and have their own character arcs
- **Cross-Module Continuity**: Your companions remember adventures across different modules
- **Character Development**: NPCs grow and change based on shared experiences

#### **🎲 AI-Driven Module Auto-Generation**
- **Contextual Adventures**: AI analyzes party history to create personalized modules
- **Seamless Integration**: New modules connect naturally to existing world geography
- **Dynamic Scaling**: Adventures adjust to party level and accumulated experience
- **Narrative Continuity**: References previous adventures and established relationships

**Auto-Generation Triggers:**
- **Adventure Completion**: New modules generated when current adventures conclude
- **Player Interest**: AI detects story hooks and creates relevant content
- **World Events**: Major decisions trigger consequences in new regions
- **Party Progression**: Level advancement unlocks higher-tier adventure options

#### **🌍 Living Campaign World Integration**
- **Isolated Module Architecture**: Each module operates independently while maintaining world coherence
- **AI Travel Narration**: Seamless transitions between modules with atmospheric descriptions
- **World Registry**: Central tracking of all modules, areas, and their relationships
- **Cross-Module Consequences**: Actions in one module affect opportunities in others

## Project Structure

### Core Systems
- `main.py` - Main game loop and player interaction
- `module_builder.py` - Automated module generation system
- `module_stitcher.py` - Organic module integration with safety protocols
- `campaign_manager.py` - Location-based hub-and-spoke campaign orchestration
- `combat_manager.py` - Combat system management
- `dm.py` & `dm_wrapper.py` - AI Dungeon Master logic

### Player Systems
- `storage_manager.py` - Player storage system with atomic file protection
- `storage_processor.py` - AI-powered natural language storage processing
- `action_handler.py` - Command processing and system integration
- `location_manager.py` - Location-based features and storage display

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
- `player_storage.json` - Central player storage repository
- `storage_action_schema.json` - Storage operation validation schema

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

### Player Housing & Storage Examples

#### **Establish a Hub**
```
Player: "I want to claim this keep as our base of operations"
AI: *Establishes Shadowfall Keep as a party stronghold with full services*
```

#### **Natural Language Storage**
```
Player: "I store my extra gold in a chest in the treasury"
AI: *Creates storage container and transfers 500 gold coins*

Player: "What's in our storage here?"
AI: *Lists all containers and contents at current location*

Player: "I get my healing potions from the chest we made"
AI: *Retrieves potions and updates inventory automatically*
```

#### **NPC Party Recruitment**
```
Player: "Elara, you've helped us so much. Would you consider joining our party?"
AI: *Elara considers your shared adventures and her own goals*
AI: "I've grown fond of you all, and these dark times require brave souls to stand together. Yes, I'll join you."
*Elara is added to your party with full character sheet and equipment*

Player: "Marcus, we're heading to the Shadowlands. Your knowledge of undead could save lives."
AI: *Marcus weighs the danger against his scholarly interests*
AI: "The chance to study the necromantic energies there... yes, I'll come. But I'm not much of a fighter."
*Marcus joins as a support character with unique magical knowledge*
```

#### **Hub Services**
```
Player: "I want to rest at our stronghold"
AI: *Provides full rest benefits and hub-specific services*

Player: "Let's gather at the tavern we established"
AI: *Transitions party to hub location with full context*
```

### AI Module Generation Examples

#### **Contextual Adventure Creation**
```
AI: *Analyzes party completed Keep_of_Doom module*
AI: *Detects themes: undead, curses, heroic rescue*
AI: *Generates "Whispers of the Shadowlands" - related but escalated adventure*
```

#### **Dynamic World Building**
```
Player: "We've heard rumors of trouble in the northern mountains"
AI: *Creates mountain-themed module tied to established lore*
AI: *Connects via travel narration from current location*
```

#### **AI Flexibility Examples**

**The AI adapts to your playstyle - strict or creative, it's your choice:**

```
Player: "I try to convince the shopkeeper that I'm nobility and deserve a discount"
AI: *Evaluates your charisma, background, and story context*
AI: "The shopkeeper seems skeptical but your confident bearing impresses them. 10% discount!"

Player: "I search the dragon's lair thoroughly for any hidden treasure"
AI: "Roll a perception check... Natural 20! You notice loose stones hiding a secret compartment with an ancient artifact."

Player: "This quest is taking forever. Can we just say we completed it?"
AI: "I understand you want to move the story along. Let's fast-forward through the completion and focus on the interesting parts!"

Player: "I want that legendary sword the NPC mentioned. Can I convince them to give it to me?"
AI: *Considers story logic, your relationship, and what would be interesting*
AI: "It won't be easy, but if you can prove yourself worthy through a specific quest, they might consider it..."
```

**Remember: The AI wants you to have fun! It provides structure for consistency but adapts to your preferred style of play.**

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

### **🎉 Major Features Added**
- **🤖 AI-Powered Startup Wizard**: Automatic module detection, level-based selection, and AI reasoning for optimal starting locations
- **👥 NPC Party Recruitment**: Ask any NPC to join your party with AI evaluation and persistent companions
- **🏠 Hub & Housing System**: Transform any location into a permanent base with full services
- **📦 Player Storage System**: Complete natural language storage with atomic file protection
- **🎯 Module Level Progression**: Intelligent 1-2 → 3-5 → 6-8 level-based adventure flow
- **🌍 Community Module Compatibility**: Universal module support with automatic conflict resolution
- **🎲 AI Auto-Generation**: Contextual module creation based on party history and preferences
- **🔄 Isolated Module Architecture**: Clean module separation with AI travel narration

### **🔧 Technical Improvements**
- **🏗️ Enhanced Module Stitcher**: Fixed areas/ subdirectory scanning with automatic ID conflict resolution
- **⚙️ Centralized AI Configuration**: Removed all hardcoded GPT models, now uses config.py for consistency
- **🔧 Startup Wizard Architecture**: Complete rewrite with proper error handling and Windows compatibility
- **📁 Campaign Path Management**: Implemented `CampaignPathManager` for centralized file path handling
- **⚔️ Combat System Fixes**: Fixed monster file loading in combat to use campaign directories
- **📂 Directory Structure**: All campaign-specific files now stored in organized campaign folders
- **🧹 Legacy Cleanup**: Moved old files to legacy folder, cleaning up root directory
- **✅ Validation System**: Relaxed combat validation to focus on major errors only
- **Equipment Syncing**: Verified arrow transfer sync between character files

### **🛡️ Safety & Protection**
- **Atomic File Operations**: Backup/restore functionality prevents data corruption
- **Schema Validation**: All operations validated against JSON schemas
- **Context Contamination Prevention**: AI prompts prevent module creation conflicts
- **Character File Protection**: Inventory changes safely backed up before modification

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
