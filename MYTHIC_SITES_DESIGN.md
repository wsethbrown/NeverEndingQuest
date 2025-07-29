# Mythic Bastionland Sites System Design

## Overview

This document outlines the conversion from D&D 5e room-based module structure to Mythic Bastionland's Sites-based system for NeverEndingQuest.

## Current D&D Structure Analysis

### Keep of Doom Module (Total: ~40 locations)
- **HH001 (Harrow's Hollow)**: 6 locations - town with general store, square, gate, barracks, inn, tunnel
- **G001 (Gloamwood)**: 9 locations - haunted forest with various encounters
- **SK001 (The Keep)**: ~10 locations - outer keep structures  
- **TBM001 (Black Banner Mercenaries)**: ~5 locations - mercenary camp
- **TCD001 (Keep Depths)**: ~10 locations - dungeon interior

### Plot Structure
1. **PP001**: Shadows Over Harrow's Hollow (investigation)
2. **PP002**: The Road to Doom (forest journey)
3. **PP003**: Breach the Keep (enter keep)
4. **PP004**: The Heart of Darkness (confront Lord Greymont)
5. **PP005**: Resolution and Rewards (return to village)

## Mythic Bastionland Sites System

### Core Principles
1. **Abstract Exploration**: Sites represent meaningful encounters, not tactical maps
2. **Narrative Focus**: Each Site tells a story or presents a dilemma
3. **Discovery-Driven**: Sites revealed through exploration and investigation
4. **Shape Coding**: 
   - Circles = Settlements and civilized areas
   - Triangles = Dangers and dungeons
   - Diamonds = Special locations and mysteries

### Site Structure Schema
```json
{
  "siteId": "S01",
  "siteName": "Site Name",
  "siteType": "settlement|danger|mystery",
  "shape": "circle|triangle|diamond", 
  "gloryRequirement": 0,
  "description": "Detailed site description",
  "discoveries": [
    {
      "id": "D01",
      "name": "Discovery Name",
      "description": "What can be discovered here",
      "requirements": "How to unlock this discovery",
      "consequences": "What happens when discovered"
    }
  ],
  "encounters": [
    {
      "type": "social|combat|exploration|mystery",
      "description": "Encounter details",
      "outcomes": ["possible", "outcomes"]
    }
  ],
  "connections": ["S02", "S03"],
  "secrets": [
    {
      "description": "Hidden information",
      "revealConditions": "How to uncover"
    }
  ],
  "npcs": [
    {
      "name": "NPC Name", 
      "role": "Purpose in site",
      "attitude": "Initial disposition",
      "information": "What they know"
    }
  ]
}
```

## Keep of Doom Sites Conversion Plan

### Proposed 8-Site Structure

#### **Site 1: Harrow's Hollow** (Circle - Settlement)
- **Consolidates**: HH001 A01-A06 (6 locations)
- **Focus**: Investigation hub, gathering information and resources
- **Key NPCs**: Elder Mirna, Sergeant Feld, Cira the Innkeeper
- **Primary Discovery**: The bronze key and Scout Elen's disappearance
- **Connection Mechanic**: Information gathering unlocks forest path

#### **Site 2: The Witchlight Trail** (Triangle - Danger) 
- **Consolidates**: G001 B01-B04 (forest approach)
- **Focus**: Treacherous journey with spectral encounters
- **Key Challenge**: Navigate haunted forest, avoid or confront spirits
- **Primary Discovery**: Signs of Scout Elen's passage and the failing ward circle

#### **Site 3: The Broken Ward Circle** (Diamond - Mystery)
- **Consolidates**: G001 B05-B06 (magical locations)
- **Focus**: Ancient protective magic, choice to restore or bypass
- **Key Challenge**: Understanding and potentially repairing the ward
- **Primary Discovery**: The source of the keep's growing influence

#### **Site 4: The Keeper's Hermitage** (Circle - Settlement)
- **Consolidates**: G001 B07-B09 (hermit area)
- **Focus**: Gaining crucial knowledge about the keep's curse
- **Key NPC**: The Keeper (hermit with deep lore)
- **Primary Discovery**: The true nature of Lord Greymont's corruption

#### **Site 5: The Keep's Shadow** (Triangle - Danger)
- **Consolidates**: SK001 C01-C05 (outer keep)
- **Focus**: Breaching the keep's defenses and mercenary complications
- **Key Challenge**: Deal with Black Banner Mercenaries, find entry
- **Primary Discovery**: Multiple paths into the keep interior

#### **Site 6: The Cursed Halls** (Triangle - Danger)
- **Consolidates**: TCD001 D01-D05 (upper keep interior)
- **Focus**: Navigate haunted keep interior, uncover the curse's history
- **Key Challenge**: Spectral guardians and trapped corridors
- **Primary Discovery**: Lord Greymont's tragic history and the shadow relic

#### **Site 7: The Heart of Darkness** (Diamond - Mystery)
- **Consolidates**: TCD001 D06-D10 (keep depths)
- **Focus**: Confront the source of the curse
- **Key Challenge**: Face Lord Greymont's corrupted spirit
- **Primary Discovery**: The shadow relic and its destruction/purification

#### **Site 8: The Aftermath** (Circle - Settlement)
- **Returns to**: Harrow's Hollow transformed
- **Focus**: Resolution, consequences of choices, rewards
- **Key Change**: Village atmosphere based on success/failure
- **Primary Discovery**: Long-term effects of the adventure

## Implementation Strategy

### Phase 1: Schema and Generator Updates
1. Create Sites-based JSON schema
2. Update module generators to create Sites instead of rooms
3. Implement Site discovery mechanics
4. Create Site navigation system

### Phase 2: Conversion Tools
1. Build converter to transform existing D&D modules to Sites
2. Create AI prompts for Site-based content generation
3. Implement discovery-based progression system
4. Update plot tracking for Site-based adventures

### Phase 3: Game Integration
1. Update game interface for Sites display
2. Implement Site-based exploration mechanics
3. Create Sites-aware save/load system
4. Update AI prompts for Sites-based storytelling

## Key Design Decisions

### Discovery vs. Mapping
- **Old System**: Players map rooms and connections
- **New System**: Players discover Sites through investigation and choices
- **Benefit**: More narrative focus, less tactical complexity

### Abstracted Scale
- **Old System**: "You are in room A01, connected to A02"
- **New System**: "You explore the settlement and discover three key areas of interest"
- **Benefit**: Faster pacing, emphasis on meaningful encounters

### Choice-Driven Progression  
- **Old System**: Linear progression through connected rooms
- **New System**: Discoveries unlock new Sites and progression paths
- **Benefit**: Player agency, multiple solution paths

### Compressed Content
- **Old System**: 40+ individual locations with detailed tactical maps
- **New System**: 8 meaningful Sites with rich narrative content
- **Benefit**: Easier to run, more focused storytelling

## Migration Path

### Existing Modules
- Keep current D&D modules for backward compatibility
- Mark as "Legacy" in module selection
- Provide conversion option to Sites format

### New Modules
- Generate only in Sites format
- Focus on Mythic Bastionland themes and mechanics
- Utilize Knight archetypes and Glory system

### User Experience
- Seamless transition between module types
- Clear indication of module format
- Conversion tools for user-created content

## Success Metrics

1. **Narrative Engagement**: Sites should create memorable story moments
2. **Pacing**: Adventures should complete in 2-4 sessions
3. **Player Agency**: Multiple paths to achieve objectives
4. **Replayability**: Different discoveries on subsequent playthroughs
5. **Ease of Use**: GMs can run Sites without extensive preparation

This design preserves the core adventure experience while embracing Mythic Bastionland's more narrative-focused approach to exploration and discovery.