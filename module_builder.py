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
    
    def build_module(self, initial_concept: str):
        """Build a complete module from an initial concept"""
        self.log("Starting module build process...")
        self.log(f"Initial concept: {initial_concept}")
        
        # Initialize context
        self.context.module_name = self.config.module_name.replace("_", " ")
        self.context.module_id = self.config.module_name
        
        # Step 1: Generate module overview
        self.log("Step 1: Generating module overview...")
        self.module_data = self.module_gen.generate_module(initial_concept, context=self.context)
        self.save_json(self.module_data, f"{self.config.module_name}_module.json")
        
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
            
            self.areas_data[area_id] = area_data
            self.save_json(area_data, f"{area_id}.json")
            
            # Save the map separately
            if "map" in area_data:
                self.save_json(area_data["map"], f"map_{area_id}.json")
            
            # Context will be updated when locations are generated
            self.context.add_area(area_id, region['regionName'], area_data["areaType"])
            
            self.log(f"Generated area: {region['regionName']} ({area_id})")
    
    def determine_area_type(self, region: Dict[str, Any]) -> str:
        """Determine area type based on region description"""
        description = region.get("regionDescription", "").lower()
        name = region.get("regionName", "").lower()
        
        if any(word in description + name for word in ["mine", "cave", "dungeon", "ruins", "tomb"]):
            return "dungeon"
        elif any(word in description + name for word in ["town", "city", "village", "settlement"]):
            return "town"
        elif any(word in description + name for word in ["forest", "mountain", "plains", "wilderness"]):
            return "wilderness"
        else:
            return "mixed"
    
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
        for area_id, area_data in self.areas_data.items():
            self.log(f"Generating locations for area {area_id}...")
            
            # Get the plot data for this area
            plot_data = self.plots_data.get(area_id, {})
            
            # Generate locations using the LocationGenerator with context
            location_data = self.location_gen.generate_locations(
                area_data,
                plot_data,
                self.module_data,
                context=self.context
            )
            
            # Store locations data
            self.locations_data[area_id] = location_data
            
            # Add locations to area data and save complete area file
            area_data["locations"] = location_data["locations"]
            self.save_json(area_data, f"{area_id}.json")
            
            self.log(f"Generated {len(location_data['locations'])} locations for {area_id}")
    
    def generate_plots(self):
        """Generate plot files for each area"""
        for area_id in self.areas_data:
            self.log(f"Generating plot for area {area_id}...")
            
            area_data = self.areas_data[area_id]
            location_data = self.locations_data[area_id]
            
            plot_data = self.plot_gen.generate_plot(
                self.module_data,
                area_data,
                location_data,
                f"Adventure in {area_data['areaName']}",
                context=self.context
            )
            
            self.plots_data[area_id] = plot_data
            self.save_json(plot_data, f"plot_{area_id}.json")
            
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
        
        # Extract NPCs from factions
        for faction in self.module_data.get("factions", []):
            for member_name in faction.get("keyMembers", []):
                faction_name = faction.get("factionName", "")
                self.context.add_npc(member_name, faction=faction_name)
                self.context.add_reference("npc", member_name, f"module:faction:{faction_name}")
    
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

if __name__ == "__main__":
    main()