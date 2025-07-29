# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
NeverEndingQuest Core Engine - Module Generator
Copyright (c) 2024 MoonlightByte
Licensed under Fair Source License 1.0

This software is free for non-commercial and educational use.
Commercial competing use is prohibited for 2 years from release.
See LICENSE file for full terms.
"""

#!/usr/bin/env python3
"""
Module Generator Script
Creates module JSON files with detailed content based on schema requirements.
"""

import json
# ============================================================================
# MODULE_GENERATOR.PY - CONTENT GENERATION LAYER - MODULES
# ============================================================================
# 
# ARCHITECTURE ROLE: Content Generation Layer - Complete Module Creation
# 
# This module implements large-scale content generation using our multi-model
# AI strategy to create complete 5th edition modules with full location hierarchies,
# character rosters, and narrative structures.
# 
# KEY RESPONSIBILITIES:
# - Generate complete module structures with multiple areas
# - Create interconnected location networks with proper connectivity
# - Generate module-appropriate NPCs, monsters, and encounters
# - Establish cohesive narrative and plot progression
# - Ensure all generated content follows schema compliance
# 
# GENERATION PIPELINE:
# Module Concept -> Area Generation -> Location Creation -> NPC/Monster
# Population -> Encounter Placement -> Plot Integration -> Validation
# 
# CONTENT COORDINATION:
# - Ensures thematic consistency across all generated content
# - Maintains proper challenge ratings and level progression
# - Creates meaningful connections between areas and characters
# - Generates appropriate treasure and item distributions
# 
# ARCHITECTURAL INTEGRATION:
# - Uses all builder modules (monster_builder, npc_builder, etc.)
# - Leverages ModulePathManager for file organization
# - Integrates with module schema validation
# - Demonstrates our "Schema-Driven Development" approach
# 
# AI STRATEGY:
# - Coordinated multi-model generation for different content types
# - Thematic consistency through shared context prompting
# - Iterative refinement with validation feedback loops
# - Modular generation allowing for partial module creation
# 
# DESIGN PATTERNS:
# - Builder Pattern: Step-by-step module construction
# - Factory Pattern: Creates appropriate content based on module theme
# - Composite Pattern: Assembles complex module hierarchies
# 
# This module showcases our approach to large-scale AI-powered content
# generation while maintaining consistency and quality standards.
# ============================================================================

import os
import re
import glob
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, DM_MAIN_MODEL
import jsonschema
from utils.module_path_manager import ModulePathManager
from utils.file_operations import safe_write_json as save_json_safely
from utils.enhanced_logger import debug, info, warning, error
from utils.sites_generator import SiteGenerator

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Location ID prefix mapping to ensure unique IDs across areas
LOCATION_PREFIX_MAP = {
    # This will be populated dynamically, but here are common patterns:
    # First area gets 'A', second gets 'B', etc.
    # Special areas can have specific prefixes
}

def get_location_prefix(area_index: int) -> str:
    """Get the appropriate prefix for location IDs based on area index"""
    # Use letters A-Z for first 26 areas, then AA-AZ, BA-BZ, etc.
    if area_index < 26:
        return chr(65 + area_index)  # A-Z
    else:
        first_letter = chr(65 + (area_index // 26) - 1)
        second_letter = chr(65 + (area_index % 26))
        return first_letter + second_letter

@dataclass
class ModulePromptGuide:
    """Detailed prompts and examples for each module field"""
    
    moduleName: str = """
    Module name should be evocative and memorable.
    Examples:
    - "Echoes of the Elemental Forge"
    - "Shadows Over Thorndale"
    - "The Last Light of Aethermoor"
    
    Format: Title case, 3-6 words typically
    Style: Fantasy-themed, hints at main conflict or theme
    """
    
    moduleDescription: str = """
    Module description should be a 1-2 sentence elevator pitch that:
    - Introduces the main conflict
    - Hints at the stakes
    - Sets the tone
    
    Example: "A group of adventurers must uncover the secrets of an ancient dwarven 
    artifact to prevent catastrophic elemental chaos."
    
    Length: 15-30 words
    Style: Active voice, present tense
    """
    
    
    moduleConflicts: str = """
    Generate 1-3 conflicts that directly affect this module's gameplay.
    Each conflict must be:
    - LOCAL or REGIONAL in scope (not world-spanning)
    - Relevant to the module's plot and NPCs
    - Something that creates gameplay opportunities
    
    Each conflict needs:
    - conflictName: Short, descriptive name
    - description: What the conflict is about
    - scope: "local" or "regional" 
    - impact: How this affects party gameplay
    
    Example:
    {
        "conflictName": "Merchant Guild Rivalry",
        "description": "Two merchant guilds compete for control of trade routes",
        "scope": "regional",
        "impact": "Creates opportunities for party to choose sides or mediate"
    }
    
    Focus on conflicts that enhance the module's themes and story.
    """
    
    
    mainObjective: str = """
    The ultimate goal of the module in one sentence.
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
    3-7 major module stages/acts.
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
    Define 2-5 major regions/areas for the module.
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
    3-6 events that will occur as the module progresses.
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

def validate_location_names(area_data):
    """Ensure map file and locations array use consistent names"""
    # Check map rooms vs locations
    for map_room in area_data.get("map", {}).get("rooms", []):
        room_id = map_room["id"]
        matching_location = next((loc for loc in area_data.get("locations", []) 
                                if loc["locationId"] == room_id), None)
        
        # If location exists but names differ, update map name to match location
        if matching_location and map_room["name"] != matching_location["name"]:
            map_room["name"] = matching_location["name"]
            print(f"DEBUG: [Module Generator] Updated map room {room_id} name to match location: {matching_location['name']}")

