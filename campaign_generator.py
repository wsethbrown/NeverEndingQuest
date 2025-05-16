#!/usr/bin/env python3
"""
Campaign Generator Script
Creates campaign JSON files with detailed content based on schema requirements.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from openai import OpenAI
from config import OPENAI_API_KEY, DM_MAIN_MODEL
import jsonschema

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

@dataclass
class CampaignPromptGuide:
    """Detailed prompts and examples for each campaign field"""
    
    campaignName: str = """
    Campaign name should be evocative and memorable.
    Examples:
    - "Echoes of the Elemental Forge"
    - "Shadows Over Thorndale"
    - "The Last Light of Aethermoor"
    
    Format: Title case, 3-6 words typically
    Style: Fantasy-themed, hints at main conflict or theme
    """
    
    campaignDescription: str = """
    Campaign description should be a 1-2 sentence elevator pitch that:
    - Introduces the main conflict
    - Hints at the stakes
    - Sets the tone
    
    Example: "A group of adventurers must uncover the secrets of an ancient dwarven 
    artifact to prevent catastrophic elemental chaos."
    
    Length: 15-30 words
    Style: Active voice, present tense
    """
    
    worldName: str = """
    World name should be:
    - Unique and pronounceable
    - Fitting for a fantasy setting
    - Single word or compound word
    
    Examples: "Teloria", "Gravenmark", "Aethermoor"
    Style: Fantasy naming conventions
    """
    
    era: str = """
    Era name should reflect the current age of the world.
    Examples:
    - "Age of Resurgence" (post-catastrophe rebuilding)
    - "The Third Empire" (political reference)
    - "Dawn of Magic" (magical awakening)
    
    Format: "Age of..." or "The ... Era" or similar
    Style: Evocative, hints at world state
    """
    
    cosmology: str = """
    Cosmology type (must be one of these):
    - "Great Wheel": Standard D&D planar system
    - "World Tree": Norse-inspired connected realms
    - "World Axis": 4e-style points of light
    - "Custom": Unique planar arrangement
    
    Choose based on campaign needs for planar travel/influence
    """
    
    planarConnections: str = """
    List of planes that directly influence or connect to the material plane.
    For elemental campaigns, include relevant elemental planes.
    For demon/devil plots, include Abyss/Nine Hells.
    
    Examples: ["Elemental Plane of Fire", "Shadowfell", "Feywild"]
    Limit: 2-5 planes most relevant to the campaign
    """
    
    majorDeities: str = """
    Include 2-6 deities most relevant to the campaign.
    Each deity needs:
    - Name: Use standard D&D deities or create fitting names
    - Domain: Primary portfolio (War, Nature, Death, etc.)
    - Alignment: Standard 9-point alignment system
    
    Example:
    {
        "name": "Moradin",
        "domain": "Forge",
        "alignment": "lawful good"
    }
    
    Consider: Which deities would characters/villains worship?
    """
    
    majorPowers: str = """
    Political/military powers in the region (2-4 typical).
    Each needs:
    - Name: The faction/nation name
    - Type: "kingdom", "empire", "city-state", "alliance", "other"
    - Influence: "local", "regional", "continental", "global"
    
    Example:
    {
        "name": "Kingdom of Ironhold",
        "type": "kingdom",
        "influence": "regional"
    }
    
    Include both allied and antagonistic powers
    """
    
    predominantRaces: str = """
    3-6 races that are most common in the campaign area.
    Standard options: Human, Elf, Dwarf, Halfling, Gnome, Half-Elf, Half-Orc, 
    Dragonborn, Tiefling
    
    Consider:
    - Which races fit the campaign theme?
    - Are there any race-specific plot points?
    - What would be good PC options?
    
    Example: ["Human", "Dwarf", "Elf", "Halfling"]
    """
    
    magicPrevalence: str = """
    How common is magic in the world?
    Must be one of:
    - "rare": Magic users are exceptional, items are legendary
    - "uncommon": Magic exists but isn't everyday
    - "common": Magic shops exist, many know cantrips
    - "abundant": Magic is part of daily life
    
    Consider: How does this affect the campaign's tone?
    """
    
    currentConflicts: str = """
    2-4 ongoing tensions or conflicts in the world.
    These should:
    - Relate to the main plot
    - Provide adventure hooks
    - Create moral dilemmas
    
    Examples:
    - "Tension between surface dwellers and dwarven clans"
    - "Rising cult activity in rural areas"
    - "Trade war between merchant guilds"
    
    Length: One sentence each
    Style: Present tense, active voice
    """
    
    mainObjective: str = """
    The ultimate goal of the campaign in one sentence.
    Should be:
    - Clear and specific
    - Achievable but challenging
    - Stakes should be evident
    
    Example: "Prevent the Ember Enclave from misusing the Elemental Forge"
    Format: Verb + specific goal
    """
    
    antagonist: str = """
    The main villain or opposing force.
    Format: Name + title/organization
    
    Examples:
    - "Rurik Emberstone, leader of the Ember Enclave"
    - "The Whispering Shadow, an ancient lich"
    - "The Crimson Hand cult"
    
    Should tie directly to the main objective
    """
    
    plotStages: str = """
    3-7 major campaign stages/acts.
    Each needs:
    - stageName: Clear identifier ("Act 1: The Awakening")
    - stageDescription: 2-3 sentences of what happens
    - requiredLevel: Appropriate character level (1-20)
    - keyNPCs: 2-4 important NPCs for this stage
    - majorEvents: 2-3 critical events/revelations
    
    Example:
    {
        "stageName": "Investigating Ember Hollow",
        "stageDescription": "Players arrive in Ember Hollow and learn about 
        the recent disturbances. They discover evidence of dark forces 
        manipulating elemental energies.",
        "requiredLevel": 1,
        "keyNPCs": ["Maera Thistledown", "Garrick Ironbelly"],
        "majorEvents": ["Meeting with village elder", "First elemental manifestation"]
    }
    
    Stages should:
    - Build in complexity
    - Have clear transitions
    - Escalate stakes
    """
    
    factions: str = """
    2-5 organizations players will interact with.
    Each needs:
    - factionName: Clear, memorable name
    - factionDescription: 2-3 sentences about goals/methods
    - alignment: Standard 9-point alignment
    - goals: 2-3 specific objectives (list)
    - keyMembers: 2-4 named NPCs (list)
    
    Include:
    - At least one potential ally
    - At least one opponent
    - Neutral parties for complexity
    
    Example:
    {
        "factionName": "Order of the Silver Flame",
        "factionDescription": "A paladin order dedicated to destroying evil. They seek to purge corruption wherever it takes root.",
        "alignment": "lawful good",
        "goals": ["Purge undead", "Protect the innocent", "Maintain order"],
        "keyMembers": ["Sir Aldric", "Lady Serana", "Brother Marcus"]
    }
    """
    
    worldMap: str = """
    Define 2-5 major regions/areas for the campaign.
    Each needs:
    - regionName: Evocative name
    - regionDescription: 2-3 sentences about the area
    - mapId: Unique identifier based on region initials (e.g., "BH001" for Blackwood Hollow)
    - dangerLevel: "low", "medium", "high", "extreme"
    - recommendedLevel: Character level range (e.g., 1-3)
    - levels: Sub-areas within the region
    
    Sub-area format:
    {
        "name": "Old Mine Entrance",
        "id": "BH001-A",
        "description": "The abandoned entrance to the mines."
    }
    
    Start with starter area (low danger) and progress to endgame
    IMPORTANT: Generate mapId from region name initials, not hardcoded examples
    """
    
    timelineEvents: str = """
    3-6 events that will occur as the campaign progresses.
    Each needs:
    - eventName: Clear identifier
    - eventDescription: What happens (2-3 sentences)
    - triggerCondition: What causes this event
    - impact: How it affects the world
    
    Example:
    {
        "eventName": "The Elemental Surge",
        "eventDescription": "Elemental energies across the region spike dramatically. Spontaneous manifestations begin appearing.",
        "triggerCondition": "Players complete the second plot stage",
        "impact": "Random elemental manifestations become common"
    }
    
    These create a living world that responds to player actions
    """

class CampaignGenerator:
    def __init__(self):
        self.prompt_guide = CampaignPromptGuide()
        self.schema = self.load_schema()
    
    def load_schema(self) -> Dict[str, Any]:
        """Load the campaign schema for validation"""
        with open("campaign_schema.json", "r") as f:
            return json.load(f)
    
    def generate_field(self, field_path: str, schema_info: Dict[str, Any], 
                      context: Dict[str, Any]) -> Any:
        """Generate content for a specific field"""
        field_name = field_path.split(".")[-1]
        guide_attr = field_name
        
        # Handle nested fields
        if "." in field_path:
            parent = field_path.split(".")[0]
            guide_attr = f"{parent}_{field_name}"
        
        guide_text = getattr(self.prompt_guide, guide_attr, "")
        
        prompt = f"""Generate content for the '{field_path}' field of a D&D 5e campaign.

