# Campaign-to-Module Conversion Plan

## Overview
Converting the existing campaign system to a module-based architecture where:
- Current "campaigns" become "modules" (self-contained adventures)
- A new campaign layer will link multiple modules together
- Keep of Doom is the test module for this conversion

## Current State Assessment ✅
- `modules/` directory created
- Keep_of_Doom data moved to `modules/Keep_of_Doom/`
- `Keep_of_Doom_module.json` created with proper module data
- Module builder files created but still use campaign terminology
- Git shows many campaign files deleted (D status) and new module files (?)

## Conversion Tasks

### Phase 1: Schema and Core Files ⏳

#### 1. Update module_schema.json
**Status**: Pending  
**Priority**: High  
**Current Issue**: Schema still uses "campaignName", "campaignDescription" etc.  
**Task**: 
- Change `campaignName` → `moduleName`
- Change `campaignDescription` → `moduleDescription` 
- Update all campaign references to module
- Add module-specific metadata (author, level range, play time)
- Add module connection points for campaign linking

#### 2. Refactor module_builder.py
**Status**: Pending  
**Priority**: High  
**Current Issue**: File is copy of campaign_builder.py with campaign terminology  
**Task**:
- Rename class `CampaignBuilder` → `ModuleBuilder`
- Update imports to use module generators
- Change `BuilderConfig.campaign_name` → `BuilderConfig.module_name`
- Update all method names and variables from campaign → module
- Focus on single module generation vs multi-area campaigns
- Remove campaign-level orchestration logic

#### 3. Update module_context.py  
**Status**: Pending  
**Priority**: High  
**Current Issue**: Unknown state, likely has campaign references  
**Task**:
- Change class `CampaignContext` → `ModuleContext`  
- Update all properties and methods to use module terminology
- Add module-specific context handling

#### 4. Update module_generator.py
**Status**: Pending  
**Priority**: Medium  
**Current Issue**: Unknown state, likely has campaign references  
**Task**:
- Change class `CampaignGenerator` → `ModuleGenerator`
- Update generation logic to focus on module creation
- Remove campaign-level world building (that goes to campaign layer)

### Phase 2: Module System Updates ⏳

#### 5. Update existing module files
**Status**: Pending  
**Priority**: Medium  
**Task**:
- Update `modules/Keep_of_Doom/module_context.json` terminology
- Ensure all module files use consistent naming
- Clean up any remaining campaign references in module data

#### 6. Create campaign linking system (Future)
**Status**: Not Started  
**Priority**: Low (Phase 2)  
**Task**:
- Design campaign schema that links modules
- Create campaign builder that imports modules
- Handle module interconnections and plot linking

### Phase 3: Testing and Validation ⏳

#### 7. Test module builder
**Status**: Pending  
**Priority**: Medium  
**Task**:
- Run `test_module_builder.py` to verify functionality
- Generate a test module using new module builder
- Validate output matches expected module schema

#### 8. Integration testing
**Status**: Pending  
**Priority**: Medium  
**Task**:
- Test loading Keep_of_Doom module in game system
- Verify all file paths and references work
- Ensure game mechanics still function with module structure

## Implementation Order ✅ COMPLETED

1. ✅ **module_schema.json** - Foundation for everything else
2. ✅ **module_builder.py** - Core generation system  
3. ✅ **module_context.py** - Supporting context system
4. ✅ **module_generator.py** - Core generator
5. ✅ **Test and validate** - Ensure system works
6. ⏳ **Clean up** - Remove unused campaign files (Future task)

## Key Decisions Made

- Keep of Doom is treated as a complete module
- Module = self-contained adventure (areas + plot + NPCs + monsters)
- Campaign = collection of linked modules (future enhancement)
- Preserve all existing game functionality during conversion

## Files Changed
- ✅ Created: `modules/Keep_of_Doom/` directory structure
- ✅ Created: `Keep_of_Doom_module.json`
- ⏳ Update: `module_schema.json`
- ⏳ Update: `module_builder.py` 
- ⏳ Update: `module_context.py`
- ⏳ Update: `module_generator.py`
- ⏳ Test: `test_module_builder.py`

## Notes for Future Campaign System

When ready to implement campaign linking:
- Campaign schema should reference module IDs
- Campaign plot connects module plots via NPCs/events
- Module import/export system for sharing
- Campaign builder orchestrates module sequence
- Handle level progression across modules

## Recovery Information

If system crashes during conversion:
- Module files are in `modules/Keep_of_Doom/`
- Schema needs campaign→module terminology update
- Builder files need refactoring from campaign focus to module focus  
- Test with Keep of Doom module once conversion complete