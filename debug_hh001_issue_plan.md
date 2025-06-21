# Plan: Debug HH001 Hardcoding/Caching Issue

## Objective
Find where HH001 (Harrow's Hollow) is being incorrectly referenced, causing the system to load it from Silver_Vein_Whispers module instead of Keep_of_Doom module.

## Search Strategy

1. **Search for hardcoded "HH001" references**
   - Look for string literals containing "HH001"
   - Check for any default values set to "HH001"

2. **Examine caching mechanisms**
   - Look for cache files or functions that might store location data
   - Check for persistent storage of area IDs

3. **Track current area tracking**
   - Search for "currentAreaId", "current_area", "current_location" variables
   - Look for functions that set or get current area

4. **Analyze conversation_utils.py**
   - Focus on lines 180-212 as mentioned
   - Check area/location handling logic

5. **Check ModulePathManager**
   - Look for area path resolution logic
   - Check for any module context issues

6. **Review area/map loading functions**
   - Find functions that load area files
   - Check for incorrect module context

## Files to examine
- conversation_utils.py
- module_path_manager.py
- action_handler.py
- party_tracker.json
- Any cache files