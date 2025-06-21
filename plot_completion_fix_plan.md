# Plot Completion Check Fix Plan

## Problem Identified
The game's module completion check is only examining the current module's plot data instead of checking all available modules. This causes premature suggestions to create new modules when other existing modules still have incomplete plot points.

## Root Cause Analysis
1. **Line 939 in main.py**: `plot_data_for_note = load_json_file(path_manager.get_plot_path())`
   - Only loads plot data from the current module's path
   - Current module from party_tracker: 'Silver_Vein_Whispers'
   - But debug shows loading from: 'modules/Keep_of_Doom/module_plot.json'

2. **Lines 997-1010 in main.py**: Plot completion check logic
   - Only examines `plot_data_for_note` (single module's data)
   - Should check ALL modules before suggesting module creation

3. **ModulePathManager fallback**: Defaults to "Keep_of_Doom" when errors occur

## Solution Implementation

### Step 1: Create All-Modules Plot Checker Function
Create `check_all_modules_plot_completion()` function that:
- Scans all module directories in `modules/` folder
- Loads each module's `module_plot.json` file  
- Analyzes plot point completion status
- Returns comprehensive completion data

### Step 2: Update Main.py Logic
Replace current single-module check (lines 992-1010) with:
- Call to new all-modules checker function
- Enhanced debug output showing all modules' status
- Only suggest module creation when ALL modules are complete

### Step 3: Debug Path Manager Issue
- Investigate why path_manager defaults to Keep_of_Doom
- Ensure proper module detection from party_tracker.json
- Add additional debug logging for module initialization

### Step 4: Testing
- Verify debug output shows correct modules being checked
- Confirm no premature module creation suggestions
- Test with multiple modules having different completion states

## Expected Behavior After Fix
- System will check plot completion for ALL available modules
- Module creation prompt will only appear when ALL modules are complete
- Debug output will clearly show which modules are incomplete
- Proper module detection from party_tracker.json

## Files to Modify
1. `main.py` - Update module completion check logic (lines 985-1075)
2. Possibly `module_path_manager.py` - If initialization issues found

## Success Criteria
- [ ] All modules' plot completion status is checked
- [ ] Module creation prompt only appears when appropriate
- [ ] Debug output clearly shows completion status per module
- [ ] No premature module creation suggestions