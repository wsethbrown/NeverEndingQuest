#!/usr/bin/env python3
"""
Master Module Builder
Orchestrates the generation of a complete 5th edition module by calling generators in the proper sequence.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import all generators
from module_generator import ModuleGenerator
from plot_generator import PlotGenerator
from location_generator import LocationGenerator
from area_generator import AreaGenerator, AreaConfig
from module_context import ModuleContext

@dataclass
class BuilderConfig:
    """Configuration for the module building process"""
    module_name: str = ""
    num_areas: int = 3
    locations_per_area: int = 15
    output_directory: str = "./modules"
    verbose: bool = True

class ModuleBuilder:
    """Orchestrates the complete module generation process"""
    
    def __init__(self, config: BuilderConfig):
        self.config = config
        self.module_data = {}
        self.areas_data = {}
        self.locations_data = {}
        self.plots_data = {}
        self.context = ModuleContext()
        
        # Initialize generators
        self.module_gen = ModuleGenerator()
        self.plot_gen = PlotGenerator()
        self.location_gen = LocationGenerator()
        self.area_gen = AreaGenerator()
        
        # Create output directory
        os.makedirs(self.config.output_directory, exist_ok=True)
    
    def log(self, message: str):
        """Log messages if verbose mode is enabled"""
        if self.config.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def save_json(self, data: Dict[str, Any], filename: str):
        """Save JSON data to the output directory"""
        filepath = os.path.join(self.config.output_directory, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        self.log(f"Saved: {filename}")
    
    def create_context_header(self, party_members: List[str]) -> str:
        """Create a context header to prepend to all generator prompts"""
        header = """
CRITICAL CONTEXT INFORMATION:
===========================
"""
        if party_members:
            header += f"""PARTY MEMBERS (Heroes who will PLAY this adventure): {', '.join(party_members)}
- These are the PLAYER CHARACTERS, not NPCs
- Do NOT create NPCs with these names
- They are the protagonists traveling TO your locations

"""
        header += """LOCATION CONTEXT:
- The party is CURRENTLY elsewhere (not in your module)
- Create a NEW location they will TRAVEL TO
- This should be a completely different place from their current location
- Give it a unique name and identity

MODULE INDEPENDENCE RULES:
1. This module represents a NEW DESTINATION
2. Party members listed above are PLAYERS, not NPCs
3. Create all-new locations, not variations of existing ones
4. Never reuse character names from the party as NPCs
===========================

