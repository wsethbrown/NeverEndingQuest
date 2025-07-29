#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Realm Generator

Implements the official Realm creation system from Mythic Bastionland (p14).
Creates proper 12x12 hex map Realms with Holdings, Wilderness, Landmarks, and Myths.

A Realm represents the loose rule of a Seat of Power, containing:
- 4 Holdings (with 1 Seat of Power)
- 6 Myth Hexes in remote places
- 12-16 Landmarks (3-4 of each type)
- Wilderness hexes with terrain and barriers
- Navigable rivers and lakes
"""

import random
import json
import math
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from utils.enhanced_logger import debug, info, warning, error, set_script_name
from utils.mythic_generators import mythic_generators

# Set script name for logging
set_script_name("realm_generator")

class TerrainType(Enum):
    """Types of terrain for wilderness hexes"""
    FOREST = "forest"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    PLAINS = "plains"
    SWAMP = "swamp"
    DESERT = "desert"
    COAST = "coast"
    RIVER = "river"
    LAKE = "lake"

class LandmarkType(Enum):
    """Types of landmarks that can be discovered in wilderness"""
    DWELLING = "dwelling"      # Humble homes amid the wilds
    SANCTUM = "sanctum"        # Sacred home to a Seer
    MONUMENT = "monument"      # Sites of inspiration (restore SPI)
    HAZARD = "hazard"          # Nature fights every step
    CURSE = "curse"            # Blights that throw you off course
    RUIN = "ruin"              # Remnants that echo the future

class HoldingType(Enum):
    """Types of Holdings in the realm"""
    CASTLE = "castle"
    TOWN = "town"
    FORTRESS = "fortress"
    TOWER = "tower"
    SEAT_OF_POWER = "seat_of_power"

class RealmHex:
    """Represents a single hex in the realm"""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.terrain = TerrainType.PLAINS
        self.holding = None  # HoldingType if present
        self.landmark = None  # LandmarkType if present
        self.myth = None  # Myth name if present
        self.barriers = []  # List of edge directions with barriers
        self.description = ""
        self.is_wilderness = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "coordinates": {"x": self.x, "y": self.y},
            "terrain": self.terrain.value,
            "holding": self.holding.value if self.holding else None,
            "landmark": self.landmark.value if self.landmark else None,
            "myth": self.myth,
            "barriers": self.barriers,
            "description": self.description,
            "is_wilderness": self.is_wilderness
        }

class RealmGenerator:
    """Generates complete Mythic Bastionland Realms using the official system"""
    
    def __init__(self, size: int = 12):
        self.size = size  # 12x12 is typical
        self.hexes = {}  # Dict of (x,y) -> RealmHex
        self.holdings = []  # List of holding positions
        self.seat_of_power = None  # Coordinates of the seat of power
        self.myths = []  # List of myth positions and names
        self.landmarks = []  # List of landmark positions
        
        # Initialize the hex grid
        for x in range(size):
            for y in range(size):
                self.hexes[(x, y)] = RealmHex(x, y)
    
    def generate_realm(self, realm_name: str, coastal: bool = None) -> Dict:
        """
        Generate a complete realm using the Mythic Bastionland system
        
        Args:
            realm_name: Name of the realm
            coastal: True for coastal, False for landlocked, None for random
            
        Returns:
            Dictionary containing complete realm data
        """
        info(f"Generating realm: {realm_name}", category="realm_generation")
        
        # Determine realm type
        if coastal is None:
            coastal = random.choice([True, False, "island"])
        
        # Step 1: Create terrain base
        self._generate_terrain(coastal)
        
        # Step 2: Place Holdings (4 total, 1 is Seat of Power)
        self._place_holdings()
        
        # Step 3: Place Myths (6 in remote places)
        self._place_myths()
        
        # Step 4: Place Landmarks (3-4 of each type)
        self._place_landmarks()
        
        # Step 5: Add barriers (1/6 of total hexes)
        self._add_barriers()
        
        # Step 6: Add rivers and lakes
        self._add_water_features()
        
        # Step 7: Generate descriptions
        self._generate_descriptions()
        
        # Create final realm data
        realm_data = {
            "name": realm_name,
            "size": self.size,
            "coastal": coastal,
            "seat_of_power": {"x": self.seat_of_power[0], "y": self.seat_of_power[1]} if self.seat_of_power else None,
            "hexes": {f"{x},{y}": hex_obj.to_dict() for (x, y), hex_obj in self.hexes.items()},
            "holdings": [{"x": x, "y": y, "type": self.hexes[(x, y)].holding.value} for x, y in self.holdings],
            "myths": [{"x": x, "y": y, "name": myth_name} for (x, y), myth_name in self.myths],
            "landmarks": [{"x": x, "y": y, "type": self.hexes[(x, y)].landmark.value} for x, y in self.landmarks],
            "metadata": {
                "total_hexes": self.size * self.size,
                "wilderness_hexes": len([h for h in self.hexes.values() if h.is_wilderness]),
                "holdings_count": len(self.holdings),
                "myths_count": len(self.myths),
                "landmarks_count": len(self.landmarks)
            }
        }
        
        info(f"Generated realm '{realm_name}' with {len(self.holdings)} holdings and {len(self.myths)} myths", 
             category="realm_generation")
        return realm_data
    
    def _generate_terrain(self, coastal):
        """Generate base terrain using clusters"""
        # Create terrain clusters (groups of d12 hexes of same type)
        terrain_types = [TerrainType.FOREST, TerrainType.HILLS, TerrainType.PLAINS, 
                        TerrainType.MOUNTAINS, TerrainType.SWAMP]
        
        if coastal == "island":
            # Islands have more coast hexes
            terrain_types.extend([TerrainType.COAST] * 3)
        elif coastal:
            # Coastal realms have some coast
            terrain_types.append(TerrainType.COAST)
        
        # Generate 5-8 terrain clusters
        num_clusters = random.randint(5, 8)
        cluster_size = random.randint(6, 12)  # d12 hexes per cluster
        
        for _ in range(num_clusters):
            terrain = random.choice(terrain_types)
            
            # Pick a random starting point
            start_x = random.randint(0, self.size - 1)
            start_y = random.randint(0, self.size - 1)
            
            # Grow cluster from starting point
            cluster_hexes = {(start_x, start_y)}
            self.hexes[(start_x, start_y)].terrain = terrain
            
            # Add adjacent hexes to cluster
            for _ in range(cluster_size - 1):
                if not cluster_hexes:
                    break
                
                # Pick a random hex from the cluster to expand from
                expand_from = random.choice(list(cluster_hexes))
                adjacent = self._get_adjacent_hexes(expand_from[0], expand_from[1])
                
                # Find valid adjacent hexes not already in cluster
                valid_adjacent = [(x, y) for x, y in adjacent 
                                if (x, y) in self.hexes and (x, y) not in cluster_hexes]
                
                if valid_adjacent:
                    new_hex = random.choice(valid_adjacent)
                    cluster_hexes.add(new_hex)
                    self.hexes[new_hex].terrain = terrain
        
        # Coastal realms get coast hexes along edges
        if coastal == True or coastal == "island":
            self._add_coastal_hexes(coastal == "island")
    
    def _add_coastal_hexes(self, is_island: bool):
        """Add coastal hexes along the edges"""
        if is_island:
            # Islands have coast all around the edges
            for x in range(self.size):
                for y in range(self.size):
                    if x == 0 or x == self.size - 1 or y == 0 or y == self.size - 1:
                        self.hexes[(x, y)].terrain = TerrainType.COAST
        else:
            # Coastal realms have coast along one or two edges
            edges = ["north", "south", "east", "west"]
            coastal_edges = random.sample(edges, random.randint(1, 2))
            
            for edge in coastal_edges:
                if edge == "north":
                    for x in range(self.size):
                        self.hexes[(x, 0)].terrain = TerrainType.COAST
                elif edge == "south":
                    for x in range(self.size):
                        self.hexes[(x, self.size - 1)].terrain = TerrainType.COAST
                elif edge == "east":
                    for y in range(self.size):
                        self.hexes[(self.size - 1, y)].terrain = TerrainType.COAST
                elif edge == "west":
                    for y in range(self.size):
                        self.hexes[(0, y)].terrain = TerrainType.COAST
    
    def _place_holdings(self):
        """Place 4 Holdings with good distance apart, one as Seat of Power"""
        holding_types = [HoldingType.CASTLE, HoldingType.TOWN, HoldingType.FORTRESS, HoldingType.TOWER]
        
        # Place holdings with minimum distance between them
        min_distance = max(3, self.size // 4)
        attempts = 0
        max_attempts = 100
        
        while len(self.holdings) < 4 and attempts < max_attempts:
            x = random.randint(1, self.size - 2)  # Avoid edges
            y = random.randint(1, self.size - 2)
            
            # Check distance from existing holdings
            too_close = False
            for hx, hy in self.holdings:
                distance = math.sqrt((x - hx)**2 + (y - hy)**2)
                if distance < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                holding_type = holding_types[len(self.holdings)]
                self.holdings.append((x, y))
                self.hexes[(x, y)].holding = holding_type
                self.hexes[(x, y)].is_wilderness = False
                debug(f"Placed {holding_type.value} at ({x}, {y})", category="realm_generation")
            
            attempts += 1
        
        # Designate first holding as Seat of Power
        if self.holdings:
            seat_x, seat_y = self.holdings[0]
            self.hexes[(seat_x, seat_y)].holding = HoldingType.SEAT_OF_POWER
            self.seat_of_power = (seat_x, seat_y)
            debug(f"Designated Seat of Power at ({seat_x}, {seat_y})", category="realm_generation")
    
    def _place_myths(self):
        """Place 6 Myths in remote places"""
        # Get all available Knights and Myths for random selection
        try:
            available_myths = list(mythic_generators.myths.keys())
            if len(available_myths) < 6:
                warning("Not enough myths available, duplicating some", category="realm_generation")
                available_myths = (available_myths * 3)[:6]  # Ensure we have enough
        except:
            # Fallback if mythic_generators not available
            available_myths = [f"Myth_{i}" for i in range(1, 7)]
        
        # Find remote locations (far from holdings)
        remote_candidates = []
        for x in range(self.size):
            for y in range(self.size):
                if self.hexes[(x, y)].is_wilderness:
                    # Check distance from all holdings
                    min_distance_to_holding = float('inf')
                    for hx, hy in self.holdings:
                        distance = math.sqrt((x - hx)**2 + (y - hy)**2)
                        min_distance_to_holding = min(min_distance_to_holding, distance)
                    
                    # Remote places are at least 4 hexes from holdings
                    if min_distance_to_holding >= 4:
                        remote_candidates.append((x, y))
        
        # If we don't have enough remote places, relax the criteria
        if len(remote_candidates) < 6:
            remote_candidates = [(x, y) for x in range(self.size) for y in range(self.size) 
                               if self.hexes[(x, y)].is_wilderness]
        
        # Place 6 myths
        selected_locations = random.sample(remote_candidates, min(6, len(remote_candidates)))
        selected_myths = random.sample(available_myths, min(6, len(available_myths)))
        
        for i, (x, y) in enumerate(selected_locations):
            myth_name = selected_myths[i] if i < len(selected_myths) else f"Unknown_Myth_{i}"
            self.myths.append(((x, y), myth_name))
            self.hexes[(x, y)].myth = myth_name
            debug(f"Placed {myth_name} at ({x}, {y})", category="realm_generation")
    
    def _place_landmarks(self):
        """Place 3-4 of each landmark type"""
        landmark_types = list(LandmarkType)
        
        for landmark_type in landmark_types:
            count = random.randint(3, 4)
            placed = 0
            attempts = 0
            max_attempts = 50
            
            while placed < count and attempts < max_attempts:
                x = random.randint(0, self.size - 1)
                y = random.randint(0, self.size - 1)
                
                hex_obj = self.hexes[(x, y)]
                
                # Only place in wilderness hexes without other features
                if hex_obj.is_wilderness and hex_obj.landmark is None and hex_obj.myth is None:
                    hex_obj.landmark = landmark_type
                    self.landmarks.append((x, y))
                    placed += 1
                    debug(f"Placed {landmark_type.value} at ({x}, {y})", category="realm_generation")
                
                attempts += 1
    
    def _add_barriers(self):
        """Add barriers on hex edges (1/6 of total hexes)"""
        total_hexes = self.size * self.size
        num_barriers = total_hexes // 6
        
        directions = ["north", "northeast", "southeast", "south", "southwest", "northwest"]
        
        for _ in range(num_barriers):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            direction = random.choice(directions)
            
            self.hexes[(x, y)].barriers.append(direction)
    
    def _add_water_features(self):
        """Add navigable rivers and large lakes"""
        # Add 1-2 rivers
        num_rivers = random.randint(1, 2)
        for _ in range(num_rivers):
            self._create_river()
        
        # Add 1-3 lakes spanning whole hexes
        num_lakes = random.randint(1, 3)
        for _ in range(num_lakes):
            self._create_lake()
    
    def _create_river(self):
        """Create a navigable river passing through the realm"""
        # Rivers typically run from one edge to another
        start_edge = random.choice(["north", "south", "east", "west"])
        
        if start_edge == "north":
            start = (random.randint(0, self.size - 1), 0)
            end = (random.randint(0, self.size - 1), self.size - 1)
        elif start_edge == "south":
            start = (random.randint(0, self.size - 1), self.size - 1)
            end = (random.randint(0, self.size - 1), 0)
        elif start_edge == "east":
            start = (self.size - 1, random.randint(0, self.size - 1))
            end = (0, random.randint(0, self.size - 1))
        else:  # west
            start = (0, random.randint(0, self.size - 1))
            end = (self.size - 1, random.randint(0, self.size - 1))
        
        # Create a meandering path from start to end
        current = start
        river_hexes = []
        
        while current != end and len(river_hexes) < self.size * 2:
            river_hexes.append(current)
            
            # Move towards the end with some randomness
            dx = 1 if end[0] > current[0] else (-1 if end[0] < current[0] else 0)
            dy = 1 if end[1] > current[1] else (-1 if end[1] < current[1] else 0)
            
            # Add some meandering
            if random.random() < 0.3:
                dx += random.choice([-1, 0, 1])
                dy += random.choice([-1, 0, 1])
            
            next_x = max(0, min(self.size - 1, current[0] + dx))
            next_y = max(0, min(self.size - 1, current[1] + dy))
            current = (next_x, next_y)
        
        # Mark river hexes
        for x, y in river_hexes:
            if self.hexes[(x, y)].terrain not in [TerrainType.LAKE, TerrainType.COAST]:
                self.hexes[(x, y)].terrain = TerrainType.RIVER
    
    def _create_lake(self):
        """Create a large lake spanning one or more hexes"""
        center_x = random.randint(1, self.size - 2)
        center_y = random.randint(1, self.size - 2)
        
        # Lake size: 1-4 hexes
        lake_size = random.randint(1, 4)
        lake_hexes = [(center_x, center_y)]
        
        # Expand lake to adjacent hexes
        for _ in range(lake_size - 1):
            if lake_hexes:
                expand_from = random.choice(lake_hexes)
                adjacent = self._get_adjacent_hexes(expand_from[0], expand_from[1])
                valid_adjacent = [(x, y) for x, y in adjacent 
                                if (x, y) in self.hexes and (x, y) not in lake_hexes 
                                and self.hexes[(x, y)].holding is None]
                
                if valid_adjacent:
                    new_hex = random.choice(valid_adjacent)
                    lake_hexes.append(new_hex)
        
        # Mark lake hexes
        for x, y in lake_hexes:
            self.hexes[(x, y)].terrain = TerrainType.LAKE
    
    def _get_adjacent_hexes(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get adjacent hex coordinates"""
        # Hex grid adjacency (flat-top hexes)
        if y % 2 == 0:  # Even rows
            adjacent = [
                (x, y - 1), (x + 1, y - 1),  # North, northeast
                (x + 1, y), (x, y + 1),      # East, south
                (x - 1, y + 1), (x - 1, y)  # Southwest, west
            ]
        else:  # Odd rows
            adjacent = [
                (x - 1, y - 1), (x, y - 1),  # Northwest, north
                (x + 1, y), (x, y + 1),      # East, south
                (x - 1, y + 1), (x - 1, y)  # Southwest, west
            ]
        
        return [(ax, ay) for ax, ay in adjacent if 0 <= ax < self.size and 0 <= ay < self.size]
    
    def _generate_descriptions(self):
        """Generate descriptions for hexes based on their features"""
        for hex_obj in self.hexes.values():
            description_parts = []
            
            # Base terrain description
            terrain_descriptions = {
                TerrainType.FOREST: "Dense woodland with ancient trees",
                TerrainType.HILLS: "Rolling hills dotted with wildflowers",
                TerrainType.MOUNTAINS: "Towering peaks shrouded in mist",
                TerrainType.PLAINS: "Open grasslands stretching to the horizon",
                TerrainType.SWAMP: "Murky wetlands thick with fog",
                TerrainType.DESERT: "Endless sands beneath scorching sun",
                TerrainType.COAST: "Rocky shores battered by waves",
                TerrainType.RIVER: "A broad river flowing through the land",
                TerrainType.LAKE: "A pristine lake reflecting the sky"
            }
            
            description_parts.append(terrain_descriptions.get(hex_obj.terrain, "Wilderness"))
            
            # Add holding description
            if hex_obj.holding:
                holding_descriptions = {
                    HoldingType.CASTLE: "dominated by an imposing castle",
                    HoldingType.TOWN: "bustling with the activity of a market town",
                    HoldingType.FORTRESS: "fortified with strong defensive walls",
                    HoldingType.TOWER: "watched over by a tall stone tower",
                    HoldingType.SEAT_OF_POWER: "crowned by the magnificent Seat of Power"
                }
                description_parts.append(holding_descriptions.get(hex_obj.holding, "with a settlement"))
            
            # Add landmark description
            if hex_obj.landmark:
                landmark_descriptions = {
                    LandmarkType.DWELLING: "where humble dwellings dot the landscape",
                    LandmarkType.SANCTUM: "blessed by the presence of a Seer's sanctum",
                    LandmarkType.MONUMENT: "marked by an ancient monument of inspiration",
                    LandmarkType.HAZARD: "dangerous with natural hazards",
                    LandmarkType.CURSE: "blighted by an ancient curse",
                    LandmarkType.RUIN: "haunted by mysterious ruins"
                }
                description_parts.append(landmark_descriptions.get(hex_obj.landmark, "of interest"))
            
            # Add myth description
            if hex_obj.myth:
                description_parts.append(f"touched by the Myth of {hex_obj.myth}")
            
            hex_obj.description = ", ".join(description_parts) + "."

# Convenience functions for external use
def generate_realm(name: str, coastal: bool = None) -> Dict:
    """Generate a realm using the official Mythic Bastionland system"""
    generator = RealmGenerator()
    return generator.generate_realm(name, coastal)

def generate_island_realm(name: str) -> Dict:
    """Generate an island realm"""
    return generate_realm(name, "island")

def generate_coastal_realm(name: str) -> Dict:
    """Generate a coastal realm"""
    return generate_realm(name, True)

def generate_landlocked_realm(name: str) -> Dict:
    """Generate a landlocked realm"""
    return generate_realm(name, False)

if __name__ == "__main__":
    # Test the generator
    realm = generate_realm("Test Realm")
    print(json.dumps(realm, indent=2))