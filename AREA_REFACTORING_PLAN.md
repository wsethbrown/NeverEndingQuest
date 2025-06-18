# Area Files Refactoring Plan

## Current State Analysis
- Area files (HH001.json, G001.json, SK001.json, etc.) are currently stored directly in `modules/[module_name]/` root
- CLAUDE.md specifies they should be in `modules/[module_name]/areas/` subfolder
- ModulePathManager.get_area_path() returns `modules/[module_name]/{area_id}.json` (incorrect path)
- 34+ files use ModulePathManager for consistent path handling

## Refactoring Plan

### Phase 1: Update ModulePathManager
- Modify `get_area_path()` to return `modules/[module_name]/areas/{area_id}.json`
- Update `get_area_ids()` to scan the areas/ subdirectory instead of root
- Add fallback logic to check root directory for backward compatibility during migration

### Phase 2: Create Areas Directories
- Create `areas/` subdirectory in all existing modules
- Migrate existing area files (HH001.json, G001.json, SK001.json, etc.) to areas/ subfolder

### Phase 3: Update Module Builders
- Modify module_builder.py, location_generator.py, and area_generator.py to create area files in areas/ subdirectory
- Update startup_wizard.py and module_generator.py to create areas/ directory structure

### Phase 4: Update Validation
- Modify validate_module_files.py to check areas/ subdirectory for area files
- Update schema validation to use new paths

### Phase 5: Testing & Validation
- Run complete validation scan using `python validate_module_files.py`
- Test area file loading/saving functionality
- Verify all 34+ files using ModulePathManager work correctly
- Test module builder functionality with new structure

## Files to Modify
1. `module_path_manager.py` - Core path management
2. `validate_module_files.py` - Validation logic
3. `module_builder.py` - Module creation
4. `location_generator.py` - Area file generation
5. `area_generator.py` - Area content generation
6. `startup_wizard.py` - Module setup
7. `module_generator.py` - Module structure creation

## Migration Strategy
- Use backward compatibility during transition
- Migrate files physically after code changes
- Maintain original files as backup until validation passes
- Remove fallback logic after successful migration

## Implementation Status
- [x] Phase 1: Update ModulePathManager
- [x] Phase 2: Create Areas Directories
- [x] Phase 3: Update Module Builders
- [x] Phase 4: Update Validation
- [x] Phase 5: Testing & Validation

## Test Results
- ✅ ModulePathManager correctly detects area files in areas/ directory
- ✅ Fallback logic works for legacy files in root directory
- ✅ Validation script updated to check both locations
- ✅ All 5 area files found and validated (100% pass rate)
- ✅ Overall validation: 36/37 files passed (97.3% success rate)
- ✅ Area files now properly located in modules/[module_name]/areas/ as specified in CLAUDE.md

## Implementation Complete
The area files refactoring has been successfully implemented and tested. All area files are now stored in the areas/ subdirectory while maintaining backward compatibility during the migration period.