"""
        return header
    
    def build_module(self, initial_concept: str):
        """Build a complete module from an initial concept"""
        self.log("Starting module build process...")
        self.log(f"Initial concept: {initial_concept}")
        
        # Get existing characters for context
        existing_characters = self.get_party_members()
        self.context_header = self.create_context_header(existing_characters)
        
        # Create required directory structure first
        self.create_module_directories()
        
        # Initialize context
        self.context.module_name = self.config.module_name.replace("_", " ")
        self.context.module_id = self.config.module_name
        
        # Step 1: Generate module overview with context
        self.log("Step 1: Generating module overview...")
        contextualized_concept = self.context_header + initial_concept
        self.module_data = self.module_gen.generate_module(contextualized_concept, context=self.context)
        
        # Extract NPCs and factions from module data
        self._extract_module_entities()
        
        # Step 2: Generate areas from the world map
        self.log("Step 2: Generating areas...")
        self.generate_areas()
        
        # Step 3: Generate locations for each area
        self.log("Step 3: Generating locations for each area...")
        self.generate_locations()
        
        # Step 4: Generate plots for each area
        self.log("Step 4: Generating plots for each area...")
        self.generate_plots()
        
        # Step 5: Generate initial party tracker
        self.log("Step 5: Creating party tracker...")
        self.create_party_tracker()
        
        # Step 6: Create module summary
        self.log("Step 6: Creating module summary...")
        self.create_module_summary()
        
        # Step 7: Validate and save context
        self.log("Step 7: Validating module consistency...")
        self.validate_module()
        
        self.log("Module generation complete!")
        self.log(f"Output saved to: {self.config.output_directory}")
    
    def generate_areas(self):
        """Generate detailed area files from the module world map"""
        world_map = self.module_data.get("worldMap", [])
        
        for i, region in enumerate(world_map[:self.config.num_areas]):
            area_id = region["mapId"]
            
            # Determine area type based on region description
            area_type = self.determine_area_type(region)
            
            config = AreaConfig(
                area_type=area_type,
                size="medium" if i == 0 else ["small", "medium", "large"][i % 3],
                complexity="moderate",
                danger_level=region["dangerLevel"],
                recommended_level=region["recommendedLevel"],
                num_locations=self.config.locations_per_area
            )
            
            # Add area to context
            self.context.add_area(area_id, region["regionName"], area_type)
            
            # Generate area using AreaGenerator
            area_data = self.area_gen.generate_area(
                region["regionName"],
                area_id,
                self.module_data,
                config
            )
            
            # Validate area consistency after generation
            self.validate_area_consistency(area_data, self.module_data)
            
            self.areas_data[area_id] = area_data
            self.save_json(area_data, f"areas/{area_id}.json")
            
            # Save the map separately
            if "map" in area_data:
                self.save_json(area_data["map"], f"map_{area_id}.json")
            
            # Context will be updated when locations are generated
            self.context.add_area(area_id, region['regionName'], area_data["areaType"])
            
            self.log(f"Generated area: {region['regionName']} ({area_id})")
    
    def determine_area_type(self, region: Dict[str, Any]) -> str:
        """Determine area type based on region description with better pattern matching"""
        description = region.get("regionDescription", "").lower()
        name = region.get("regionName", "").lower()
        
        # Enhanced pattern matching
        if any(word in description + name for word in ["mine", "cave", "dungeon", "ruins", "tomb", "underground", "depths"]):
            return "dungeon"
        elif any(word in description + name for word in ["town", "city", "village", "settlement", "hollow", "borough"]):
            return "town"
        elif any(word in description + name for word in ["forest", "woods", "wilds", "grove", "emerald", "woodland"]):
            return "wilderness"
        elif any(word in description + name for word in ["mountain", "peaks", "marches", "highlands", "cliffs"]):
            return "wilderness" 
        elif any(word in description + name for word in ["swamp", "marsh", "bog", "mire"]):
            return "wilderness"
        else:
            return "mixed"
    
    def validate_area_consistency(self, area_data: Dict[str, Any], module_data: Dict[str, Any]):
        """Validate area descriptions match their names and themes"""
        area_name = area_data.get("areaName", "").lower()
        climate = area_data.get("climate", "")
        terrain = area_data.get("terrain", "")
        
        # Fix obvious mismatches
        if any(word in area_name for word in ["emerald", "wilds", "forest", "woods"]):
            if climate == "desert" or "desert" in terrain:
                self.log(f"WARNING: Fixed climate mismatch for {area_data['areaName']}")
                area_data["climate"] = "temperate"
                area_data["terrain"] = "dense forest with clearings and groves"
        
        if any(word in area_name for word in ["frostward", "marches", "winter", "ice"]):
            if climate == "temperate":
                self.log(f"WARNING: Fixed climate mismatch for {area_data['areaName']}")
                area_data["climate"] = "cold"
                area_data["terrain"] = "frozen tundra and icy peaks"
    
    def get_party_members(self):
        """Get list of existing character names to avoid conflicts"""
        character_names = []
        
        # Try to read from current module's character files first
        try:
            import glob
            # Check current module directory first
            current_module_chars = glob.glob(f"{self.config.output_directory}/characters/*.json")
            
            # If no characters in current module, check all modules
            if not current_module_chars:
                char_files = glob.glob("modules/*/characters/*.json")
            else:
                char_files = current_module_chars
                
            for char_file in char_files:
                try:
                    with open(char_file, 'r') as f:
                        char_data = json.load(f)
                        # Include both player characters and NPCs to avoid naming conflicts
                        char_role = char_data.get('character_role', '')
                        if char_role in ['player', 'npc']:
                            name = char_data.get('name', '').strip()
                            if name and name not in character_names:  # Avoid duplicates
                                character_names.append(name)
                except Exception:
                    continue
        except Exception:
            pass
        
        # No fallback - let each module work with actual characters or none
        if not character_names:
            character_names = []
            self.log("No existing characters detected - module will use generic references")
        
        return character_names
    
    def create_module_directories(self):
        """Create all required module directories"""
        required_dirs = ["characters", "monsters", "encounters", "areas"]
        
        for dir_name in required_dirs:
            dir_path = os.path.join(self.config.output_directory, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            self.log(f"Created directory: {dir_name}/")
        
        # Create empty .gitkeep files to preserve directory structure
        for dir_name in required_dirs:
            gitkeep_path = os.path.join(self.config.output_directory, dir_name, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write("# Keep this directory in git\n")
    
    def generate_area_map(self, area_id: str) -> Dict[str, Any]:
        """Generate a map layout for an area"""
        # For now, create a simple grid map
        # This would be enhanced with the actual map generator
        return {
            "mapId": area_id,
            "mapName": f"Map of {area_id}",
            "totalRooms": self.config.locations_per_area,
            "layout": self.create_simple_layout(self.config.locations_per_area)
        }
    
    def create_simple_layout(self, num_rooms: int) -> List[List[str]]:
        """Create a simple grid layout for demonstration"""
        # This is a placeholder - real implementation would create
        # a proper dungeon layout
        grid_size = int((num_rooms ** 0.5) + 1)
        layout = []
        room_count = 1
        
        for y in range(grid_size):
            row = []
            for x in range(grid_size):
                if room_count <= num_rooms and (x + y) % 2 == 0:
                    row.append(f"R{room_count:02d}")
                    room_count += 1
                else:
                    row.append("   ")
            layout.append(row)
        
        return layout
    
    def generate_locations(self):
        """Generate detailed locations for each area"""
        # Get existing character names to avoid conflicts
        existing_characters = self.get_party_members()
        self.log(f"Avoiding character name conflicts with: {', '.join(existing_characters)}")
        
        for area_id, area_data in self.areas_data.items():
            self.log(f"Generating locations for area {area_id}...")
            
            # Get the plot data for this area
            plot_data = self.plots_data.get(area_id, {})
            
            # Generate locations using the LocationGenerator with context
            location_data = self.location_gen.generate_locations(
                area_data,
                plot_data,
                self.module_data,
                context=self.context,
                excluded_names=existing_characters,
                context_header=self.context_header
            )
            
            # Store locations data
            self.locations_data[area_id] = location_data
            
            # Add locations to area data and save complete area file
            area_data["locations"] = location_data["locations"]
            self.save_json(area_data, f"areas/{area_id}.json")
            
            self.log(f"Generated {len(location_data['locations'])} locations for {area_id}")
    
    def generate_plots(self):
        """Generate plot files for each area"""
        for area_id in self.areas_data:
            self.log(f"Generating plot for area {area_id}...")
            
            area_data = self.areas_data[area_id]
            location_data = self.locations_data[area_id]
            
            # Create area-specific context for plot generation
            area_specific_context = f"""
