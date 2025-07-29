# Mythic Bastionland Sites System Design (Corrected)

## Overview

This document outlines the correct implementation of Mythic Bastionland's Sites system for detailed exploration within NeverEndingQuest modules.

## Understanding Sites in Mythic Bastionland

### What Sites Are (Official Definition)
"A Knight's journey largely focuses on travelling great distances to seek the guidance of Seers and uncover Myths. However, on occasion there may be the need to zoom in on a single Hex, or a specific site within a Hex, in more detail."

Sites are detailed exploration areas using the **7-Point Hex Method** for locations that warrant more detailed exploration than simple hex descriptions.

### When to Use Sites (From Rulebook)
- Ancient tombs
- Hostile castles  
- Twisting caverns
- Misty woods spanning the entire Hex
- Any area within a Hex that needs detailed exploration

## The 7-Point Hex Method (Official Rules)

### Step 1: Create Points
1. Draw 6 points as corners of a hexagon, with a 7th in the center
2. Mark 3 points with **circles** (features that give information or set mood)
3. Mark 2 points with **triangles** (dangers to be navigated carefully)  
4. Mark 1 point with **diamond** (treasure, useful or valuable find)
5. **Erase the final point** and assign numbers to remaining 6 points

### Step 2: Create Routes
1. Draw **3 open routes** with solid line (straightforward paths)
2. Draw **2 closed routes** with crossed line (something blocks the way)
3. Draw **1 hidden route** with dotted line (found through exploration)
4. Ensure all points can be reached even if routes are closed/secret
5. Place entrance at any point, plus optional hidden entrance

## Site Structure Schema

```json
{
  "siteId": "SITE001",
  "siteName": "The Cursed Halls",
  "siteDescription": "Ancient keep interior with spectral guardians",
  "entrances": {
    "main": 1,
    "hidden": 4
  },
  "points": [
    {
      "id": 1,
      "type": "feature",
      "shape": "circle",
      "name": "Grand Entrance Hall",
      "description": "Massive chamber with faded banners",
      "routes": [
        {"to": 2, "type": "open"},
        {"to": 3, "type": "closed", "obstacle": "Collapsed rubble"}
      ]
    },
    {
      "id": 2,
      "type": "danger", 
      "shape": "triangle",
      "name": "Spectral Guardroom",
      "description": "Ghostly sentries patrol this chamber",
      "threat": "Must navigate past hostile spirits",
      "routes": [
        {"to": 1, "type": "open"},
        {"to": 5, "type": "hidden", "discovery": "Secret passage behind tapestry"}
      ]
    },
    {
      "id": 6,
      "type": "treasure",
      "shape": "diamond", 
      "name": "Lord's Treasury",
      "description": "Hidden vault with ancient riches",
      "treasure": "Shadow relic and family heirlooms",
      "routes": [
        {"to": 5, "type": "closed", "obstacle": "Magical lock"}
      ]
    }
  ],
  "mapLayout": {
    "hexPoints": [
      {"point": 1, "position": "top"},
      {"point": 2, "position": "top-right"},
      {"point": 3, "position": "bottom-right"},
      {"point": 4, "position": "bottom"},
      {"point": 5, "position": "bottom-left"},
      {"point": 6, "position": "top-left"}
    ]
  }
}
```

## Integration with Realm Structure (Official System)

### Realm-Based Adventure Structure

**Mythic Bastionland uses Realms as the primary adventure structure**, not traditional D&D modules:

#### Official Realm Structure:
- **12x12 Hex Map**: Covering the loose rule of a Seat of Power
- **4 Holdings**: Castles, towns, fortresses, or towers (1 is Seat of Power)
- **6 Myths**: Placed in remote places, numbered 1-6
- **Landmarks**: 3-4 of each type (Dwellings, Sanctums, Monuments, Hazards, Curses, Ruins)
- **Wilderness**: Various terrain types in clusters of d12 hexes
- **Barriers**: 1/6 of total hexes have impassable edges
- **Water Features**: Navigable rivers and large lakes

#### Sites Within the Realm:
- **Sites zoom in on single Hexes** that need detailed exploration
- **Not separate areas**, but detailed views of realm locations
- **Typically used for**: Holdings (castles), Myth locations, significant Landmarks

### Module Structure with Sites
```
modules/Keep_of_Doom/
├── areas/                    # Traditional D&D areas
│   ├── HH001_BU.json        # Harrow's Hollow (town)
│   ├── G001_BU.json         # Gloamwood (forest)
│   └── SK001_BU.json        # Keep Exterior
├── sites/                   # Detailed Sites using 7-point hex
│   ├── SITE001_keep_interior.json
│   └── SITE002_ancient_crypt.json
├── module_plot_BU.json      # Plot progression
└── Keep_of_Doom_module.json # Module metadata
```

## Implementation Strategy

### Phase 1: Update Sites Generator
1. Fix SiteGenerator to properly implement 7-point hex method
2. Ensure proper point types (3 circles, 2 triangles, 1 diamond)
3. Implement route system (3 open, 2 closed, 1 hidden)
4. Add entrance placement logic

### Phase 2: Module Integration
1. Identify which locations in existing modules warrant Sites
2. Create Sites for complex exploration areas
3. Link Sites to traditional areas in module progression
4. Update plot system to handle Site exploration

### Phase 3: AI Integration  
1. Create AI prompts for Site content generation
2. Implement Site-aware storytelling in DM system
3. Update navigation commands for Site exploration
4. Create Site discovery and progression mechanics

## Key Design Principles

### Sites Complement, Don't Replace
- Traditional areas for travel, towns, wilderness
- Sites for detailed exploration of significant locations
- Both systems work together in same module

### Focused Exploration
- Sites contain 6 meaningful points of interest
- Each point serves specific narrative purpose
- Routes create navigation challenges and discoveries

### Player Agency
- Multiple paths between points
- Hidden routes reward exploration
- Closed routes require creative solutions

### Narrative Integration
- Sites advance module plot
- Points contain key story elements
- Discoveries unlock progression

## Conversion Guidelines

### When to Create a Site
- Location has 5+ interconnected rooms/areas
- Multiple navigation challenges exist
- Hidden areas and secret passages present
- Significant treasures or plot elements contained
- Complex tactical or exploration decisions required

### When to Keep Traditional Areas
- Simple travel locations
- Single-purpose areas (shops, inns)
- Random encounter areas
- Linear progression paths

This corrected design maintains the strengths of both systems while properly implementing Mythic Bastionland's intended Sites mechanics.