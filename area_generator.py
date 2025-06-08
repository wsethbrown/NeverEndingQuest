#!/usr/bin/env python3
"""
Area Generator Script
Creates area JSON files with map layouts based on campaign requirements.
"""

import json
import random
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class AreaConfig:
    """Configuration for area generation"""
    area_type: str = "dungeon"  # dungeon, wilderness, town, mixed
    size: str = "medium"  # small, medium, large
    complexity: str = "moderate"  # simple, moderate, complex
    danger_level: str = "medium"  # low, medium, high, extreme
    recommended_level: int = 1
    num_locations: int = None  # If specified, override size-based calculation

class MapLayoutGenerator:
    """Generates map layouts for areas"""
    
    def __init__(self):
        self.room_types = {
            "dungeon": ["entrance", "corridor", "chamber", "hall", "vault", "shrine", "prison", "laboratory", "throne room", "treasure room"],
            "wilderness": ["clearing", "grove", "cave", "ravine", "hilltop", "riverside", "ruins", "campsite", "crossroads", "landmark"],
            "town": ["square", "market", "tavern", "shop", "temple", "guild", "residence", "gate", "warehouse", "barracks"]
        }
    
    def generate_layout(self, num_locations: int, area_type: str = "dungeon") -> Dict[str, Any]:
        """Generate a map layout with connected rooms"""
        # Calculate grid size
        grid_size = max(5, int((num_locations * 1.5) ** 0.5))
        
        # Initialize empty grid
        grid = [["   " for _ in range(grid_size)] for _ in range(grid_size)]
        connections = {}
        room_positions = {}
        
        # Place rooms
        placed_rooms = 0
        attempts = 0
        
        # Start in center
        center = grid_size // 2
        current_pos = (center, center)
        
        while placed_rooms < num_locations and attempts < num_locations * 10:
            x, y = current_pos
            
            if 0 <= x < grid_size and 0 <= y < grid_size and grid[y][x] == "   ":
                room_id = f"R{placed_rooms + 1:02d}"
                grid[y][x] = room_id
                room_positions[room_id] = (x, y)
                connections[room_id] = []
                
                # Connect to adjacent rooms
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < grid_size and 0 <= ny < grid_size:
                        neighbor = grid[ny][nx]
                        if neighbor != "   ":
                            connections[room_id].append(neighbor)
                            connections[neighbor].append(room_id)
                
                placed_rooms += 1
            
            # Move to a new position
            if placed_rooms > 0:
                # Find an empty spot adjacent to existing rooms
                candidates = []
                for room_id, (rx, ry) in room_positions.items():
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = rx + dx, ry + dy
                        if (0 <= nx < grid_size and 0 <= ny < grid_size and 
                            grid[ny][nx] == "   "):
                            candidates.append((nx, ny))
                
                if candidates:
                    current_pos = random.choice(candidates)
                else:
                    # Random position if no adjacent spots
                    current_pos = (random.randint(0, grid_size-1), 
                                 random.randint(0, grid_size-1))
            
            attempts += 1
        
        # Clean up grid (remove empty rows/columns)
        cleaned_grid = self.clean_grid(grid)
        
        # Create room data
        rooms = []
        for room_id in sorted(room_positions.keys()):
            x, y = room_positions[room_id]
            room_type = random.choice(self.room_types.get(area_type, ["room"]))
            
            rooms.append({
                "id": room_id,
                "name": f"{room_type.title()} {room_id}",
                "type": room_type,
                "connections": sorted(list(set(connections[room_id]))),
                "coordinates": f"X{x}Y{y}"
            })
        
        return {
            "mapId": f"MAP_{placed_rooms}",
            "mapName": f"{area_type.title()} Map",
            "totalRooms": placed_rooms,
            "rooms": rooms,
            "layout": cleaned_grid
        }
    
    def clean_grid(self, grid: List[List[str]]) -> List[List[str]]:
        """Remove empty rows and columns from grid"""
        # Find bounds
        min_x, max_x = len(grid[0]), 0
        min_y, max_y = len(grid), 0
        
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] != "   ":
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        
        # Extract non-empty portion
        if min_x <= max_x and min_y <= max_y:
            cleaned = []
            for y in range(min_y, max_y + 1):
                row = []
                for x in range(min_x, max_x + 1):
                    row.append(grid[y][x])
                cleaned.append(row)
            return cleaned
        
        return [[]]