def standardize_location_ids(module_name):
    """Normalize location ID formats across all files"""
    # Mapping of old to new formats
    id_mappings = {}
    # path_manager = ModulePathManager(module_name)
    
    # Get all location IDs from area files
    for area_file in glob.glob(f"modules/{module_name}/*.json"):
        if not os.path.basename(area_file).startswith("map_") and not os.path.basename(area_file).startswith("plot_"):
            try:
                area_data = json.load(open(area_file, 'r'))
                if "locations" in area_data:
                    for location in area_data["locations"]:
                        old_id = location.get("locationId", "")
                        # Check if it's not using the R## format
                        if not re.match(r'^R\d{2}$', old_id):
                            # Create standardized ID (R01, R02, etc.)
                            new_id = f"R{len(id_mappings) + 1:02d}"
                            id_mappings[old_id] = new_id
            except json.JSONDecodeError:
                pass  # Skip invalid JSON files
    
    # If mappings found, update all references
    if id_mappings:
        for file_path in glob.glob(f"modules/{module_name}/**/*.json", recursive=True):
            update_location_references(file_path, id_mappings)

def update_location_references(file_path, id_mappings):
    """Update all location ID references in a file"""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Check if data is modified
        modified = False
        
        # Process different file types differently
        if "locations" in data:
            # This is an area file
            for location in data["locations"]:
                if location.get("locationId") in id_mappings:
                    location["locationId"] = id_mappings[location["locationId"]]
                    modified = True
            
            # Update map data if present
            if "map" in data and "rooms" in data["map"]:
                for room in data["map"]["rooms"]:
                    if room.get("id") in id_mappings:
                        room["id"] = id_mappings[room["id"]]
                        modified = True
        
        # Handle plot files
        if "plotPoints" in data:
            for plot_point in data["plotPoints"]:
                if plot_point.get("location") in id_mappings:
                    plot_point["location"] = id_mappings[plot_point["location"]]
                    modified = True
                    
                # Update side quests
                if "sideQuests" in plot_point:
                    for side_quest in plot_point["sideQuests"]:
                        if "involvedLocations" in side_quest:
                            for i, loc in enumerate(side_quest["involvedLocations"]):
                                if loc in id_mappings:
                                    side_quest["involvedLocations"][i] = id_mappings[loc]
                                    modified = True
        
        # Handle party tracker
        if "worldConditions" in data:
            if data["worldConditions"].get("currentLocationId") in id_mappings:
                data["worldConditions"]["currentLocationId"] = id_mappings[data["worldConditions"]["currentLocationId"]]
                modified = True
        
        # Save if modified
        if modified:
            save_json_safely(data, file_path)
            print(f"DEBUG: [Module Generator] Updated location references in {file_path}")
    
    except (json.JSONDecodeError, IOError):
        pass  # Skip invalid or inaccessible files

def ensure_module_path_manager_usage(module_name):
    """Validate and fix file paths to use ModulePathManager patterns"""
    path_manager = ModulePathManager(module_name)
    file_paths = {
        "area": lambda area_id: path_manager.get_area_path(area_id),
        "map": lambda area_id: path_manager.get_map_path(area_id),
        "plot": lambda area_id: path_manager.get_plot_path(area_id),
        "player": lambda player_name: path_manager.get_character_path(player_name),
        "npc": lambda npc_name: path_manager.get_character_path(npc_name)
    }
    
    modified_files = []
    
    # Process Python files to ensure they use ModulePathManager
    for py_file in glob.glob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check for direct file access patterns
            area_pattern = re.compile(r'(["\'])([A-Z]{2}\d{3})\.json(["\'])')
            map_pattern = re.compile(r'(["\'])map_([A-Z]{2}\d{3})\.json(["\'])')
            plot_pattern = re.compile(r'(["\'])plot_([A-Z]{2}\d{3})\.json(["\'])')
            
            # Skip files that already use ModulePathManager
            if "ModulePathManager" in content and "get_area_path" in content:
                continue
                
            # Look for direct file references without path manager
            if (area_pattern.search(content) or map_pattern.search(content) or 
                plot_pattern.search(content)):
                modified_files.append(py_file)
                print(f"DEBUG: [Module Generator] WARNING: {py_file} should use ModulePathManager for file paths.")
        except IOError:
            pass
    
    return modified_files

def validate_module_structure(module_name):
    """Validate the structure of a module and return any issues"""
    issues = []
    # Ensure module name uses underscores for directory path
    module_name_safe = module_name.replace(" ", "_")
    module_dir = f"modules/{module_name_safe}"
    
    # Check for required directories
    for required_dir in ["npcs", "monsters"]:
        if not os.path.exists(f"{module_dir}/{required_dir}"):
            issues.append(f"Missing required directory: {required_dir}")
    
    # Check area files
    area_files = []
    for file in os.listdir(module_dir):
        if file.endswith(".json") and not file.startswith("map_") and not file.startswith("plot_"):
            if file != f"{module_name.replace(' ', '_')}_module.json" and file != "party_tracker.json":
                area_files.append(file)
    
    if not area_files:
        issues.append("No area files found")
    
    # Check each area file
    for area_file in area_files:
        try:
            with open(f"{module_dir}/{area_file}", "r") as f:
                area_data = json.load(f)
                
            # Check required fields
            for required_field in ["areaId", "areaName", "locations"]:
                if required_field not in area_data:
                    issues.append(f"Area file {area_file} missing required field: {required_field}")
            
            # Check locations
            if "locations" in area_data and not area_data["locations"]:
                issues.append(f"Area file {area_file} has empty locations array")
            
            # Check for corresponding map file
            area_id = area_data.get("areaId", "")
            if area_id and not os.path.exists(f"{module_dir}/map_{area_id}.json"):
                issues.append(f"Missing map file for area: {area_id}")
            
            # Individual plot files no longer used - centralized module_plot.json handles all plots
            # Validation removed for individual plot files
                
        except json.JSONDecodeError:
            issues.append(f"Invalid JSON in area file: {area_file}")
        except FileNotFoundError:
            issues.append(f"Could not open area file: {area_file}")
    
    return issues

