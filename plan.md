# Plan: Add Duplicate NPC Removal to Main Game Loop

## Objective
Remove duplicate NPCs from party_tracker.json on each game loop iteration to prevent issues like having multiple "Corrupted Ranger Thane" entries.

## Implementation Steps

1. **Create a deduplicate function**
   - Add a new function `remove_duplicate_npcs()` that:
     - Takes party_tracker_data as input
     - Removes duplicate NPCs based on name (keeping first occurrence)
     - Returns the cleaned data and a boolean indicating if changes were made

2. **Integrate into main game loop**
   - Add the deduplication check after loading party_tracker.json at line 1674
   - Save the cleaned data back to file if changes were made
   - Add debug logging to track when duplicates are removed

3. **Testing**
   - Verify duplicate NPCs are removed
   - Ensure first occurrence is kept
   - Check that the cleaned data is properly saved

## Key Locations
- Main game loop: line 1674 where party_tracker_data is loaded
- New function will be added near other utility functions
- Integration point: right after loading party tracker in the game loop