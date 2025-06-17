# Player Storage System - Complete Implementation Plan

## Overview
This document outlines the implementation of a fully agentic player storage system that allows players to create and manage storage containers at specific locations using natural language descriptions.

## Core Design Philosophy

### Player-Initiated Storage
- Storage devices only become functional when players explicitly decide to use them
- No automatic conversion of location items into containers
- Player agency drives all storage creation and management

### Central Repository Architecture
- Single `player_storage.json` file tracks all player-created storage
- Separate from module files but tied to specific locations
- Persistent across sessions and module transitions

### Fully Agentic Processing
- Natural language descriptions processed by secondary AI (full model)
- Similar to updateCharacterInfo workflow
- AI converts descriptions to validated JSON operations

## Data Structure

### player_storage.json Schema
```json
{
  "version": "1.0.0",
  "lastUpdated": "2025-06-17T10:30:00.000000",
  "playerStorage": [
    {
      "id": "storage_001",
      "deviceType": "chest",
      "deviceName": "Gaol Storage Chest", 
      "locationId": "A15",
      "locationName": "Guard Post",
      "areaId": "SK001",
      "areaName": "Shadowfall Keep",
      "contents": [
        {
          "item_name": "Gold Coins",
          "item_type": "currency", 
          "quantity": 500,
          "description": "Standard gold coins"
        },
        {
          "item_name": "Ancient Arrows",
          "item_type": "ammunition",
          "quantity": 20,
          "description": "Arrows recovered from skeletal archer"
        }
      ],
      "createdBy": "Norn",
      "createdDate": "2025-06-17T10:15:00.000000",
      "accessibility": "party",
      "lastAccessed": "2025-06-17T10:30:00.000000",
      "accessLog": [
        {
          "character": "Norn",
          "action": "create",
          "timestamp": "2025-06-17T10:15:00.000000"
        },
        {
          "character": "Norn", 
          "action": "store_item",
          "item": "Gold Coins",
          "quantity": 500,
          "timestamp": "2025-06-17T10:30:00.000000"
        }
      ]
    }
  ]
}
```

### Storage Action Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["create_storage", "store_item", "retrieve_item", "view_storage"]
    },
    "character": {
      "type": "string",
      "description": "Character performing the action"
    },
    "storage_id": {
      "type": "string",
      "description": "Existing storage ID (for retrieve/view)"
    },
    "storage_type": {
      "type": "string", 
      "enum": ["chest", "lockbox", "barrel", "crate", "strongbox"],
      "description": "Type of storage container"
    },
    "storage_name": {
      "type": "string",
      "description": "Custom name for the storage container"
    },
    "location_id": {
      "type": "string",
      "description": "Location ID where storage is placed"
    },
    "location_description": {
      "type": "string",
      "description": "Natural language description of location"
    },
    "item_name": {
      "type": "string",
      "description": "Name of item to store/retrieve"
    },
    "quantity": {
      "type": "integer",
      "minimum": 1,
      "description": "Quantity to store/retrieve"
    }
  },
  "required": ["action", "character"],
  "allOf": [
    {
      "if": {"properties": {"action": {"const": "create_storage"}}},
      "then": {"required": ["storage_type", "location_description"]}
    },
    {
      "if": {"properties": {"action": {"const": "store_item"}}}, 
      "then": {"required": ["item_name", "quantity"]}
    },
    {
      "if": {"properties": {"action": {"const": "retrieve_item"}}},
      "then": {"required": ["storage_id", "item_name", "quantity"]}
    }
  ]
}
```

## Implementation Components

### 1. Core Files

#### storage_manager.py
- Core storage operations with atomic file protection
- Backup/restore functionality for data safety
- Schema validation for all operations
- Integration with character inventory system

#### storage_processor.py  
- Agentic AI processing for natural language descriptions
- Full model (not mini) for accurate interpretation
- Schema validation of generated operations
- Error handling and fallback responses

#### player_storage.json
- Central repository for all player storage
- Persistent across sessions and modules
- Atomic file operations with backup protection

### 2. Integration Points

#### action_handler.py
- Add `ACTION_STORAGE_INTERACTION` processing
- Route storage descriptions to storage_processor.py
- Execute validated operations through storage_manager.py
- Full error handling and rollback capabilities

#### location_manager.py
- Display available player storage when entering locations
- Show storage contents and accessibility
- Integration with location description system

### 3. AI Integration

#### System Prompt Updates
```
STORAGE SYSTEM:
Players can create storage containers at locations to organize their inventory.
When a player mentions storing items or using containers, recognize this as storage intent.
Pass natural language descriptions to the storage processor for validation.

