# Campaign Generator Investigation Plan - COMPLETE

## Objective ✓ COMPLETED
Find and analyze the campaign generator code that's creating individual plot files instead of the centralized module_plot.json structure.

## Current Issue ✓ IDENTIFIED
- Generator is creating plot_*.json files (like plot_GV001.json, plot_VW001.json)
- Should be creating centralized module_plot.json files per module
- Wrong architecture conflicts with module-centric design

## Investigation Results ✓ COMPLETE

### ROOT CAUSE IDENTIFIED:
**File: /mnt/c/dungeon_master_v1/module_builder.py**
**Line 374:** `self.save_json(plot_data, f"plot_{area_id}.json")`

### The Problem:
The `ModuleBuilder.generate_plots()` method creates individual plot files per area:
```python
def generate_plots(self):
    """Generate plot files for each area"""
    for area_id in self.areas_data:
        # ... generates plot for area ...
        self.plots_data[area_id] = plot_data
        self.save_json(plot_data, f"plot_{area_id}.json")  # ← THIS IS THE PROBLEM
```

### Current Architecture Status:
✅ **GOOD NEWS**: Silver_Vein_Whispers module ALREADY HAS correct centralized structure!
- `/mnt/c/dungeon_master_v1/modules/Silver_Vein_Whispers/module_plot.json` exists and is properly formatted
- Contains unified plot points across all areas (SR001, WR001, RC001)
- Each plot point has proper areaId field linking to specific areas

❌ **BAD NEWS**: The generator still creates BOTH structures:
- Individual files: `plot_RC001.json`, `plot_SR001.json`, `plot_WR001.json` (wrong)
- Centralized file: `module_plot.json` (correct)

### Files Creating Wrong Architecture:

1. **module_builder.py:374** - Main culprit creating individual plot files
2. **module_generator.py:930** - Has method `generate_unified_plot_file()` that creates correct structure
3. **plot_generator.py:520** - Can create individual plot files when used standalone

### Module Status Analysis:
Current modules show BOTH architectures exist side-by-side:
- ✅ `module_plot.json` (correct centralized structure)
- ❌ `plot_*.json` files (incorrect individual files)

## Module-Centric Architecture Requirement ✓ VERIFIED
Each module should have:
- ✅ modules/[module_name]/module_plot.json (centralized) - EXISTS
- ❌ NOT individual plot_*.json files per area/location - THESE STILL EXIST