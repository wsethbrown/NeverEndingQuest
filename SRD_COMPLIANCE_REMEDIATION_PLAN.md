# SRD 5.2.1 Compliance Remediation Plan

## Overview
This plan addresses compliance with SRD 5.2.1 Creative Commons licensing requirements by removing trademarked terms and ensuring proper attribution throughout the dungeon master game codebase.

## Issues Identified

### Critical Trademark Violations
**Files with "D&D" or "Dungeons & Dragons" references that must be updated:**

#### **High Priority System Files:**
1. **system_prompt.txt** - Core AI prompt with "Dungeons & Dragons 5th Edition Dungeon Master"
2. **character_validator.py** - Multiple "D&D 5e" references in header and code
3. **build_spell_repository.py** - "D&D 5e" references without proper SRD attribution
4. **modify.py** - "Dungeons & Dragons 5th Edition" reference
5. **module_creation_prompt.txt** - "D&D" references in AI prompts
6. **combat_validation_prompt.txt** - Trademark references

#### **Medium Priority Game Files:**
7. **main.py** - Core game loop with potential D&D references
8. **module_builder.py** - Module generation with D&D references
9. **action_handler.py** - Action processing with potential violations
10. **save_game_manager.py** - Save system with potential references

#### **Low Priority Files:**
11. **Test files** (6 files): test_npc_visual_formatting.py, etc.
12. **Backup files** (3 files): system_prompt_backup_20250617_220158.txt, etc.

## Compliance Requirements

### SRD 5.2.1 Standards
- ✅ **Replace "D&D"** → "5th edition"
- ✅ **Replace "D&D 5e"** → "5th edition" 
- ✅ **Replace "Dungeons & Dragons"** → "5th edition" or "the world's most popular role-playing game"
- ✅ **Add SRD Attribution** → `"_srd_attribution": "Portions derived from SRD 5.2.1, CC BY 4.0"`

### Required Attribution Locations
- Files using armor, weapon, spell, or monster data from SRD
- AI prompts that reference 5th edition game rules
- Generated content templates using SRD mechanics

## Implementation Strategy

### Phase 1: Critical System Files (Immediate)
Focus on files that directly impact AI behavior and user-facing content:
- system_prompt.txt (main AI personality and rules)
- character_validator.py (character data validation)
- build_spell_repository.py (spell data processing)
- modify.py (character modification system)
- module_creation_prompt.txt (content generation)
- combat_validation_prompt.txt (combat rule validation)

### Phase 2: Core Game Files (High Priority)
Update remaining core game functionality:
- main.py (game loop controller)
- module_builder.py (content generation)
- action_handler.py (command processing)
- save_game_manager.py (persistence system)

### Phase 3: Supporting Files (Medium Priority)
Complete remaining files for consistency:
- Test files (ensure test scenarios are compliant)
- Backup files (maintain consistency across versions)

### Phase 4: Validation (Final)
- Search entire codebase for remaining trademark violations
- Verify SRD attribution is present where required
- Test AI prompts generate compliant content
- Ensure no trademarked terminology in user output

## Expected Outcomes
- Complete removal of trademarked terms from all game files
- Proper SRD 5.2.1 attribution on all SRD-derived content
- Full compliance with Creative Commons CC BY 4.0 licensing
- Maintained functionality with legally compliant terminology

## Success Criteria
- Zero trademark violations in codebase search results
- All SRD content properly attributed
- AI generates only SRD-compliant content
- Legal compliance maintained while preserving game functionality

## Timeline
- **Phase 1**: Immediate (critical system files)
- **Phase 2**: Same session (core game files)  
- **Phase 3**: Same session (supporting files)
- **Phase 4**: Final validation and testing

This remediation ensures full SRD 5.2.1 compliance while maintaining the sophisticated architecture and functionality of the dungeon master system.