Examples:
- "I store my extra gold in a chest in the gaol"
- "I put the ancient artifacts in a lockbox here"  
- "I retrieve my arrows from the storage we created"
- "What's in our chest at the tavern?"
```

#### Storage Processor AI Prompt
```
You are a storage operations specialist for a 5e RPG system. Convert natural language storage descriptions into valid JSON operations.

CONTEXT:
- Character data: {character_info}
- Current location: {location_info}
- Existing storage: {storage_info}

TASK: Convert this description into a valid storage operation:
"{storage_description}"

OUTPUT: Valid JSON matching the storage action schema.
```

## Workflow Examples

### Example 1: Create Storage and Store Items
1. **Player**: "I store my extra gold in a chest in the gaol"
2. **Main AI**: Recognizes storage intent, calls storage processor
3. **Storage Processor**: 
   ```json
   {
     "action": "create_storage",
     "character": "Norn",
     "storage_type": "chest",
     "storage_name": "Gaol Storage Chest",
     "location_description": "gaol",
     "item_name": "Gold Coins", 
     "quantity": 500
   }
   ```
4. **Storage Manager**: 
   - Creates backup of character file
   - Creates backup of storage file
   - Validates operation
   - Creates storage entry
   - Transfers gold from character to storage
   - Updates both files atomically

### Example 2: Retrieve Items
1. **Player**: "I get my arrows from the chest we made here"
2. **Storage Processor**:
   ```json
   {
     "action": "retrieve_item",
     "character": "Norn", 
     "storage_id": "storage_001",
     "item_name": "Ancient Arrows",
     "quantity": 10
   }
   ```
3. **Storage Manager**: Transfers arrows from storage to character inventory

### Example 3: View Storage
1. **Player**: "What's in our storage here?"
2. **Location Manager**: Displays available storage automatically
3. **Output**: "A chest here contains: Gold Coins (500), Ancient Arrows (20)"

## Safety & Data Protection

### Atomic File Operations
```python
def atomic_file_update(file_path, new_data):
    backup_path = f"{file_path}.backup_{timestamp}"
    
    try:
        # Create backup
        shutil.copy2(file_path, backup_path)
        
        # Validate new data
        validate_schema(new_data)
        
        # Write new data
        safe_json_dump(new_data, file_path)
        
        # Remove backup on success
        os.remove(backup_path)
        
    except Exception as e:
        # Restore backup on failure
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            os.remove(backup_path)
        raise e
```

### Character Inventory Protection
- Validate item exists before removal
- Verify quantities are sufficient
- Create character file backup before any modification
- Rollback character changes if storage operation fails

### Error Handling
- Schema validation for all operations
- Graceful handling of invalid requests
- Clear error messages for players
- Full operation rollback on any failure

## Testing Strategy

### Unit Tests
- Storage manager operations
- Schema validation
- Atomic file operations
- Error handling and rollback

### Integration Tests  
- Full workflow from player input to file updates
- Cross-module storage persistence
- Character inventory integration
- AI processing accuracy

### Gameplay Tests
- Real player scenarios
- Edge cases and error conditions
- Performance with large inventories
- Multi-character party storage

## Future Enhancements

### Phase 2 Features
- Lock mechanisms and keys
- Access permissions and ownership
- Container size limits and upgrades
- Security and trap systems

### Phase 3 Features
- Visual storage interface
- Advanced organization and categorization  
- Shared storage between locations
- Container crafting and customization

## Implementation Timeline

### Phase 1 (Core System)
1. Create documentation and schemas ✓
2. Implement storage_manager.py
3. Implement storage_processor.py
4. Update action_handler.py
5. Update location_manager.py
6. Basic testing and validation

### Phase 2 (AI Integration)
1. Update system prompts
2. Update validation prompts  
3. Integration testing
4. Performance optimization

### Phase 3 (Polish)
1. Error message improvements
2. Edge case handling
3. Documentation updates
4. Final testing and validation

This plan provides a complete roadmap for implementing a fully agentic, safe, and extensible player storage system that enhances gameplay while maintaining data integrity.