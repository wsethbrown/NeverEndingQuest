# Search Plan: Find Missing Plot Files for Keep of Doom Areas

## Objective
Find missing plot files for Keep of Doom areas: G001, SK001, TBM001, and TCD001. We currently only have plot_HH001_BU.json and need to locate clean backup versions of the other plot files.

## Search Strategy
1. Search for plot files with patterns:
   - plot_G001.json or similar
   - plot_SK001.json or similar  
   - plot_TBM001.json or similar
   - plot_TCD001.json or similar

2. Search locations:
   - Other module directories under /mnt/c/dungeon_master_v1/modules/
   - Backup directories
   - Root directory and subdirectories

3. Criteria for clean versions:
   - No "Norn" references (player contamination)
   - No completed quest states
   - Most recent timestamps

## Files to Find
- plot_G001.json (Goblin area)
- plot_SK001.json (Skeleton area)
- plot_TBM001.json (Tomb area)
- plot_TCD001.json (Crypt area)

## Next Steps
Once found, report exact file paths for copying to Keep_of_Doom module as backups.