PLOT GENERATION FOR SPECIFIC AREA:
===================================
AREA NAME: {area_data['areaName']}
AREA TYPE: {area_data.get('areaType', 'unknown')}
AREA DESCRIPTION: {area_data.get('areaDescription', '')}
TERRAIN: {area_data.get('terrain', 'unknown')}

IMPORTANT: This plot must be specific to the {area_data['areaName']} area.
The plot title should reference this specific area, not other locations.
===================================

{self.context_header}"""
            
            plot_data = self.plot_gen.generate_plot(
                self.module_data,
                area_data,
                location_data,
                f"Create a plot specifically for {area_data['areaName']}, a {area_data.get('areaType', 'region')} area",
                context=self.context,
                context_header=area_specific_context
            )
            
            self.plots_data[area_id] = plot_data
            # Individual plot files removed - using centralized module_plot.json instead
            
            # Update context with plot points
            for plot_point in plot_data.get("plotPoints", []):
                self.context.add_plot_point(
                    plot_point["id"],
                    area_id,
                    plot_point.get("location")
                )
            
            self.log(f"Generated plot for {area_id}")
    
    
    def create_party_tracker(self):
        """Create the initial party tracker file"""
        # Use the first area as the starting location
        first_area_id = list(self.areas_data.keys())[0]
        first_area = self.areas_data[first_area_id]
        
        # Get the first location from the locations data
        first_locations_data = self.locations_data.get(first_area_id, {})
        locations_list = first_locations_data.get("locations", [])
        
        if not locations_list:
            # Fallback to a default location
            first_location = {
                "name": "Starting Location",
                "locationId": "R01"
            }
        else:
            first_location = locations_list[0]
        
        party_tracker = {
            "module": self.config.module_name.replace("_", " "),
            "partyMembers": [],  # Will be populated when players join
            "partyNPCs": [],
            "worldConditions": {
                "year": 1492,  # Standard Forgotten Realms year
                "month": "Hammer",  # January equivalent
                "day": 1,
                "time": "08:00:00",
                "weather": "Clear",
                "season": "Winter",
                "dayNightCycle": "Day",
                "moonPhase": "New Moon",
                "currentLocation": first_location["name"],
                "currentLocationId": first_location["locationId"],
                "currentArea": first_area["areaName"],
                "currentAreaId": first_area["areaId"],
                "majorEventsUnderway": [],
                "politicalClimate": "",
                "activeEncounter": "",
                "activeCombatEncounter": "",
                "weatherConditions": "",
                "lastCompletedEncounter": ""
            },
            "activeQuests": []
        }
        
        self.save_json(party_tracker, "party_tracker.json")
        self.log("Created party tracker")
    
    def create_module_summary(self):
        """Create a human-readable module summary"""
        summary = f"""# {self.module_data['moduleName']} - Module Summary

