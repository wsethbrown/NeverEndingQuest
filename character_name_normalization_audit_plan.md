# Character Name Normalization Audit Plan

## Objective
Conduct a comprehensive final pass through the entire codebase to ensure ALL functions that handle character names are using the consistent normalization approach.

## Search Patterns to Investigate
1. `.lower().replace(' ', '_')` - Direct character name formatting
2. `.replace("'", "")` - Apostrophe removal
3. `re.sub` patterns on character names
4. Custom character name formatting functions
5. Character file loading/saving operations
6. File path construction for characters

## Areas to Focus On
- Character creation functions
- Character loading functions  
- File path construction for characters
- Combat or encounter systems that handle character names
- Save/restore systems that might normalize names
- Any utility functions that format character names

## Expected Deliverables
1. Complete list of all files that handle character name normalization
2. Any remaining inconsistencies found
3. All fixes applied to ensure 100% consistency
4. Verification that the entire system now uses consistent normalization

## Process
1. Search entire codebase for character name manipulation patterns
2. Identify the centralized normalize_character_name() function
3. Find any functions not using the centralized approach
4. Update inconsistent functions
5. Verify all character file operations use consistent normalization
6. Generate final verification report