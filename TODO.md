# Mythic Bastionland Conversion TODO List

## HIGH PRIORITY - Core System Integration

### Character System Updates
- [x] Create `core/validation/mythic_character_validator.py` for mythic schema validation
- [x] Create `utils/mythic_startup_wizard.py` for Knight character creation
- [ ] Update `core/ai/action_handler.py` for Virtue-based saves and mechanics
- [ ] Update `core/validation/dm_response_validator.py` for Mythic Bastionland rules
- [ ] Replace old character_validator.py usage with mythic_character_validator.py

### Combat System Integration  
- [ ] Integrate mythic combat prompt into combat manager
- [ ] Update combat validation to use Guard/Vigour instead of HP/AC
- [ ] Test simultaneous combat resolution

### Module Generation Updates
- [ ] Update `core/generators/npc_builder.py` to generate Knights instead of D&D classes
- [ ] Update `core/generators/monster_builder.py` for Mythic Bastionland creatures
- [ ] Update `core/generators/module_generator.py` to remove D&D references
- [ ] Update `prompts/generators/npc_builder_prompt.txt` for Knight generation

## MEDIUM PRIORITY - System Replacement

### Legacy System Removal
- [ ] Remove/deprecate `utils/xp.py` (replaced by glory_system.py)
- [ ] Remove/deprecate `core/managers/level_up_manager.py` (no leveling in Mythic Bastionland)
- [ ] Remove/deprecate `prompts/leveling/` directory (obsolete)
- [ ] Remove/deprecate `utils/level_up.py` (legacy)

### Integration Updates
- [ ] Update `main.py` to use Glory system instead of XP
- [ ] Update all imports from removed files
- [ ] Create migration scripts for existing saves
- [ ] Update configuration files

## LOW PRIORITY - Interface & Documentation

### Web Interface Updates
- [ ] Update `web/templates/game_interface.html` for Virtues/Guard/Glory display
- [ ] Update `web/web_interface.py` endpoints for new system
- [ ] Update real-time character display

### Documentation Updates
- [ ] Update CLAUDE.md to reflect Mythic Bastionland instead of SRD 5.2.1
- [ ] Update README.md for new system
- [ ] Create user migration guide
- [ ] Update architecture documentation

## TESTING & VALIDATION

### Core Testing
- [ ] Test Knight character creation with different starts (Wanderer/Courtier/Ruler)
- [ ] Test combat flow with simultaneous resolution
- [ ] Test Glory system awarding and rank progression
- [ ] Test module generation with Mythic Bastionland content

### Integration Testing  
- [ ] Test save compatibility and migration
- [ ] Test web interface with new character system
- [ ] Test AI prompt consistency across system
- [ ] Performance testing with new mechanics

## CONTENT INTEGRATION

### Data Files (COMPLETED ✅)
- [x] Convert all 72 Knights to JSON format (`data/mythic_knights.json`)
- [x] Convert all 72 Myths + City Quest to JSON format (`data/mythic_myths.json`) 
- [x] Remove duplicate entries from data files
- [x] Validate all official content is present

### Generator Integration
- [ ] Integrate mythic selectors (`utils/mythic_selectors.py`) into content generation
- [ ] Update encounter generation for Mythic Bastionland creatures
- [ ] Update treasure/trade generation for barter system (no gold coins)

## ARCHITECTURE IMPROVEMENTS

### Error Handling
- [ ] Add validation for Mythic Bastionland rule compliance
- [ ] Add error handling for missing mythic content
- [ ] Add backwards compatibility warnings

### Performance
- [ ] Optimize Glory system calculations
- [ ] Optimize mythic content lookups
- [ ] Profile new system vs old system performance

---

**Notes:**
- Never delete completed items, just mark with [x]
- Add new items as they are discovered
- Update priority levels based on dependencies
- Maintain detailed progress in PROGRESS.md