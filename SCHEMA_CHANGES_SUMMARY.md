# Character Schema Changes Summary

## Phase 1 Completed: Schema Updates

### 1. Enhanced classFeatures
Added optional `usage` tracking for limited-use abilities:
```json
"usage": {
  "current": 0,
  "max": 1,
  "refreshOn": "shortRest" // Options: shortRest, longRest, dawn, turn, bonus, action
}
```

### 2. Enhanced temporaryEffects
Added fields for better tracking of magical effects:
- `expiration`: ISO date-time format for automatic expiration
- `effectType`: Categorization (spell, potion, magic, environmental, other)
- Made `source` required

### 3. New injuries Array
For tracking physical damage separate from magical effects:
```json
{
  "type": "wound", // Options: wound, poison, disease, curse, other
  "description": "Piercing wound from giant rat bite",
  "damage": 4,
  "healingRequired": true,
  "source": "Giant Rat Attack"
}
```

### 4. New equipment_effects Array
Auto-calculated from equipped items:
```json
{
  "name": "Shield AC Bonus",
  "type": "bonus", // Options: bonus, resistance, immunity, advantage, disadvantage, other
  "target": "AC",
  "value": 2,
  "description": "Shield provides +2 AC",
  "source": "Shield"
}
```

### 5. Enhanced equipment Items
Added optional `effects` array to equipment:
```json
"effects": [
  {
    "type": "resistance",
    "target": "fear",
    "value": null,
    "description": "Resistance to fear effects"
  }
]
```

## What This Enables

1. **Proper Separation**: Temporary magical effects, injuries, and equipment bonuses are now properly separated
2. **Usage Tracking**: Class features can track limited uses (e.g., Second Wind 1/short rest)
3. **Auto-calculation**: Equipment effects can be automatically calculated from equipped items
4. **Time-based Expiration**: Temporary effects can expire based on game time
5. **Better Organization**: Clear categorization of different effect types

## Next Steps

Phase 2: Create the character effects validator script to:
- Migrate existing mixed effects to proper categories
- Calculate equipment effects from equipped items
- Set up usage tracking for class features
- Standardize duration formats to timestamps