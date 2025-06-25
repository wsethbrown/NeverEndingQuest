# Location ID Audit Plan

## Objective
Collect all location IDs currently in use across all three campaign modules to identify conflicts and create a comprehensive list.

## Modules to Audit
1. **Keep_of_Doom** - Area files: G001.json, HH001.json, SK001.json, TBM001.json, TCD001.json
2. **The_Thornwood_Watch** - Area files: NCW001.json, RO001.json, TW001.json  
3. **Silver_Vein_Whispers** - Area files: RC001.json, SR001.json, WR001.json

## Process
1. Search each area file for "locationId" fields
2. Extract all location IDs used in each module
3. Compile comprehensive list by module
4. Identify any conflicts/duplicates between modules
5. Generate final report

## Expected Output
- Module-by-module location ID listing
- Conflict identification
- Comprehensive master list