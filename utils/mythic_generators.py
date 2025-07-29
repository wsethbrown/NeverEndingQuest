#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Content Generators

Utility functions to access the rich generator tables from Knights and Myths.
Provides programmatic access to location tables, Knight generators, Seer information,
and other random content from the converted mythic_knights.json and mythic_myths.json files.

This module allows developers and AI systems to easily use the extensive random tables
and generators that are part of each Knight archetype and Myth.
"""

import json
import random
from typing import Dict, List, Any, Optional, Union
from utils.encoding_utils import safe_json_load
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("mythic_generators")

class MythicGenerators:
    """Access to all Mythic Bastionland random generators and tables"""
    
    def __init__(self):
        """Initialize by loading mythic data files"""
        self.knights_data = safe_json_load('data/mythic_knights.json')
        self.myths_data = safe_json_load('data/mythic_myths.json')
        
        if not self.knights_data or not self.myths_data:
            error("Failed to load mythic data files", category="generators")
            raise RuntimeError("Missing mythic data files required for generators")
        
        self.knights = self.knights_data.get('knights', {})
        self.myths = self.myths_data.get('myths', {})
    
    def get_random_knight(self) -> Dict[str, Any]:
        """Get a random Knight archetype with all their data"""
        knight_names = list(self.knights.keys())
        if not knight_names:
            return {}
        
        knight_name = random.choice(knight_names)
        return {
            'name': knight_name,
            **self.knights[knight_name]
        }
    
    def get_knight_by_name(self, knight_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific Knight archetype by name"""
        knight_data = self.knights.get(knight_name)
        if knight_data:
            return {
                'name': knight_name,
                **knight_data
            }
        return None
    
    def get_knight_seer(self, knight_name: str) -> Optional[str]:
        """Get the Seer associated with a specific Knight (not for general NPC generation)"""
        knight_data = self.knights.get(knight_name, {})
        return knight_data.get('seer')
    
    def get_knight_tables(self, knight_name: str) -> Dict[str, Any]:
        """Get all random tables associated with a Knight"""
        knight_data = self.knights.get(knight_name, {})
        tables = {}
        
        # Extract all table-like structures (dictionaries with numeric keys)
        for key, value in knight_data.items():
            if isinstance(value, dict) and key.endswith('_table'):
                tables[key] = value
        
        return tables
    
    def roll_on_knight_table(self, knight_name: str, table_name: str, dice: str = 'd6') -> Optional[Dict[str, Any]]:
        """Roll on a specific Knight table"""
        knight_data = self.knights.get(knight_name, {})
        table = knight_data.get(table_name, {})
        
        if not table:
            return None
        
        # Roll dice
        if dice == 'd6':
            roll = random.randint(1, 6)
        elif dice == 'd12':
            roll = random.randint(1, 12)
        else:
            roll = random.randint(1, 6)  # Default to d6
        
        return table.get(str(roll))
    
    def get_random_myth(self) -> Dict[str, Any]:
        """Get a random Myth with all their data"""
        myth_names = list(self.myths.keys())
        if not myth_names:
            return {}
        
        myth_name = random.choice(myth_names)
        return {
            'name': myth_name,
            **self.myths[myth_name]
        }
    
    def get_myth_by_name(self, myth_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific Myth by name"""
        myth_data = self.myths.get(myth_name)
        if myth_data:
            return {
                'name': myth_name,
                **myth_data
            }
        return None
    
    def get_myth_locations(self, myth_name: str) -> Dict[str, str]:
        """Get location generators for a specific Myth"""
        myth_data = self.myths.get(myth_name, {})
        locations = myth_data.get('locations', {})
        
        # Also check for legacy location structure
        if not locations:
            legacy_locations = {}
            for location_type in ['dwelling', 'sanctum', 'monument', 'hazard', 'curse', 'ruin']:
                if location_type in myth_data:
                    legacy_locations[location_type] = myth_data[location_type]
            return legacy_locations
        
        return locations
    
    def get_random_location(self, location_type: str = None) -> Dict[str, str]:
        """Get a random location from any Myth"""
        all_locations = []
        
        for myth_name, myth_data in self.myths.items():
            locations = self.get_myth_locations(myth_name)
            for loc_type, loc_name in locations.items():
                if location_type is None or loc_type == location_type:
                    all_locations.append({
                        'type': loc_type,
                        'name': loc_name,
                        'source_myth': myth_name
                    })
        
        if not all_locations:
            return {}
        
        return random.choice(all_locations)
    
    def get_myth_cast(self, myth_name: str) -> List[Dict[str, Any]]:
        """Get the cast of characters from a specific Myth"""
        myth_data = self.myths.get(myth_name, {})
        return myth_data.get('cast', [])
    
    def get_random_cast_member(self, myth_name: str = None) -> Dict[str, Any]:
        """Get a random cast member, optionally from a specific Myth"""
        if myth_name:
            cast = self.get_myth_cast(myth_name)
            if cast:
                return random.choice(cast)
            return {}
        
        # Get from any myth
        all_cast = []
        for myth_name, myth_data in self.myths.items():
            cast = myth_data.get('cast', [])
            for member in cast:
                member['source_myth'] = myth_name
                all_cast.append(member)
        
        if not all_cast:
            return {}
        
        return random.choice(all_cast)
    
    def get_myth_omens(self, myth_name: str) -> List[str]:
        """Get the omens from a specific Myth"""
        myth_data = self.myths.get(myth_name, {})
        return myth_data.get('omens', [])
    
    def get_random_omen(self, myth_name: str = None) -> Dict[str, str]:
        """Get a random omen, optionally from a specific Myth"""
        if myth_name:
            omens = self.get_myth_omens(myth_name)
            if omens:
                return {
                    'omen': random.choice(omens),
                    'source_myth': myth_name
                }
            return {}
        
        # Get from any myth
        all_omens = []
        for myth_name, myth_data in self.myths.items():
            omens = myth_data.get('omens', [])
            for omen in omens:
                all_omens.append({
                    'omen': omen,
                    'source_myth': myth_name
                })
        
        if not all_omens:
            return {}
        
        return random.choice(all_omens)
    
    def generate_location_set(self, count: int = 6) -> List[Dict[str, str]]:
        """Generate a set of varied locations for a region"""
        location_types = ['dwelling', 'sanctum', 'monument', 'hazard', 'curse', 'ruin']
        locations = []
        
        for i in range(count):
            loc_type = location_types[i % len(location_types)]
            location = self.get_random_location(loc_type)
            if location:
                locations.append(location)
        
        return locations
    
    def generate_encounter_seed(self) -> Dict[str, Any]:
        """Generate a complete encounter seed with Knight, Myth, and location"""
        knight = self.get_random_knight()
        myth = self.get_random_myth()
        location = self.get_random_location()
        cast_member = self.get_random_cast_member()
        
        return {
            'knight': knight,
            'myth': myth,
            'location': location,
            'npc': cast_member,
            'omen': self.get_random_omen(myth.get('name')),
            'seer': self.get_knight_seer(knight.get('name')) if knight else None
        }
    
    def get_knight_names_by_dice(self, d6_value: int) -> List[str]:
        """Get all Knight names for a specific d6 value (1-6)"""
        knights = []
        for name, data in self.knights.items():
            if data.get('d6') == d6_value:
                knights.append(name)
        return knights
    
    def get_myth_names_by_dice(self, d6_value: int) -> List[str]:
        """Get all Myth names for a specific d6 value (1-6)"""
        myths = []
        for name, data in self.myths.items():
            if data.get('d6') == d6_value:
                myths.append(name)
        return myths
    
    def roll_random_knight_by_dice(self) -> Dict[str, Any]:
        """Roll random dice to select a Knight (as per Mythic Bastionland rules)"""
        d6_roll = random.randint(1, 6)
        d12_roll = random.randint(1, 12)
        
        # Find knight matching both dice
        for name, data in self.knights.items():
            if data.get('d6') == d6_roll and data.get('d12') == d12_roll:
                return {
                    'name': name,
                    'dice_rolled': {'d6': d6_roll, 'd12': d12_roll},
                    **data
                }
        
        # Fallback to any knight with matching d6
        knights = self.get_knight_names_by_dice(d6_roll)
        if knights:
            knight_name = random.choice(knights)
            return {
                'name': knight_name,
                'dice_rolled': {'d6': d6_roll, 'd12': d12_roll},
                **self.knights[knight_name]
            }
        
        # Final fallback to completely random knight
        return self.get_random_knight()
    
    def roll_random_myth_by_dice(self) -> Dict[str, Any]:
        """Roll random dice to select a Myth (as per Mythic Bastionland rules)"""
        d6_roll = random.randint(1, 6)
        d12_roll = random.randint(1, 12)
        
        # Find myth matching both dice
        for name, data in self.myths.items():
            if data.get('d6') == d6_roll and data.get('d12') == d12_roll:
                return {
                    'name': name,
                    'dice_rolled': {'d6': d6_roll, 'd12': d12_roll},
                    **data
                }
        
        # Fallback to any myth with matching d6
        myths = self.get_myth_names_by_dice(d6_roll)
        if myths:
            myth_name = random.choice(myths)
            return {
                'name': myth_name,
                'dice_rolled': {'d6': d6_roll, 'd12': d12_roll},
                **self.myths[myth_name]
            }
        
        # Final fallback to completely random myth
        return self.get_random_myth()

# Global instance for easy access
mythic_generators = MythicGenerators()

# Convenience functions for easy access
def get_random_knight() -> Dict[str, Any]:
    """Get a random Knight archetype"""
    return mythic_generators.get_random_knight()

def get_random_myth() -> Dict[str, Any]:
    """Get a random Myth"""
    return mythic_generators.get_random_myth()

def get_random_location(location_type: str = None) -> Dict[str, str]:
    """Get a random location"""
    return mythic_generators.get_random_location(location_type)

def generate_encounter_seed() -> Dict[str, Any]:
    """Generate a complete encounter seed"""
    return mythic_generators.generate_encounter_seed()

if __name__ == "__main__":
    # Test the generators
    print("=== MYTHIC BASTIONLAND GENERATORS TEST ===")
    
    # Test Knight generation
    print("\n--- Random Knight ---")
    knight = get_random_knight()
    print(f"Knight: {knight.get('name', 'Unknown')}")
    print(f"Quote: {knight.get('quote', 'No quote')}")
    
    # Test Myth generation  
    print("\n--- Random Myth ---")
    myth = get_random_myth()
    print(f"Myth: {myth.get('name', 'Unknown')}")
    print(f"Quote: {myth.get('quote', 'No quote')}")
    
    # Test location generation
    print("\n--- Random Locations ---")
    for location_type in ['dwelling', 'monument', 'hazard']:
        location = get_random_location(location_type)
        print(f"{location_type.title()}: {location.get('name', 'Unknown')} (from {location.get('source_myth', 'Unknown myth')})")
    
    # Test encounter seed
    print("\n--- Encounter Seed ---")
    encounter = generate_encounter_seed()
    print(f"Knight: {encounter['knight'].get('name', 'Unknown')}")
    print(f"Myth: {encounter['myth'].get('name', 'Unknown')}")
    print(f"Location: {encounter['location'].get('name', 'Unknown')} ({encounter['location'].get('type', 'unknown type')})")
    print(f"NPC: {encounter['npc'].get('name', 'Unknown')}")
    
    print("\n--- Test Complete ---")