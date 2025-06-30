# Encounter File Operations Analysis

## Overview

The dungeon master system uses encounter JSON files to manage combat state, following a consistent naming pattern: `encounter_{encounter_id}.json` where encounter_id follows the format `{location_id}-E{number}` (e.g., `encounter_TW05-E1.json`).

## Encounter File Structure

Based on `encounter_TW05-E1.json`, encounter files contain:
- `encounterId`: Unique identifier
- `creatures`: Array of participants (players, NPCs, enemies)
- `encounterSummary`: Narrative description
- `current_round` / `combat_round`: Turn tracking
- Each creature has: name, type, initiative, status, conditions, actions, hit points, armor class

## Complete Function Mapping

### CREATE Operations

#### 1. combat_builder.py
**Function:** `create_encounter_file(encounter_id, player_characters, npcs, monsters, encounter_summary)`
- **Operation:** Creates new encounter JSON files
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Main encounter creation function that initializes combat with all participants, rolls initiative, and saves the initial encounter state

#### 2. action_handler.py
**Function:** `createEncounter(player, npcs, monsters, encounterSummary)`
- **Operation:** Creates encounter through action system
- **File Pattern:** `encounter_{encounter_id}.json` 
- **Description:** Action handler that delegates to combat_builder for encounter creation, generates unique encounter IDs based on location

### READ Operations

#### 3. combat_manager.py
**Function:** `load_encounter(encounter_id)`
- **Operation:** Loads encounter data from JSON
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Core function to load encounter state for combat management

**Function:** `get_encounter_status(encounter_id)`
- **Operation:** Reads encounter to check combat status
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Returns whether encounter is active, completed, or error state

#### 4. xp.py
**Function:** `process_encounter_xp(encounter_id)`
- **Operation:** Reads encounter data for XP calculation
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Analyzes completed encounters to award experience points to participants

#### 5. generate_prerolls.py
**Function:** `process_encounter_for_prerolls(encounter_file)`
- **Operation:** Reads encounter files for preroll generation
- **File Pattern:** `encounter_*.json` (processes multiple files)
- **Description:** Generates pre-rolled values for encounters to speed up combat

### WRITE/UPDATE Operations

#### 6. update_encounter.py
**Function:** `update_encounter_file(encounter_id, updates)`
- **Operation:** Updates existing encounter JSON files
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Primary function for updating encounter state during combat (HP changes, status updates, turn progression)

#### 7. combat_manager.py
**Function:** `save_encounter(encounter_data)`
- **Operation:** Saves encounter state to JSON
- **File Pattern:** `encounter_{encounter_data['encounterId']}.json`
- **Description:** Persists encounter state after changes

**Function:** `end_encounter(encounter_id)`
- **Operation:** Marks encounter as completed and saves final state
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Finalizes encounter when combat ends

#### 8. action_handler.py
**Function:** `updateEncounter(encounter_id, changes)`
- **Operation:** Updates encounter through action system
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Action handler that processes encounter updates from DM responses

### UTILITY Operations

#### 9. save_game_manager.py
**Function:** `backup_encounter_files()`
- **Operation:** Creates backups of encounter files
- **File Pattern:** `encounter_*.json` → backup directory
- **Description:** Part of save game system, backs up all encounter files

**Function:** `restore_encounter_files(save_slot)`
- **Operation:** Restores encounter files from backup
- **File Pattern:** Restores `encounter_*.json` files
- **Description:** Restores encounter state when loading saved games

#### 10. encounter_old.py (Legacy)
**Function:** `load_encounter_legacy(encounter_id)`
- **Operation:** Legacy encounter loading (deprecated)
- **File Pattern:** `encounter_{encounter_id}.json`
- **Description:** Old encounter system, maintained for backward compatibility

#### 11. module_path_manager.py
**Function:** `get_encounter_path(encounter_id)`
- **Operation:** Utility to get encounter file paths
- **File Pattern:** Returns path to `encounter_{encounter_id}.json`
- **Description:** Provides consistent file path resolution for encounter files

## Data Flow Analysis

### Encounter Creation Flow
1. **DM Response** → `action_handler.py:createEncounter()`
2. **Action Handler** → `combat_builder.py:create_encounter_file()`
3. **Combat Builder** → Creates `encounter_{id}.json` in root directory

### Combat Update Flow
1. **DM Response** → `action_handler.py:updateEncounter()`
2. **Action Handler** → `update_encounter.py:update_encounter_file()`
3. **Update Function** → Modifies `encounter_{id}.json`

### Combat Management Flow
1. **Combat System** → `combat_manager.py:load_encounter()`
2. **Process Changes** → `combat_manager.py:save_encounter()`
3. **End Combat** → `combat_manager.py:end_encounter()`

## File Naming Conventions

### Pattern: `encounter_{location_id}-E{number}.json`
- **location_id**: Area identifier (e.g., TW05, B04, C01)
- **E{number}**: Encounter sequence (E1, E2, E3, etc.)
- **Examples**: 
  - `encounter_TW05-E1.json`
  - `encounter_B04-E1.json`
  - `encounter_C03-E2.json`

### Special Cases
- Root directory storage (not module-specific)
- Automatic ID generation based on current location
- Sequential numbering for multiple encounters in same location

## Key Integration Points

### With Main Game Loop
- `main.py` coordinates encounter creation through action handlers
- Combat state persists across game sessions via JSON files
- Real-time updates during combat maintained in files

### With Save System
- Encounter files included in save game backups
- State restoration preserves combat progress
- Module transitions preserve encounter history

### With XP System
- Completed encounters processed for experience awards
- Dead creatures trigger XP calculations
- Encounter outcomes affect character progression

## File Locations
- **Primary Storage**: Root directory (`/mnt/c/dungeon_master_v1/`)
- **Backup Storage**: Handled by save_game_manager.py
- **Schema**: `encounter_schema.json` defines structure
- **Examples**: 20+ encounter files currently exist in system

## Summary Statistics
- **Total Functions Identified**: 13
- **Files Involved**: 8 Python scripts
- **Operation Types**: CREATE (2), READ (4), WRITE/UPDATE (4), UTILITY (3)
- **Current Encounter Files**: 20+ active encounter files
- **Naming Pattern**: Consistent `encounter_{id}.json` format