class ModuleGenerator:
    def __init__(self):
        self.prompt_guide = ModulePromptGuide()
        self.schema = self.load_schema()
    
    def load_schema(self) -> Dict[str, Any]:
        """Load the module schema for validation"""
        with open("schemas/module_schema.json", "r") as f:
            return json.load(f)
    
    def generate_file_references(self, module_name: str) -> Dict:
        """Generate proper file paths using ModulePathManager patterns"""
        path_manager = ModulePathManager(module_name)
        return {
            "area_pattern": lambda area_id: path_manager.get_area_path(area_id),
            "map_pattern": lambda area_id: path_manager.get_map_path(area_id),
            "plot_pattern": lambda area_id: path_manager.get_plot_path(area_id),
            "player_pattern": lambda player_name: path_manager.get_character_path(player_name),
            "npc_pattern": lambda npc_name: path_manager.get_character_path(npc_name)
        }
    
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
        
        prompt = f"""Generate content for the '{field_path}' field of a 5e module.

Field Schema:
{json.dumps(schema_info, indent=2)}

Detailed Guidelines:
{guide_text}

Context from already generated fields:
{json.dumps(context.to_dict() if hasattr(context, 'to_dict') else context, indent=2)}

Return ONLY the value for this field in the correct format (not wrapped in a JSON object).
If the field expects a string, return just the string.
If the field expects an array, return just the array.
If the field expects an object, return just the object.
"""
        
        response = client.chat.completions.create(
            model=DM_MAIN_MODEL,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are an expert 5e module designer. Return only the requested data in the exact format needed."},
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
    
    def generate_module(self, initial_concept: str, custom_values: Dict[str, Any] = None, context=None) -> Dict[str, Any]:
        """Generate a complete module from an initial concept"""
        module_data = custom_values or {}
        
        # Add context validation if provided
        if context:
            module_data["moduleName"] = context.module_name
        
        # Generate fields in order of dependencies
        field_order = [
            "moduleName",
            "moduleDescription", 
            "moduleMetadata",
            "moduleConflicts",
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
            if self.get_nested_value(module_data, field_path) is not None:
                continue
            
            # Get schema info for this field
            schema_info = self.get_field_schema(field_path)
            
            # Generate the field
            value = self.generate_field(field_path, schema_info, context)
            
            # Set the value in module_data
            self.set_nested_value(module_data, field_path, value)
            
            # Update context with the new field
            self.set_nested_value(context, field_path, value)
            
            print(f"DEBUG: [Module Generator] Generated: {field_path}")
        
        # Get module name for file operations
        module_name = module_data.get("moduleName", "")
        if module_name:
            # Post-generation cleanup and validation
            print("DEBUG: [Module Generator] Performing post-generation validation and cleanup...")
            # Standardize location IDs (DISABLED - using prefix system instead)
            # standardize_location_ids(module_name)
            
            # Validate module structure (skip for custom output directories)
            try:
                issues = validate_module_structure(module_name)
                if issues:
                    print("DEBUG: [Module Generator] Validation issues found:")
                    for issue in issues:
                        print(f"DEBUG: [Module Generator] - {issue}")
                    
                    # Create validation report
                    module_dir = f"modules/{module_name}"
                    save_json_safely({"issues": issues}, f"{module_dir}/validation_report.json")
                    print(f"DEBUG: [Module Generator] Validation report saved to {module_dir}/validation_report.json")
                else:
                    print("DEBUG: [Module Generator] Module validation passed!")
            except FileNotFoundError:
                print("DEBUG: [Module Generator] Skipping validation (custom output directory)")
            except Exception as e:
                print(f"DEBUG: [Module Generator] Validation skipped due to error: {e}")
            else:
                print("DEBUG: [Module Generator] No validation issues found.")
        
        return module_data
    
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
    
    def validate_module(self, module_data: Dict[str, Any]) -> List[str]:
        """Validate module data against schema"""
        errors = []
        
        try:
            jsonschema.validate(module_data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        
        return errors
    
    def generate_all_areas(self, module_data: Dict[str, Any], module_name: str) -> Dict[str, Any]:
        """Generate all area files from world_map data"""
        print("DEBUG: [Module Generator] Generating all module areas...")
        
        # Create module directory if it doesn't exist
        module_dir = f"modules/{module_name.replace(' ', '_')}"
        os.makedirs(module_dir, exist_ok=True)
        os.makedirs(f"{module_dir}/npcs", exist_ok=True)
        os.makedirs(f"{module_dir}/monsters", exist_ok=True)
        
        # Import area generator
        from core.generators.area_generator import AreaGenerator, AreaConfig
        from utils.module_context import ModuleContext
        
        # Initialize area generator and context
        area_gen = AreaGenerator()
        context = ModuleContext()
        context.module_name = module_name
        context.module_id = module_name.replace(' ', '_')
        
        # Create list to track generated areas
        generated_areas = []
        
        # Extract world map data
        world_map = module_data.get("worldMap", [])
        
        # Generate the main Realm (12x12 hex map)
        realm_name = module_name
        coastal_type = self._determine_coastal_type(module_data)
        
        info(f"Generating Realm: {realm_name} (coastal: {coastal_type})", category="module_generation")
        realm_data = realm_gen.generate_realm(realm_name, coastal_type)
        
        # Save the main realm data
        save_json_safely(realm_data, f"{module_dir}/realm_map.json")
        info(f"Generated Realm with {len(realm_data['holdings'])} Holdings and {len(realm_data['myths'])} Myths", category="module_generation")
        
        # Generate detailed Sites for significant locations
        generated_sites = self._generate_detailed_sites(realm_data, module_dir, context)
        
        # Generate Holdings data with potential for conflict
        generated_holdings = self._generate_holdings_data(realm_data, module_dir, context)
        
        # Generate Warfare scenarios for potential conflicts
        warfare_scenarios = self._generate_warfare_scenarios(realm_data, module_dir, context)
        
        # Generate Knights and creatures for the realm
        self._populate_realm_with_characters(realm_data, module_dir, context)
        
        # Legacy world_map processing (will be phased out)
        for index, region in enumerate(world_map):
            area_id = region.get("mapId")
            area_name = region.get("regionName")
            area_type = self._determine_area_type(region.get("regionDescription", ""))
            danger_level = region.get("dangerLevel", "medium")
            recommended_level = region.get("recommendedLevel", 1)
            
            # Get unique prefix for this area's locations
            location_prefix = get_location_prefix(index)
            
            # Add area to context
            context.add_area(area_id, area_name, area_type)
            
            # Create area configuration
            config = AreaConfig(
                area_type=area_type,
                size="medium",  # Default to medium size
                complexity="moderate",
                danger_level=danger_level,
                recommended_level=recommended_level,
                num_locations=random.randint(5, 7)  # Explicitly set to 5-7 locations
            )
            
            # Generate area data
            area_data = area_gen.generate_area(area_name, area_id, context.to_dict(), config)
            
            # Add locations to context
            for location in area_data.get("locations", []):
                loc_id = location.get("locationId")
                loc_name = location.get("name")
                context.add_location(loc_id, loc_name, area_id)
            
            # Save area files in module directory
            print(f"DEBUG: [Module Generator] About to save area {area_id} with locations: {[loc.get('locationId') for loc in area_data.get('locations', [])]}")
            area_gen.save_area(area_data, module_name=module_name)
            
            # DEBUG: Verify what was actually saved
            saved_file_path = f"{module_dir}/areas/{area_id}.json"
            try:
                with open(saved_file_path, 'r') as f:
                    saved_data = json.load(f)
                    saved_locs = [loc.get('locationId') for loc in saved_data.get('locations', [])]
                    print(f"DEBUG: [Module Generator] Verified saved file has locations: {saved_locs}")
            except Exception as e:
                print(f"DEBUG: [Module Generator] Could not verify saved file: {e}")
            generated_areas.append(area_id)
            
            print(f"DEBUG: [Module Generator] Generated area: {area_name} ({area_id}) with location prefix '{location_prefix}' and {len(area_data.get('locations', []))} locations")
        
        # Validate no duplicate location IDs across all areas
        all_location_ids = {}
        duplicate_ids = []
        
        for area_id in generated_areas:
            try:
                with open(f"{module_dir}/areas/{area_id}.json", 'r') as f:
                    area_data = json.load(f)
                    for location in area_data.get("locations", []):
                        loc_id = location.get("locationId")
                        if loc_id in all_location_ids:
                            duplicate_ids.append(f"{loc_id} (in {area_id} and {all_location_ids[loc_id]})")
                        else:
                            all_location_ids[loc_id] = area_id
            except Exception as e:
                print(f"DEBUG: [Module Generator] Warning: Could not validate area {area_id}: {e}")
        
        if duplicate_ids:
            print(f"DEBUG: [Module Generator] WARNING: Duplicate location IDs found across areas: {duplicate_ids}")
        else:
            print(f"DEBUG: [Module Generator] Validation passed: All {len(all_location_ids)} location IDs are unique across the module")
        
        # Save context file
        context.save(f"{module_dir}/module_context.json")
        
        # Create realm summary with all generated components
        realm_summary = {
            "realm_data": realm_data,
            "generated_sites": generated_sites,
            "holdings": generated_holdings,
            "warfare_scenarios": warfare_scenarios,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        save_json_safely(realm_summary, f"{module_dir}/realm_summary.json")
        info(f"Generated complete Mythic Bastionland Realm with {len(generated_sites)} detailed Sites", category="module_generation")
        
        # Return realm data and generated components
        return {
            "realm_data": realm_data,
            "sites": generated_sites,
            "holdings": generated_holdings,
            "warfare": warfare_scenarios
        }
    
    def _determine_coastal_type(self, module_data: Dict[str, Any]) -> Optional[bool]:
        """Determine if realm should be coastal, landlocked, or island based on module data"""
        description = module_data.get("moduleDescription", "").lower()
        
        if any(word in description for word in ["island", "archipelago", "atoll"]):
            return "island"
        elif any(word in description for word in ["coastal", "shore", "harbor", "port", "sea", "ocean"]):
            return True
        elif any(word in description for word in ["inland", "landlocked", "mountain", "desert", "forest"]):
            return False
        else:
            return None  # Random
    
    def _generate_detailed_sites(self, realm_data: Dict[str, Any], module_dir: str, context) -> List[Dict]:
        """Generate detailed Sites using the 7-point hex method for significant locations"""
        info("Generating detailed Sites for significant realm locations", category="module_generation")
        
        generated_sites = []
        site_gen = SiteGenerator()
        
        # Generate Sites for each Holding
        for holding in realm_data.get("holdings", []):
            holding_name = f"{holding['type'].replace('_', ' ').title()} at ({holding['x']}, {holding['y']})"
            site_theme = self._get_site_theme_for_holding(holding['type'])
            
            site_data = site_gen.generate_site(holding_name, site_theme)
            site_filename = f"site_{holding['x']}_{holding['y']}_{holding['type']}.json"
            
            save_json_safely(site_data, f"{module_dir}/sites/{site_filename}")
            generated_sites.append({
                "name": holding_name,
                "filename": site_filename,
                "hex_coords": (holding['x'], holding['y']),
                "type": "holding",
                "theme": site_theme
            })
            
            debug(f"Generated Site for {holding['type']}: {holding_name}", category="module_generation")
        
        # Generate Sites for some Myths (50% chance each)
        for myth_data in realm_data.get("myths", []):
            if random.random() < 0.5:  # 50% chance
                myth_name = myth_data['name']
                site_name = f"Site of {myth_name}"
                
                site_data = site_gen.generate_site(site_name, "generic")
                site_filename = f"myth_site_{myth_data['x']}_{myth_data['y']}.json"
                
                save_json_safely(site_data, f"{module_dir}/sites/{site_filename}")
                generated_sites.append({
                    "name": site_name,
                    "filename": site_filename,
                    "hex_coords": (myth_data['x'], myth_data['y']),
                    "type": "myth",
                    "myth": myth_name
                })
                
                debug(f"Generated Site for Myth: {myth_name}", category="module_generation")
        
        info(f"Generated {len(generated_sites)} detailed Sites", category="module_generation")
        return generated_sites
    
    def _get_site_theme_for_holding(self, holding_type: str) -> str:
        """Get appropriate site theme based on holding type"""
        theme_map = {
            "castle": "fortress",
            "fortress": "fortress", 
            "tower": "fortress",
            "seat_of_power": "fortress",
            "town": "generic"
        }
        return theme_map.get(holding_type, "generic")
    
    def _generate_holdings_data(self, realm_data: Dict[str, Any], module_dir: str, context) -> List[Dict]:
        """Generate detailed data for each Holding including potential conflicts"""
        info("Generating Holdings data with conflict potential", category="module_generation")
        
        generated_holdings = []
        
        for holding in realm_data.get("holdings", []):
            holding_data = {
                "name": f"{holding['type'].replace('_', ' ').title()}",
                "type": holding['type'],
                "hex_coords": (holding['x'], holding['y']),
                "population": self._get_holding_population(holding['type']),
                "governance": self._get_holding_governance(holding['type']),
                "notable_knights": self._generate_holding_knights(holding['type']),
                "trade_goods": self._generate_trade_goods(),
                "conflicts": self._generate_holding_conflicts(holding['type']),
                "defenses": self._generate_holding_defenses(holding['type'])
            }
            
            filename = f"holding_{holding['x']}_{holding['y']}.json"
            save_json_safely(holding_data, f"{module_dir}/holdings/{filename}")
            
            generated_holdings.append(holding_data)
            debug(f"Generated Holding data: {holding_data['name']}", category="module_generation")
        
        return generated_holdings
    
    def _generate_warfare_scenarios(self, realm_data: Dict[str, Any], module_dir: str, context) -> List[Dict]:
        """Generate potential Warfare scenarios for the realm"""
        info("Generating Warfare scenarios for realm conflicts", category="module_generation")
        
        scenarios = []
        
        # Generate a siege scenario for the Seat of Power
        seat_of_power = next((h for h in realm_data.get("holdings", []) if h['type'] == 'seat_of_power'), None)
        if seat_of_power:
            siege_scenario = create_siege_scenario("castle")
            siege_data = {
                "name": f"Siege of {seat_of_power['type'].replace('_', ' ').title()}",
                "type": "siege",
                "location": (seat_of_power['x'], seat_of_power['y']),
                "description": f"A major siege targeting the realm's Seat of Power",
                "warfare_data": siege_scenario.generate_battle_report(),
                "trigger_conditions": ["Realm under serious threat", "Major antagonist revealed"],
                "glory_reward": random.randint(3, 5)
            }
            
            save_json_safely(siege_data, f"{module_dir}/warfare/siege_scenario.json")
            scenarios.append(siege_data)
        
        # Generate field battle scenarios
        for i in range(random.randint(1, 3)):
            battle_scenario = WarfareManager()
            # Add some opposing forces
            battle_scenario.add_warband("knights", "Defender Knights", "defender")
            battle_scenario.add_warband("mercenaries", "Attacking Force", "attacker")
            
            battle_data = {
                "name": f"Battle of the Borderlands {i+1}",
                "type": "field_battle",
                "description": f"A field battle between opposing forces in the realm",
                "warfare_data": battle_scenario.generate_battle_report(),
                "trigger_conditions": ["Faction conflict escalates", "Territory dispute"],
                "glory_reward": random.randint(1, 3)
            }
            
            save_json_safely(battle_data, f"{module_dir}/warfare/battle_scenario_{i+1}.json")
            scenarios.append(battle_data)
        
        info(f"Generated {len(scenarios)} Warfare scenarios", category="module_generation")
        return scenarios
    
    def _populate_realm_with_characters(self, realm_data: Dict[str, Any], module_dir: str, context):
        """Generate Knights and creatures to populate the realm"""
        info("Populating realm with Knights and creatures", category="module_generation")
        
        # Generate Knights for Holdings
        for holding in realm_data.get("holdings", []):
            num_knights = self._get_knights_per_holding(holding['type'])
            
            for i in range(num_knights):
                knight_data = self._generate_random_knight()
                knight_data["location"] = f"Holding at ({holding['x']}, {holding['y']})"
                knight_data["holding_type"] = holding['type']
                
                filename = f"knight_{holding['x']}_{holding['y']}_{i+1}.json"
                save_json_safely(knight_data, f"{module_dir}/knights/{filename}")
        
        # Generate creatures for Myths
        for myth_data in realm_data.get("myths", []):
            creature_data = self._generate_mythic_creature(myth_data['name'])
            creature_data["myth"] = myth_data['name']
            creature_data["location"] = f"Myth site at ({myth_data['x']}, {myth_data['y']})"
            
            filename = f"creature_{myth_data['x']}_{myth_data['y']}.json"
            save_json_safely(creature_data, f"{module_dir}/creatures/{filename}")
        
        info("Completed realm character population", category="module_generation")
    
    def _get_holding_population(self, holding_type: str) -> str:
        """Get population description for holding type"""
        populations = {
            "castle": "50-200 residents including guards and servants",
            "town": "500-2000 inhabitants engaged in trade and crafts", 
            "fortress": "100-300 military personnel and support staff",
            "tower": "10-50 residents, mostly guards and a castellan",
            "seat_of_power": "200-500 nobles, guards, and court officials"
        }
        return populations.get(holding_type, "Unknown population")
    
    def _get_holding_governance(self, holding_type: str) -> Dict:
        """Get governance structure for holding type"""
        if holding_type == "seat_of_power":
            return {"ruler": "Lord/Lady of the Realm", "structure": "Feudal court with advisors"}
        elif holding_type == "town":
            return {"ruler": "Mayor or Guild Council", "structure": "Elected or merchant-led"}
        else:
            return {"ruler": "Local Knight or Castellan", "structure": "Military hierarchy"}
    
    def _generate_holding_knights(self, holding_type: str) -> List[str]:
        """Generate notable knights for a holding"""
        num_knights = self._get_knights_per_holding(holding_type)
        return [f"Knight {i+1}" for i in range(min(3, num_knights))]  # Just names for now
    
    def _get_knights_per_holding(self, holding_type: str) -> int:
        """Get number of knights per holding type"""
        knight_counts = {
            "seat_of_power": random.randint(5, 8),
            "castle": random.randint(3, 5),
            "fortress": random.randint(2, 4),
            "tower": random.randint(1, 2),
            "town": random.randint(1, 3)
        }
        return knight_counts.get(holding_type, 1)
    
    def _generate_trade_goods(self) -> List[str]:
        """Generate trade goods for barter system"""
        common_goods = ["grain", "wool", "iron tools", "pottery", "leather goods"]
        uncommon_goods = ["spices", "fine cloth", "worked metal", "preserved foods"]
        rare_goods = ["precious metals", "gemstones", "rare spices", "magical components"]
        
        goods = random.sample(common_goods, random.randint(2, 3))
        if random.random() < 0.7:
            goods.extend(random.sample(uncommon_goods, random.randint(1, 2)))
        if random.random() < 0.3:
            goods.extend(random.sample(rare_goods, 1))
        
        return goods
    
    def _generate_holding_conflicts(self, holding_type: str) -> List[str]:
        """Generate potential conflicts for a holding"""
        conflicts = [
            "Trade route disputes",
            "Succession questions", 
            "Resource scarcity",
            "Bandit problems",
            "Neighboring realm tensions"
        ]
        return random.sample(conflicts, random.randint(1, 3))
    
    def _generate_holding_defenses(self, holding_type: str) -> Dict:
        """Generate defensive capabilities for a holding"""
        if holding_type in ["castle", "fortress", "seat_of_power"]:
            return {
                "walls": "Stone fortifications",
                "garrison": f"{random.randint(20, 100)} professional soldiers",
                "siege_equipment": "Basic defensive engines"
            }
        elif holding_type == "tower":
            return {
                "walls": "Tower walls and palisade",
                "garrison": f"{random.randint(10, 30)} guards",
                "siege_equipment": "None"
            }
        else:
            return {
                "walls": "Wooden palisade or none",
                "garrison": f"{random.randint(5, 20)} militia",
                "siege_equipment": "None"
            }
    
    def _generate_random_knight(self) -> Dict:
        """Generate a random Knight using the mythic system"""
        try:
            # Use mythic_generators to get a random knight
            knight_types = list(mythic_generators.knights.keys())
            if knight_types:
                knight_type = random.choice(knight_types)
                knight_data = mythic_generators.knights[knight_type].copy()
                knight_data["generated_name"] = f"Sir/Dame {self._generate_knight_name()}"
                return knight_data
        except:
            pass
        
        # Fallback if mythic_generators not available
        return {
            "generated_name": f"Sir/Dame {self._generate_knight_name()}",
            "type": "Generic Knight",
            "vigour": random.randint(8, 15),
            "clarity": random.randint(8, 15), 
            "spirit": random.randint(8, 15),
            "guard": random.randint(2, 5),
            "glory": random.randint(0, 3)
        }
    
    def _generate_knight_name(self) -> str:
        """Generate a random knight name"""
        first_names = ["Aldric", "Brianna", "Cedric", "Diana", "Edmund", "Fiona", "Gareth", "Helena"]
        last_names = ["Ironhold", "Stormwind", "Goldleaf", "Shadowmere", "Brightblade", "Thornfield"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_mythic_creature(self, myth_name: str) -> Dict:
        """Generate a creature associated with a specific myth"""
        try:
            # Try to get cast members from the myth
            myth_data = mythic_generators.myths.get(myth_name, {})
            cast_members = myth_data.get("cast", [])
            if cast_members:
                return {
                    "name": random.choice(cast_members),
                    "type": "Mythic Entity",
                    "description": f"A being associated with the Myth of {myth_name}",
                    "threat_level": "Varies by omen progression"
                }
        except:
            pass
        
        # Fallback creature
        return {
            "name": f"Guardian of {myth_name}",
            "type": "Mythic Entity", 
            "description": f"A mysterious entity tied to {myth_name}",
            "threat_level": "Unknown"
        }
    
    def _determine_area_type(self, description: str) -> str:
        """Determine area type from description text (legacy method)"""
        description = description.lower()
        
        if any(word in description for word in ["dungeon", "cave", "crypt", "tomb", "underground"]):
            return "dungeon"
        elif any(word in description for word in ["forest", "mountain", "swamp", "wilderness", "natural"]):
            return "wilderness"
        elif any(word in description for word in ["town", "city", "village", "settlement", "urban"]):
            return "town"
        else:
            return "mixed"
    
    def update_area_with_prefix(self, area_data: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """Update all location IDs in area data to use the specified prefix"""
        # Update map room IDs
        if "map" in area_data and "rooms" in area_data["map"]:
            for room in area_data["map"]["rooms"]:
                if "id" in room and room["id"].startswith("R"):
                    # Extract the number part and add new prefix
                    num = room["id"][1:]
                    new_id = prefix + num
                    old_id = room["id"]
                    room["id"] = new_id
                    
                    # Update room name if it contains the ID
                    if "name" in room and old_id in room["name"]:
                        room["name"] = room["name"].replace(old_id, new_id)
                    
                    # Update connections
                    if "connections" in room:
                        room["connections"] = [
                            prefix + conn[1:] if conn.startswith("R") else conn
                            for conn in room["connections"]
                        ]
        
        # Update layout grid
        if "map" in area_data and "layout" in area_data["map"]:
            for i, row in enumerate(area_data["map"]["layout"]):
                for j, cell in enumerate(row):
                    if cell.startswith("R"):
                        area_data["map"]["layout"][i][j] = prefix + cell[1:]
        
        # Update location IDs
        if "locations" in area_data:
            for location in area_data["locations"]:
                if "locationId" in location and location["locationId"].startswith("R"):
                    num = location["locationId"][1:]
                    location["locationId"] = prefix + num
                
                # Update connectivity
                if "connectivity" in location:
                    location["connectivity"] = [
                        prefix + conn[1:] if conn.startswith("R") else conn
                        for conn in location["connectivity"]
                    ]
        
        return area_data
    
        

    def generate_unified_plot_file(self, module_data: Dict[str, Any], realm_components: Dict, module_name: str):
        """Generate unified module plot file"""
        print("DEBUG: [Module Generator] Generating unified module plot file...")
        
        module_dir = f"modules/{module_name.replace(' ', '_')}"
        
        # Get plot stages to determine progression
        plot_stages = module_data.get("mainPlot", {}).get("plotStages", [])
        if not plot_stages:
            print("DEBUG: [Module Generator] Warning: No plot stages found in module data")
            return
        
        # Get holdings and sites from realm data for plot progression
        realm_data = realm_components.get("realm_data", {})
        holdings = realm_data.get("holdings", [])
        sites = realm_components.get("sites", [])
        
        # Sort holdings by importance (Seat of Power first, then others)
        sorted_holdings = sorted(holdings, key=lambda h: 0 if h['type'] == 'seat_of_power' else 1)
        
        # Create location references combining holdings and sites
        plot_locations = []
        for holding in sorted_holdings:
            plot_locations.append({
                "id": f"holding_{holding['x']}_{holding['y']}",
                "name": f"{holding['type'].replace('_', ' ').title()}",
                "type": "holding",
                "coords": (holding['x'], holding['y'])
            })
        
        for site in sites:
            plot_locations.append({
                "id": f"site_{site['hex_coords'][0]}_{site['hex_coords'][1]}",
                "name": site['name'],
                "type": "site", 
                "coords": site['hex_coords']
            })
        
        # Create unified plot structure
        module_plot = {
            "plotTitle": module_data.get("moduleName", "Unknown Module"),
            "mainObjective": module_data.get("mainPlot", {}).get("mainObjective", ""),
            "plotPoints": []
        }
        
        # Generate plot points
        side_quest_counter = 1
        for i, stage in enumerate(plot_stages):
            # Assign to appropriate location based on progression
            target_location_index = min(i, len(plot_locations) - 1) if plot_locations else 0
            location = plot_locations[target_location_index] if plot_locations else {"id": "unknown", "name": "Unknown Location"}
            
            # Create plot point
            plot_point = {
                "id": f"PP{i+1:03d}",
                "title": stage.get("stageName", f"Plot Point {i+1}"),
                "description": stage.get("stageDescription", ""),
                "location": location["id"],
                "location_name": location["name"],
                "location_type": location.get("type", "unknown"),
                "hex_coords": location.get("coords", (0, 0)),
                "nextPoints": [f"PP{i+2:03d}"] if i < len(plot_stages) - 1 else [],
                "status": "not started",
                "plotImpact": "",
                "sideQuests": []
            }
            
            # Generate side quests based on key NPCs and events
            key_npcs = stage.get("keyNPCs", [])
            major_events = stage.get("majorEvents", [])
            
            # Create 1-2 side quests per plot point
            for j in range(min(2, max(1, len(key_npcs)))):
                side_quest = {
                    "id": f"SQ{side_quest_counter:03d}",
                    "title": f"Side Quest: {key_npcs[j] if j < len(key_npcs) else 'Local Concerns'}",
                    "description": f"A quest involving {key_npcs[j] if j < len(key_npcs) else 'local concerns'} that may provide useful information or resources.",
                    "involvedLocations": [location["id"]],
                    "status": "not started",
                    "plotImpact": "Completing this quest provides Glory and advantages in the main plot.",
                    "glory_reward": random.randint(1, 2)
                }
                plot_point["sideQuests"].append(side_quest)
                side_quest_counter += 1
            
            module_plot["plotPoints"].append(plot_point)
        
        # Save unified plot file
        save_json_safely(module_plot, f"{module_dir}/module_plot.json")
        print(f"DEBUG: [Module Generator] Generated unified module plot file with {len(module_plot['plotPoints'])} plot points")
    
    def save_module(self, module_data: Dict[str, Any], filename: str = None):
        """Save module data to file"""
        # Create module_name for directory creation
        module_name = module_data['moduleName']
        module_dir = f"modules/{module_name.replace(' ', '_')}"
        
        # Create module directory
        os.makedirs(module_dir, exist_ok=True)
        
        # Note: *_module.json files are not used in current architecture
        # Module data is now stored in individual component files and world registry
        
        # Generate Mythic Bastionland Realm
        realm_components = self.generate_mythic_realm(module_data, module_name)
        
        # Generate unified plot file based on realm structure
        self.generate_unified_plot_file(module_data, realm_components, module_name)
        
        # Create party tracker file
        # party_tracker = {
        #     "module": module_name,
        #     "partyMembers": [],
        #     "partyNPCs": [],
        #     "worldConditions": {
        #         "currentAreaId": areas[0] if areas else "",
        #         "currentLocationId": "R01",  # Default to first room
        #         "time": {
        #             "day": 1,
        #             "hour": 8,
        #             "minute": 0,
        #             "timeOfDay": "morning"
        #         },
        #         "weather": "clear",
        #         "events": []
        #     },
        #     "notes": ""
        # }
        # 
        # save_json_safely(party_tracker, f"{module_dir}/party_tracker.json")
        
        # Run module debugger for validation
        from module_debugger import ModuleDebugger
        print("DEBUG: [Module Generator] Validating complete module structure...")
        debugger = ModuleDebugger()
        debugger.module_path = module_dir
        debugger.load_schemas()
        debugger.load_module_files()
        debugger.validate_schema_compliance()
        debugger.validate_references()
        debugger.validate_party_tracker()
        debugger.check_structural_issues()
        debugger.simulate_script_loading()
        
        # Generate validation report
        report = debugger.generate_report()
        
        # Save validation report
        validation_data = {
            "timestamp": datetime.now().isoformat(),
            "errors": debugger.errors,
            "warnings": debugger.warnings
        }
        save_json_safely(validation_data, f"{module_dir}/validation_report.json")
        
        print(f"DEBUG: [Module Generator] Validation complete - {len(debugger.errors)} errors, {len(debugger.warnings)} warnings")
        print(f"DEBUG: [Module Generator] Validation report saved to {module_dir}/validation_report.json")

        # Create a module summary markdown file
        with open(f"{module_dir}/MODULE_SUMMARY.md", "w") as f:
            f.write(f"# {module_name}\n\n")
            f.write(f"{module_data.get('moduleDescription', '')}\n\n")
            
            # Realm information
            realm_data = realm_components.get("realm_data", {})
            f.write("## Realm Information\n\n")
            f.write(f"- **Size**: {realm_data.get('size', 12)}x{realm_data.get('size', 12)} hex map\n")
            f.write(f"- **Type**: {'Coastal' if realm_data.get('coastal') else 'Landlocked'}\n")
            f.write(f"- **Holdings**: {len(realm_data.get('holdings', []))}\n")
            f.write(f"- **Myths**: {len(realm_data.get('myths', []))}\n")
            f.write(f"- **Landmarks**: {len(realm_data.get('landmarks', []))}\n\n")
            
            # Holdings
            f.write("## Holdings\n\n")
            for holding in realm_data.get("holdings", []):
                f.write(f"- **{holding['type'].replace('_', ' ').title()}** at hex ({holding['x']}, {holding['y']})\n")
            
            # Sites
            f.write("\n## Detailed Sites\n\n")
            for site in realm_components.get("sites", []):
                f.write(f"- **{site['name']}** ({site['type']})\n")
            
            # Warfare scenarios
            f.write("\n## Warfare Scenarios\n\n")
            for scenario in realm_components.get("warfare", []):
                f.write(f"- **{scenario['name']}** ({scenario['type']})\n")
            
            f.write("\n## Main Objective\n\n")
            f.write(f"{module_data.get('mainPlot', {}).get('mainObjective', '')}\n\n")
            f.write("## Antagonist\n\n")
            f.write(f"{module_data.get('mainPlot', {}).get('antagonist', '')}\n\n")
        
        return realm_components

def main():
    generator = ModuleGenerator()
    
    # Example usage
    print("Module Generator")
    print("-" * 50)
    
    # Get initial concept
    concept = input("Enter your module concept (or press Enter for example): ").strip()
    if not concept:
        concept = "A haunted coastal town where ancient sea gods are awakening"
    
    print(f"\nGenerating module based on: {concept}")
    print("-" * 50)
    
    # Optional: provide custom values for specific fields
    custom_values = {}
    
    # Generate module
    module = generator.generate_module(concept, custom_values)
    
    # Validate
    errors = generator.validate_module(module)
    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nValidation successful!")
        
        # Save
        generator.save_module(module)
        
        # Display summary
        print("\nModule Summary:")
        print(f"Name: {module['moduleName']}")
        print(f"Description: {module['moduleDescription']}")
        print(f"Level Range: {module['moduleMetadata']['levelRange']['min']}-{module['moduleMetadata']['levelRange']['max']}")
        print(f"Main Villain: {module['mainPlot']['antagonist']}")

if __name__ == "__main__":
    main()