class AreaGenerator:
    """Generates complete area files"""
    
    def __init__(self):
        self.map_gen = MapLayoutGenerator()
    
    def generate_area(self, 
                     area_name: str,
                     area_id: str,
                     campaign_context: Dict[str, Any],
                     config: AreaConfig) -> Dict[str, Any]:
        """Generate a complete area file"""
        
        # Determine number of locations
        if config.num_locations is not None:
            num_locations = config.num_locations
        else:
            # Use size-based calculation if not specified
            location_counts = {
                "small": random.randint(8, 12),
                "medium": random.randint(15, 20),
                "large": random.randint(25, 35)
            }
            num_locations = location_counts.get(config.size, 15)
        
        # Generate map layout
        map_data = self.map_gen.generate_layout(num_locations, config.area_type)
        
        # Generate locations from map rooms
        locations = []
        for room in map_data.get("rooms", []):
            room_id = room.get("id")
            name = room.get("name")
            room_type = room.get("type", "room")
            
            # Generate location data matching Keep of Doom schema
            location = {
                "locationId": room_id,
                "name": name,
                "type": room_type,
                "description": f"A {room_type} in {area_name}.",
                "coordinates": room.get("coordinates", "X0Y0"),
                "connectivity": room.get("connections", []),
                "areaConnectivity": [],
                "areaConnectivityId": [],
                "npcs": [],
                "monsters": [],
                "lootTable": [],
                "plotHooks": [],
                "dmInstructions": f"This {room_type} is part of {area_name}. Adjust encounters based on party strength.",
                "doors": [],
                "traps": [],
                "dcChecks": [],
                "accessibility": "Normal access",
                "dangerLevel": config.danger_level.capitalize(),
                "features": self.generate_location_features(room_type),
                "encounters": [],
                "adventureSummary": ""
            }
            
            # Add some rare features like traps or hidden items
            if random.random() < 0.2:  # 20% chance
                if config.area_type == "dungeon":
                    location["traps"].append({
                        "name": "Simple Pressure Plate",
                        "description": "A hidden pressure plate that triggers when stepped on.",
                        "detectDC": 13,
                        "disableDC": 15,
                        "triggerDC": 12,
                        "damage": "1d6 piercing damage from hidden spikes"
                    })
            
            locations.append(location)
        
        # Create area structure
        area_data = {
            "areaId": area_id,
            "areaName": area_name,
            "areaType": config.area_type,
            "areaDescription": self.generate_area_description(area_name, config),
            "dangerLevel": config.danger_level,
            "recommendedLevel": config.recommended_level,
            "climate": self.determine_climate(config.area_type),
            "terrain": self.determine_terrain(config.area_type),
            "map": map_data,
            "locations": locations,
            "randomEncounters": self.generate_encounter_table(config),
            "areaFeatures": self.generate_area_features(config),
            "notes": self.generate_dm_notes(config)
        }
        
        return area_data
    
    def generate_area_description(self, area_name: str, config: AreaConfig) -> str:
        """Generate a thematic area description"""
        templates = {
            "dungeon": f"{area_name} is a {config.complexity} network of underground passages and chambers. The air is thick with age and mystery, and danger lurks in every shadow.",
            "wilderness": f"{area_name} spans a {config.size} region of untamed nature. Wildlife and natural hazards make travel treacherous for the unprepared.",
            "town": f"{area_name} is a {config.size} settlement where civilization meets the frontier. Politics and intrigue mix with everyday commerce.",
            "mixed": f"{area_name} combines both natural and constructed elements, creating a unique environment where wilderness and civilization intersect."
        }
        
        return templates.get(config.area_type, f"{area_name} is a mysterious location waiting to be explored.")
    
    def determine_climate(self, area_type: str) -> str:
        """Determine appropriate climate for area type"""
        climates = {
            "dungeon": "controlled - cool and damp",
            "wilderness": random.choice(["temperate", "tropical", "arctic", "desert"]),
            "town": "temperate",
            "mixed": "varied"
        }
        return climates.get(area_type, "temperate")
    
    def determine_terrain(self, area_type: str) -> str:
        """Determine appropriate terrain for area type"""
        terrains = {
            "dungeon": "stone corridors and chambers",
            "wilderness": random.choice(["forest", "mountains", "plains", "swamp", "coast"]),
            "town": "urban streets and buildings",
            "mixed": "varied terrain"
        }
        return terrains.get(area_type, "varied")
    
    
    def generate_encounter_table(self, config: AreaConfig) -> List[Dict[str, Any]]:
        """Generate a random encounter table for the area"""
        encounter_types = {
            "low": ["wandering animal", "lost traveler", "environmental hazard"],
            "medium": ["hostile creature", "bandit patrol", "territorial beast"],
            "high": ["monster pack", "enemy squad", "dangerous predator"],
            "extreme": ["boss monster", "elite enemies", "deadly trap"]
        }
        
        encounters = []
        num_encounters = random.randint(6, 10)
        
        for i in range(num_encounters):
            roll_range = f"{i*10 + 1}-{(i+1)*10}"
            encounter_type = random.choice(encounter_types.get(config.danger_level, ["creature"]))
            
            encounters.append({
                "roll": roll_range,
                "encounter": encounter_type,
                "description": f"A {encounter_type} appropriate for level {config.recommended_level} parties"
            })
        
        return encounters
    
    def generate_area_features(self, config: AreaConfig) -> List[str]:
        """Generate notable features for the area"""
        features = {
            "dungeon": ["ancient murals", "mysterious mechanisms", "forgotten shrines", "hidden passages"],
            "wilderness": ["ancient trees", "rock formations", "water sources", "animal dens"],
            "town": ["market square", "local tavern", "guard posts", "merchant quarter"],
            "mixed": ["ruins", "bridges", "crossroads", "landmarks"]
        }
        
        area_features = features.get(config.area_type, ["interesting locations"])
        return random.sample(area_features, min(3, len(area_features)))
    
    def generate_location_features(self, room_type: str) -> List[Dict[str, str]]:
        """Generate features for a specific location type"""
        feature_types = {
            "entrance": ["weathered door", "grand archway", "narrow passage", "hidden opening"],
            "corridor": ["sconces", "tapestries", "cracks in walls", "echoing sound"],
            "chamber": ["furniture", "fireplace", "wall decorations", "floor symbols"],
            "hall": ["high ceiling", "support columns", "chandeliers", "banners"],
            "vault": ["locked chests", "shelves", "strange containers", "preservation magic"],
            "shrine": ["altar", "religious symbols", "offering bowls", "prayer mats"],
            "prison": ["cell bars", "chains", "guard post", "scratches on walls"],
            "laboratory": ["workbenches", "alchemical equipment", "strange ingredients", "experiment notes"],
            "clearing": ["fallen logs", "stone circle", "wild flowers", "animal tracks"],
            "grove": ["ancient trees", "mushroom circles", "unusual plants", "birdsong"],
            "cave": ["stalactites", "rock formations", "underground pool", "glowing fungi"],
            "square": ["well", "notice board", "sitting area", "merchant stalls"],
            "market": ["vendor stalls", "crowd areas", "display tables", "haggling spots"],
            "tavern": ["bar counter", "tables and chairs", "hearth", "trophy display"],
            "shop": ["merchandise displays", "counter", "backroom storage", "specialty items"],
            "temple": ["worship area", "offering space", "religious symbols", "ritual items"]
        }
        
        # Default features if room type not recognized
        default_features = ["dust", "signs of age", "interesting architecture"]
        
        # Get features for this room type, or use defaults
        room_features = feature_types.get(room_type, default_features)
        
        # Return 1-3 random features as objects with name and description
        num_features = random.randint(1, min(3, len(room_features)))
        selected_features = random.sample(room_features, num_features)
        
        # Convert to proper format
        return [
            {
                "name": feature.title(),
                "description": f"A {feature} that adds character to this {room_type}."
            }
            for feature in selected_features
        ]
    
    def generate_dm_notes(self, config: AreaConfig) -> str:
        """Generate helpful DM notes for running the area"""
        notes = {
            "dungeon": "Consider lighting sources and trap placement. Underground areas may have limited resources.",
            "wilderness": "Weather and terrain should affect travel times. Random encounters keep exploration tense.",
            "town": "NPCs should have daily routines. Political factions create roleplay opportunities.",
            "mixed": "Balance combat, exploration, and social encounters. Transitions between areas should feel natural."
        }
        
        return notes.get(config.area_type, "Customize this area to fit your campaign's needs.")
    
    def save_area(self, area_data: Dict[str, Any], filename: str = None):
        """Save area data to file"""
        if filename is None:
            filename = f"{area_data['areaId']}.json"
        
        # Also save a separate map file
        map_data = area_data["map"]
        map_filename = f"map_{area_data['areaId']}.json"
        
        with open(filename, "w") as f:
            json.dump(area_data, f, indent=2)
        
        with open(map_filename, "w") as f:
            json.dump(map_data, f, indent=2)
        
        print(f"Area saved to {filename}")
        print(f"Map saved to {map_filename}")