Field Schema:
{json.dumps(schema_info, indent=2)}

Detailed Guidelines:
{guide_text}

Context from already generated fields:
{json.dumps(context, indent=2)}

Return ONLY the value for this field in the correct format (not wrapped in a JSON object).
If the field expects a string, return just the string.
If the field expects an array, return just the array.
If the field expects an object, return just the object.
"""
        
        response = client.chat.completions.create(
            model=DM_MAIN_MODEL,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are an expert D&D 5e campaign designer. Return only the requested data in the exact format needed."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON if it looks like JSON
        if content.startswith(('[', '{')):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
        
        return content
    
    def generate_campaign(self, initial_concept: str, custom_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a complete campaign from an initial concept"""
        campaign_data = custom_values or {}
        
        # Generate fields in order of dependencies
        field_order = [
            "campaignName",
            "campaignDescription",
            "worldSettings.worldName",
            "worldSettings.era",
            "worldSettings.cosmology",
            "worldSettings.planarConnections",
            "worldSettings.majorDeities",
            "worldSettings.majorPowers",
            "worldSettings.predominantRaces",
            "worldSettings.magicPrevalence",
            "worldSettings.currentConflicts",
            "mainPlot.mainObjective",
            "mainPlot.antagonist",
            "mainPlot.plotStages",
            "factions",
            "worldMap",
            "timelineEvents"
        ]
        
        # Build context with initial concept
        context = {"initialConcept": initial_concept}
        
        for field_path in field_order:
            # Skip if already provided in custom_values
            if self.get_nested_value(campaign_data, field_path) is not None:
                continue
            
            # Get schema info for this field
            schema_info = self.get_field_schema(field_path)
            
            # Generate the field
            value = self.generate_field(field_path, schema_info, context)
            
            # Set the value in campaign_data
            self.set_nested_value(campaign_data, field_path, value)
            
            # Update context with the new field
            self.set_nested_value(context, field_path, value)
            
            print(f"Generated: {field_path}")
        
        return campaign_data
    
    def get_field_schema(self, field_path: str) -> Dict[str, Any]:
        """Get schema information for a specific field"""
        parts = field_path.split(".")
        current = self.schema["properties"]
        
        for part in parts:
            if part in current:
                current = current[part]
                if "properties" in current:
                    current = current["properties"]
            else:
                # Handle array items
                parent = ".".join(parts[:parts.index(part)])
                parent_schema = self.get_field_schema(parent)
                if "items" in parent_schema:
                    return parent_schema["items"]
        
        return current
    
    def get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get a value from nested dictionary using dot notation"""
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set a value in nested dictionary using dot notation"""
        parts = path.split(".")
        current = data
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def validate_campaign(self, campaign_data: Dict[str, Any]) -> List[str]:
        """Validate campaign data against schema"""
        errors = []
        
        try:
            jsonschema.validate(campaign_data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        
        return errors
    
    def save_campaign(self, campaign_data: Dict[str, Any], filename: str = None):
        """Save campaign data to file"""
        if filename is None:
            filename = f"{campaign_data['campaignName'].replace(' ', '_')}_campaign.json"
        
        with open(filename, "w") as f:
            json.dump(campaign_data, f, indent=2)
        
        print(f"Campaign saved to {filename}")

def main():
    generator = CampaignGenerator()
    
    # Example usage
    print("Campaign Generator")
    print("-" * 50)
    
    # Get initial concept
    concept = input("Enter your campaign concept (or press Enter for example): ").strip()
    if not concept:
        concept = "A haunted coastal town where ancient sea gods are awakening"
    
    print(f"\nGenerating campaign based on: {concept}")
    print("-" * 50)
    
    # Optional: provide custom values for specific fields
    custom_values = {}
    
    # Generate campaign
    campaign = generator.generate_campaign(concept, custom_values)
    
    # Validate
    errors = generator.validate_campaign(campaign)
    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nValidation successful!")
        
        # Save
        generator.save_campaign(campaign)
        
        # Display summary
        print("\nCampaign Summary:")
        print(f"Name: {campaign['campaignName']}")
        print(f"Description: {campaign['campaignDescription']}")
        print(f"World: {campaign['worldSettings']['worldName']}")
        print(f"Main Villain: {campaign['mainPlot']['antagonist']}")

if __name__ == "__main__":
    main()