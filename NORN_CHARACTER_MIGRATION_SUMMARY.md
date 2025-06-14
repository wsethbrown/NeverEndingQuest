# Norn Character File Migration Summary

## Changes Made to Match New Schema

### 1. Class Features Enhanced
- **Second Wind**: Added usage tracking (current: 0, max: 1, refreshOn: "shortRest")
- **Action Surge**: Added usage tracking (current: 1, max: 1, refreshOn: "shortRest")

### 2. Temporary Effects Cleaned
**Removed (not magical effects):**
- Second Wind status (moved to class feature usage)
- Knight's Heart Amulet effect (moved to equipment_effects)
- All physical wounds (piercing, acid, cold damage)

**Enhanced remaining effects with:**
- `expiration` timestamps based on game time
- `effectType` set to "magic" for all

**Current temporaryEffects:**
1. Spiritual Fortitude (expires 1492-03-03T07:39:00)
2. Blessing of the Forest Guardian (expires 1492-03-03T07:39:00)
3. Ward's Favor (expires 1492-03-03T07:39:00)
4. Blessing of the Restored Shrine (expires 1492-03-02T15:39:00)

### 3. New Arrays Added
**injuries**: Empty array (physical wounds don't count as effects)

**equipment_effects**: Auto-calculated from equipment
- Knight's Heart Amulet - Fear Resistance
- Knight's Heart Amulet - Necrotic Resistance
- Fighting Style: Defense (+1 AC)
- Shield AC Bonus (+2 AC)

### 4. Equipment Enhanced
**Knight's heart amulet**: Added effects array with fear and necrotic resistance

## Key Insights

1. **Physical damage** (wounds) are NOT effects - they're just HP loss
2. **Injuries array** should be for ongoing conditions like:
   - Poison (ongoing damage)
   - Disease (stat penalties)
   - Curses (magical afflictions)
   - Conditions that persist beyond immediate damage

3. **Equipment effects** are now properly tracked separately from temporary effects
4. **Class features** with limited uses now have proper tracking

## Testing Notes
- File validates as proper JSON
- All required fields present
- Ready for testing with the effects validator script