## Overview
{self.module_data['moduleDescription']}

## Module Conflicts
"""
        # Add module conflicts if they exist
        if 'moduleConflicts' in self.module_data:
            for conflict in self.module_data['moduleConflicts']:
                summary += f"- **{conflict['conflictName']}** ({conflict['scope']}): {conflict['description']}\n"
        
        summary += """

## Main Plot
**Objective**: {self.module_data['mainPlot']['mainObjective']}
**Antagonist**: {self.module_data['mainPlot']['antagonist']}

## Areas
"""
        
        for area_id, area_data in self.areas_data.items():
            plot_data = self.plots_data.get(area_id, {})
            summary += f"""
### {area_data['areaName']} ({area_id})
- **Description**: {area_data['areaDescription']}
- **Danger Level**: {area_data['dangerLevel']}
- **Recommended Level**: {area_data['recommendedLevel']}
- **Locations**: {len(area_data['locations'])}
- **Plot**: {plot_data.get('plotTitle', 'TBD')}
- **Objective**: {plot_data.get('mainObjective', 'TBD')}
"""
        
        summary += f"""
## Module Structure
- **Total Areas**: {len(self.areas_data)}
- **Total Locations**: {sum(len(area['locations']) for area in self.areas_data.values())}

## Getting Started
1. Players start in {list(self.areas_data.values())[0]['areaName']}
2. Initial quest hook: {self.plots_data[list(self.areas_data.keys())[0]].get('plotPoints', [{}])[0].get('description', 'TBD')}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        summary_path = os.path.join(self.config.output_directory, "MODULE_SUMMARY.md")
        with open(summary_path, "w") as f:
            f.write(summary)
        
        self.log("Created module summary")
    
    def _extract_module_entities(self):
        """Extract NPCs and other entities from module data"""
        # Extract NPCs from plot stages
        for stage in self.module_data.get("mainPlot", {}).get("plotStages", []):
            for npc_name in stage.get("keyNPCs", []):
                self.context.add_npc(npc_name)
                self.context.add_reference("npc", npc_name, "module:plotStages")
        
        # Note: Faction NPCs removed - location-generated NPCs are sufficient
    
    def validate_module(self):
        """Validate module consistency and save results"""
        issues = self.context.validate_all()
        
        if issues:
            self.log(f"Found {len(issues)} validation issues:")
            for issue in issues:
                self.log(f"  - {issue}")
        else:
            self.log("All validation checks passed!")
        
        # Save context and validation report
        self.context.save(os.path.join(self.config.output_directory, "module_context.json"))
        
        # Create validation report
        report = {
            "validation_date": datetime.now().isoformat(),
            "issues": issues,
            "context_summary": {
                "areas": len(self.context.areas),
                "npcs": len(self.context.npcs),
                "locations": len(self.context.locations),
                "plot_points": len(self.context.plot_scopes)
            }
        }
        self.save_json(report, "validation_report.json")

