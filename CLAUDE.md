# DungeonMasterAI Project Guide

## Project Overview

DungeonMasterAI is an AI-powered Dungeon Master system for D&D 5e that provides automated gameplay, campaign management, and web-based player interaction. The system generates dynamic encounters, manages world state, and provides intelligent responses to player actions.

## Core Architecture

### Game Loop & Entry Point
- **main.py**: Core game loop handling player input, AI responses, and state management
- **dm_wrapper.py**: AI interface wrapper for generating DM responses and managing game flow
- **action_handler.py**: Processes player actions and determines appropriate responses

### Key Modules

#### Campaign Management
- **campaign_generator.py**: Creates new campaigns and scenarios
- **campaign_context.py**: Manages campaign state and context
- **campaign_path_manager.py**: Handles file paths for campaign data
- **location_manager.py**: Manages location data and transitions

#### Game Systems
- **combat_manager.py**: Handles combat encounters and mechanics
- **cumulative_summary.py**: Generates adventure summaries and maintains continuity
- **status_manager.py**: Manages game status and UI updates

#### Data Updates
- **update_player_info.py**: Handles player character updates (with validation)
- **update_npc_info.py**: Manages NPC information updates
- **conversation_utils.py**: Manages conversation history and context

#### Web Interface
- **web_interface.py**: Flask/SocketIO server for web-based gameplay
- **templates/game_interface.html**: Main web UI with character sheets, inventory, debug panels

### Data Structures

#### JSON Schemas (*/schema.json files)
- **campaign_schema.json**: Campaign structure
- **char_schema.json**: Character data format
- **location_schema.json**: Location definitions
- **encounter_schema.json**: Combat encounter format

#### Key Data Files
- **party_tracker.json**: Current party state, location, world conditions
- **conversation_history.json**: AI conversation log
- **journal.json**: Adventure journal entries

### Campaign Organization
```
campaigns/[CAMPAIGN_NAME]/
├── [CAMPAIGN_NAME]_campaign.json    # Main campaign file
├── [AREA_ID].json                   # Area locations (e.g., G001.json)
├── map_[AREA_ID].json              # Area maps
├── monsters/                        # Custom monsters
├── npcs/                           # NPCs
└── norn.json                       # Player character file
```

## Important Patterns

### AI Integration
- Uses Claude API for DM responses and game logic
- Validation layers prevent AI from corrupting game state
- Structured prompts with examples guide AI behavior

### State Management
- JSON-based persistence with schema validation
- Atomic updates with rollback capability
- Separation of player data, world state, and campaign data

### Action Processing Flow
1. Player input → action_handler.py
2. Context gathering → conversation_utils.py
3. AI processing → dm_wrapper.py
4. State updates → update_*.py modules
5. Response delivery → web_interface.py

## Quick Tips

### Working with Player Updates
- Always use validation functions in update_player_info.py
- Check examples in prompts to understand expected AI behavior
- Array updates replace entirely (not merge) - validate carefully

### Campaign Development
- Use campaign_generator.py for new scenarios
- Location data follows strict schema - validate before saving
- Encounter IDs follow pattern: [AREA][LOCATION]-E[NUMBER]

### Web UI Development
- Character sheet uses CSS transform scaling for responsive design
- **Important**: Remove whitespace/newlines from HTML generation to fix spacing issues
- Use SocketIO for real-time updates between frontend and backend

## Common Issues & Solutions

### Web UI Spacing Problems
**Issue**: Phantom spacing in web UI layouts (especially character sheets)
**Solution**: Remove ALL whitespace and newlines from HTML generation. Use inline string concatenation instead of formatted multi-line HTML. This fixes spacing issues caused by whitespace nodes in the DOM.

Example:
```javascript
// BAD - Creates spacing issues
html += `
    <div class="item">
        <span>${name}</span>
    </div>
`;

// GOOD - No spacing issues  
html += `<div class="item"><span>${name}</span></div>`;
```

### Character Data Validation
**Issue**: AI sometimes returns incomplete arrays, wiping inventory
**Solution**: Use validation functions that check proposed updates against original state before applying

### Campaign File Corruption
**Issue**: JSON files become malformed during updates
**Solution**: Always backup before major changes, use schema validation, implement atomic updates