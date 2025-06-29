# Spell Tooltip Implementation Plan

## Overview
Add hover tooltips to spell names in the "spells & magic" tab that display spell descriptions from the spell_repository.json file.

## Current State Analysis

### Game Interface Structure
- **Main HTML**: `/mnt/c/dungeon_master_v1/templates/game_interface.html`
- **Spell Display Function**: `displaySpellsAndMagic(data)` function in the HTML file
- **Spell CSS**: `/mnt/c/dungeon_master_v1/static/css/original-spells.css`
- **Spell Repository**: `/mnt/c/dungeon_master_v1/spell_repository.json`

### Current Spell Display
- Spells are displayed in `.spell-item` containers
- Each spell has a `.spell-name` element containing the spell name
- Already has hover effect: background color change on `.spell-item:hover`
- Spells are grouped by level (cantrips, level1, level2, etc.)

### Spell Repository Structure
```json
{
  "acid_splash": {
    "name": "Acid Splash",
    "level": 0,
    "school": "Conjuration",
    "description": "You hurl a bubble of acid...",
    "components": {...},
    "duration": "Instantaneous",
    ...
  }
}
```

## Implementation Plan

### Step 1: Add Tooltip CSS Styles
- Add tooltip container and styling to spell CSS
- Create tooltip positioning and animation
- Ensure tooltip works with dark theme

### Step 2: Load Spell Repository Data
- Add endpoint to web_interface.py to serve spell repository data
- Create JavaScript function to fetch and cache spell data
- Handle spell name normalization (spaces, capitalization)

### Step 3: Modify Spell Display
- Update `displaySpellsAndMagic()` function to add tooltip data attributes
- Add tooltip creation and positioning logic
- Implement show/hide tooltip on hover

### Step 4: Handle Edge Cases
- Unknown spells (not in repository)
- Long descriptions (truncation/scrolling)
- Tooltip positioning near screen edges
- Mobile responsiveness

## Files to Modify

### 1. `/mnt/c/dungeon_master_v1/static/css/original-spells.css`
- Add tooltip styles
- Position tooltip relative to spell item

### 2. `/mnt/c/dungeon_master_v1/templates/game_interface.html`
- Modify `displaySpellsAndMagic()` function
- Add spell tooltip JavaScript functionality
- Load spell repository data

### 3. `/mnt/c/dungeon_master_v1/web_interface.py`
- Add endpoint to serve spell repository data

## Technical Considerations

### Spell Name Matching
- Handle case differences (e.g., "Acid Splash" vs "acid_splash")
- Handle spaces vs underscores
- Fallback for spells not found in repository

### Performance
- Cache spell repository data in browser
- Only load repository once per session
- Efficient spell lookup using normalized names

### Accessibility
- Ensure tooltips work with keyboard navigation
- Add ARIA labels for screen readers
- Provide alternative access to spell descriptions

## Implementation Steps

1. **Add CSS tooltip styles** - Create tooltip appearance and positioning
2. **Create spell repository endpoint** - Server-side spell data access
3. **Implement tooltip JavaScript** - Client-side tooltip functionality
4. **Update spell display function** - Add tooltip data to spell elements
5. **Test and refine** - Handle edge cases and polish UX

## Expected Behavior

When a user hovers over a spell name in the "spells & magic" tab:
1. Tooltip appears showing spell description
2. Tooltip includes key spell information (level, school, components, duration)
3. Tooltip is positioned to not overlap with other UI elements
4. Tooltip disappears when cursor moves away
5. Fallback message for spells not found in repository