def main():
    """Interactive module builder"""
    print("5th Edition Module Builder")
    print("=" * 50)
    
    # Get module configuration
    module_name = input("Module name: ").strip()
    if not module_name:
        module_name = "New_Module"
    
    module_name = module_name.replace(" ", "_")
    
    num_areas = input("Number of areas to generate (default 3): ").strip()
    num_areas = int(num_areas) if num_areas else 3
    
    locations_per_area = input("Locations per area (default 15): ").strip()
    locations_per_area = int(locations_per_area) if locations_per_area else 15
    
    # Get initial concept
    print("\nDescribe your module concept:")
    concept = input("> ").strip()
    if not concept:
        concept = "A classic fantasy adventure with dungeons, dragons, and ancient mysteries"
    
    # Configure builder
    config = BuilderConfig(
        module_name=module_name,
        num_areas=num_areas,
        locations_per_area=locations_per_area,
        output_directory=f"./modules/{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Build module
    builder = ModuleBuilder(config)
    builder.build_module(concept)
    
    print(f"\nModule '{module_name}' has been generated!")
    print(f"Output directory: {config.output_directory}")
    print("\nYou can now:")
    print("1. Review the MODULE_SUMMARY.md file")
    print("2. Edit any generated files as needed")
    print("3. Start your adventure with main.py")

def parse_narrative_to_module_params(narrative: str) -> Dict[str, Any]:
    """Use AI to parse a narrative description into module parameters
    
    Args:
        narrative: The rich narrative description of the new module
        
    Returns:
        Dict containing parsed module parameters
    """
    from openai import OpenAI
    import config
    
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    parsing_prompt = """You are a module configuration parser. Given a narrative description of a D&D adventure module, extract the key parameters needed for module generation.

The narrative may contain embedded parameters in this format:
- **Module Name**: _Name_With_Underscores_
- **Adventure Type**: Type description
- **Level Range**: X-Y
- **Number of Areas**: N
- **Locations per Area**: X-Y
- **Plot Themes**: Listed themes or goals

Extract these values and return a JSON object with these fields:
- module_name: The title with underscores (e.g., "Bell_of_the_Tidegrave")
- num_areas: Number of distinct areas (extract from "Number of Areas")
- locations_per_area: Average of the range given (e.g., "6-7" becomes 6 or 7)
- level_range: {"min": X, "max": Y} from the Level Range
- adventure_type: Extract type, lowercase ("dungeon", "wilderness", "urban", or "mixed")
- plot_themes: Extract the core themes or goals as comma-separated values

If values are ranges (like "6-7"), use the average or higher value.
For plot themes, extract the essential goals/themes, not the full descriptions.

Return ONLY the JSON object, no explanation."""
    
    try:
        response = client.chat.completions.create(
            model=config.DM_SUMMARIZATION_MODEL,
            temperature=0.3,
            messages=[
                {"role": "system", "content": parsing_prompt},
                {"role": "user", "content": f"Parse this module narrative:\n\n{narrative}"}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        # Clean up potential code blocks
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(result)
        print(f"DEBUG: AI parsed narrative into: {json.dumps(parsed, indent=2)}")
        return parsed
        
    except Exception as e:
        print(f"ERROR: Failed to parse narrative with AI: {e}")
        # Return sensible defaults
        return {
            "module_name": "New_Adventure",
            "num_areas": 2,
            "locations_per_area": 12,
            "level_range": {"min": 3, "max": 5},
            "adventure_type": "mixed",
            "plot_themes": "adventure,mystery"
        }

def ai_driven_module_creation(params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """AI-driven module creation that accepts a narrative and autonomously creates a module
    
    This function is fully agentic - it can work with just a narrative description
    or accept explicit parameters from the AI DM.
    
    Args:
        params: Dictionary that can contain either:
            - concept: Adventure narrative (required)
            - module_name: If provided, will override AI parsing
            - Other optional params that override AI parsing
            OR just:
            - narrative: Full narrative description (AI will parse all params)
    
    Returns:
        tuple[bool, Optional[str]]: (success_status, module_name)
            - success_status: True if module was created successfully, False otherwise
            - module_name: Name of the created module if successful, None if failed
    """
    try:
        # Check if we have a narrative to parse
        narrative = params.get("narrative") or params.get("concept")
        if not narrative:
            print(f"ERROR: No narrative or concept provided")
            return False, None
        
        # Parse narrative with AI to get module parameters
        parsed_params = parse_narrative_to_module_params(narrative)
        
        # Allow explicit parameters to override AI parsing
        module_name = params.get("module_name") or parsed_params.get("module_name")
        num_areas = params.get("num_areas") or parsed_params.get("num_areas", 2)
        locations_per_area = params.get("locations_per_area") or parsed_params.get("locations_per_area", 12)
        level_range = params.get("level_range") or parsed_params.get("level_range", {"min": 3, "max": 5})
        adventure_type = params.get("adventure_type") or parsed_params.get("adventure_type", "mixed")
        plot_themes = params.get("plot_themes") or parsed_params.get("plot_themes", "")
        
        # Clean module name (replace spaces with underscores)
        module_name = module_name.replace(" ", "_")
        
        # Enhance the concept with AI-provided context
        enhanced_concept = f"{narrative}"
        if adventure_type:
            enhanced_concept += f" This is primarily a {adventure_type} adventure."
        if level_range:
            enhanced_concept += f" Designed for characters level {level_range.get('min', 3)} to {level_range.get('max', 5)}."
        if plot_themes:
            enhanced_concept += f" Key themes include: {plot_themes}."
        
        print(f"DEBUG: AI-driven module creation starting for '{module_name}'")
        
        # Configure builder with AI parameters
        config = BuilderConfig(
            module_name=module_name,
            num_areas=int(num_areas),
            locations_per_area=int(locations_per_area),
            output_directory=f"./modules/{module_name}",
            verbose=True
        )
        
        # Create and run the builder
        builder = ModuleBuilder(config)
        
        # Store AI context for generators to use
        # The generators will pick up these values from the enhanced_concept text
        
        # Build the module
        builder.build_module(enhanced_concept)
        
        print(f"DEBUG: Module '{module_name}' created successfully at {config.output_directory}")
        
        # Create a module_plot.json file for the new module (required by the system)
        plot_file_path = os.path.join(config.output_directory, "module_plot.json")
        if not os.path.exists(plot_file_path):
            # Create a unified plot file from area plots
            unified_plot = {
                "plotTitle": builder.module_data.get("moduleName", module_name.replace("_", " ")),
                "mainObjective": builder.module_data.get("mainPlot", {}).get("mainObjective", "Complete the adventure"),
                "plotPoints": []
            }
            
            # Aggregate plot points from all areas
            plot_id_counter = 1
            for area_id, plot_data in builder.plots_data.items():
                for plot_point in plot_data.get("plotPoints", []):
                    # Renumber plot points for unified file
                    plot_point["id"] = f"PP{plot_id_counter:03d}"
                    plot_point["areaId"] = area_id
                    unified_plot["plotPoints"].append(plot_point)
                    plot_id_counter += 1
            
            with open(plot_file_path, "w") as f:
                json.dump(unified_plot, f, indent=2)
            print(f"DEBUG: Created unified module_plot.json with {len(unified_plot['plotPoints'])} plot points")
        
        return True, module_name
        
    except Exception as e:
        print(f"ERROR: AI-driven module creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    main()