def main():
    """Interactive area generator"""
    generator = AreaGenerator()
    
    print("Area Generator")
    print("-" * 50)
    
    # Get area configuration
    area_name = input("Area name: ").strip() or "Mysterious Dungeon"
    area_id = input("Area ID (e.g., DG001): ").strip() or "DG001"
    
    area_type = input("Area type (dungeon/wilderness/town/mixed): ").strip() or "dungeon"
    size = input("Size (small/medium/large): ").strip() or "medium"
    complexity = input("Complexity (simple/moderate/complex): ").strip() or "moderate"
    danger_level = input("Danger level (low/medium/high/extreme): ").strip() or "medium"
    recommended_level = int(input("Recommended character level (1-20): ").strip() or "1")
    
    config = AreaConfig(
        area_type=area_type,
        size=size,
        complexity=complexity,
        danger_level=danger_level,
        recommended_level=recommended_level
    )
    
    # Mock campaign context
    campaign_context = {
        "campaignName": "Test Campaign",
        "theme": "Classic fantasy adventure"
    }
    
    # Generate area
    area_data = generator.generate_area(area_name, area_id, campaign_context, config)
    
    # Save
    generator.save_area(area_data)
    
    print("\nArea generation complete!")
    print(f"Locations: {len(area_data.get('locations', []))}")
    print(f"Danger level: {area_data['dangerLevel']}")

if __name__ == "__main__":
    main()