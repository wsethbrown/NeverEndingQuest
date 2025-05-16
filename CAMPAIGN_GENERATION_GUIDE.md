# Campaign Generation System Guide

This guide explains how to create campaign content that properly follows the schema requirements.

## Problem Statement

The schemas define structure but not content requirements. For example:
- "dmInstructions" is defined as a string, but what should it contain?
- "plotHooks" are strings in an array, but how detailed should they be?
- "dangerLevel" has enum values, but when should each be used?

## Solution: Detailed Content Prompts

The `campaign_generator.py` script solves this by combining:
1. **Schema validation** - Ensures correct structure
2. **Detailed prompts** - Provides content guidelines
3. **Context awareness** - Uses already-generated fields to maintain consistency

## How It Works

### 1. Field Order Matters
Fields are generated in dependency order:
```python
field_order = [
    "campaignName",           # Generated first
    "campaignDescription",    # Uses campaign name for context
    "worldSettings.worldName",# Uses both above
    # ... etc
]
```

### 2. Each Field Has Detailed Guidelines
```python
campaignName: str = """
Campaign name should be evocative and memorable.
Examples:
- "Echoes of the Elemental Forge"
- "Shadows Over Thorndale"
- "The Last Light of Aethermoor"

Format: Title case, 3-6 words typically
Style: Fantasy-themed, hints at main conflict or theme
"""
```

### 3. Context Accumulates
As fields are generated, they're added to the context for subsequent fields:
```python
context = {"initialConcept": initial_concept}
# After generating campaignName:
context["campaignName"] = "Echoes of the Elemental Forge"
# This context is used when generating campaignDescription
```

## Extending to Other File Types

To create generators for other file types (locations, NPCs, etc.), follow this pattern:

### 1. Create a Prompt Guide Class
```python
@dataclass
class LocationPromptGuide:
    name: str = """
    Location name should be memorable and descriptive.
    Examples:
    - "The Whispering Gallery"
    - "Ember Hollow Mine Entrance"
    - "Temple of Forgotten Names"
    
    Style: Evocative, hints at purpose or danger
    """
    
    description: str = """
    Location description should paint a vivid picture in 2-3 sentences.
    Include:
    - Primary visual elements
    - Atmospheric details (sounds, smells, temperature)
    - Hints at purpose or history
    
    Example: "The ancient mine entrance yawns before you, its wooden 
    supports groaning under centuries of neglect. A faint warmth emanates 
    from within, carrying the acrid scent of sulfur."
    """
    
    dmInstructions: str = """
    DM instructions should provide practical running advice:
    - Key roleplay notes
    - Important mechanics (skill checks, combat triggers)
    - Secrets not obvious to players
    - Pacing suggestions
    
    Example: "If players investigate the support beams, DC 12 
    Investigation reveals recent tool marks. The warmth intensifies 
    deeper in - Constitution saves (DC 10+depth/10ft) or gain 
    exhaustion. The left passage leads to the underground river."
    
    Length: 2-4 sentences
    Style: Direct, mechanical language
    """
```

### 2. Create the Generator Class
```python
class LocationGenerator:
    def __init__(self):
        self.prompt_guide = LocationPromptGuide()
        self.schema = self.load_schema("loca_schema.json")
    
    def generate_location(self, 
                         area_context: Dict[str, Any], 
                         location_concept: str) -> Dict[str, Any]:
        # Similar pattern to campaign generator
        pass
```

### 3. Define Generation Dependencies
For locations, consider:
- Campaign context (theme, world, conflicts)
- Area context (danger level, purpose)
- Connected locations
- Plot requirements

### 4. Add Validation Rules
Beyond schema validation, add content validation:
```python
def validate_location_content(self, location: Dict[str, Any]) -> List[str]:
    errors = []
    
    # Check danger level matches monsters
    if location["dangerLevel"] == "low" and location["monsters"]:
        for monster in location["monsters"]:
            if "dragon" in monster["name"].lower():
                errors.append("Low danger location shouldn't have dragons")
    
    return errors
```

## Best Practices

1. **Use Real Examples**: Include actual examples from the game in prompts
2. **Be Specific**: "2-3 sentences" is better than "brief"
3. **Consider Context**: Use previously generated content to maintain consistency
4. **Validate Content**: Check that generated content makes sense together
5. **Iterative Generation**: Allow regeneration of specific fields if needed

## Next Steps

1. Create `plot_generator.py` for plot file generation
2. Create `location_generator.py` for area/location generation
3. Create `npc_generator.py` for NPC generation
4. Create a master `campaign_builder.py` that orchestrates all generators

Each generator should follow the same pattern:
- Detailed prompt guides
- Context-aware generation
- Schema validation
- Content validation

This approach ensures that generated content is both structurally correct and appropriately detailed for gameplay.