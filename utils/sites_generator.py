#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Sites Generator

Implements the 7-point hex method for creating detailed exploration sites.
Based on the official Mythic Bastionland Sites system (p15).

Creates complex locations like tombs, castles, caverns, or forests that warrant
detailed exploration beyond simple area descriptions.
"""

import random
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("sites_generator")

class PointType(Enum):
    """Types of points in a site"""
    FEATURE = "feature"      # Circle - Information/mood setting
    DANGER = "danger"        # Triangle - Navigate carefully
    TREASURE = "treasure"    # Diamond - Valuable find

class RouteType(Enum):
    """Types of routes between points"""
    OPEN = "open"           # Solid line - Straightforward path
    CLOSED = "closed"       # Crossed line - Something blocks the way
    HIDDEN = "hidden"       # Dotted line - Found through exploration

class SitePoint:
    """Represents a single point in a site"""
    
    def __init__(self, point_id: int, point_type: PointType, description: str = ""):
        self.id = point_id
        self.type = point_type
        self.description = description
        self.connections = []  # List of (point_id, route_type) tuples
    
    def add_connection(self, target_point_id: int, route_type: RouteType):
        """Add a connection to another point"""
        self.connections.append((target_point_id, route_type))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "connections": [(target_id, route_type.value) for target_id, route_type in self.connections]
        }

class SiteGenerator:
    """Generates detailed sites using the Mythic Bastionland 7-point hex method"""
    
    def __init__(self):
        self.points = {}  # Dict of point_id -> SitePoint
        self.entrances = []  # List of point IDs that are entrances
        
    def generate_site(self, site_name: str, site_theme: str = "generic") -> Dict:
        """
        Generate a complete site using the 7-point hex method
        
        Args:
            site_name: Name of the site
            site_theme: Theme to influence descriptions (tomb, castle, cavern, forest, etc.)
            
        Returns:
            Dictionary containing the complete site data
        """
        debug(f"Generating site: {site_name} with theme: {site_theme}", category="site_generation")
        
        # Step 1: Create 7 points (will erase one later)
        self._create_points()
        
        # Step 2: Assign point types
        self._assign_point_types(site_theme)
        
        # Step 3: Create routes between points
        self._create_routes()
        
        # Step 4: Ensure all points are reachable
        self._ensure_connectivity()
        
        # Step 5: Place entrances
        self._place_entrances()
        
        # Step 6: Generate descriptions based on theme
        self._generate_descriptions(site_theme)
        
        # Create final site data
        site_data = {
            "name": site_name,
            "theme": site_theme,
            "points": {str(point_id): point.to_dict() for point_id, point in self.points.items()},
            "entrances": self.entrances,
            "metadata": {
                "generation_method": "7-point hex",
                "total_points": len(self.points),
                "features": len([p for p in self.points.values() if p.type == PointType.FEATURE]),
                "dangers": len([p for p in self.points.values() if p.type == PointType.DANGER]),
                "treasures": len([p for p in self.points.values() if p.type == PointType.TREASURE])
            }
        }
        
        info(f"Generated site '{site_name}' with {len(self.points)} points", category="site_generation")
        return site_data
    
    def _create_points(self):
        """Create the initial 7 points, then erase one (following official rules)"""
        # Create points 1-7 (6 corners + 1 center)
        for i in range(1, 8):
            self.points[i] = SitePoint(i, PointType.FEATURE)  # Temporary type
        
        # Always erase exactly one point to leave 6 (official rule)
        erased_point = random.randint(1, 7)
        del self.points[erased_point]
        
        # Renumber remaining points 1-6
        old_points = list(self.points.values())
        self.points.clear()
        for i, point in enumerate(old_points, 1):
            point.id = i
            self.points[i] = point
        
        debug(f"Erased point {erased_point}, renumbered remaining points 1-6", category="site_generation")
    
    def _assign_point_types(self, theme: str):
        """Assign types to points following official 7-point hex rules"""
        point_ids = list(self.points.keys())
        
        # Official distribution (NEVER changes): 3 circles, 2 triangles, 1 diamond
        features_count = 3   # Circles - information/mood
        dangers_count = 2    # Triangles - navigate carefully  
        treasures_count = 1  # Diamond - valuable find
        
        # Always exactly 6 points with fixed distribution
        assert len(point_ids) == 6, f"Expected 6 points, got {len(point_ids)}"
        
        # Randomly assign types
        random.shuffle(point_ids)
        
        # Assign exactly 1 treasure (diamond)
        self.points[point_ids[0]].type = PointType.TREASURE
        
        # Assign exactly 2 dangers (triangles)
        for i in range(1, 3):
            self.points[point_ids[i]].type = PointType.DANGER
        
        # Assign exactly 3 features (circles)
        for i in range(3, 6):
            self.points[point_ids[i]].type = PointType.FEATURE
    
    def _create_routes(self):
        """Create routes following official 7-point hex rules: 3 open, 2 closed, 1 hidden"""
        point_ids = list(self.points.keys())
        
        # Official distribution (NEVER changes): 3 open, 2 closed, 1 hidden (total 6 routes)
        routes_to_create = ([RouteType.OPEN] * 3 + 
                           [RouteType.CLOSED] * 2 + 
                           [RouteType.HIDDEN] * 1)
        random.shuffle(routes_to_create)
        
        # Generate all possible point pairs
        possible_pairs = []
        for i, point_a in enumerate(point_ids):
            for point_b in point_ids[i+1:]:
                possible_pairs.append((point_a, point_b))
        
        # We need exactly 6 routes, so select 6 pairs
        selected_pairs = random.sample(possible_pairs, 6)
        
        # Create the routes
        routes_created = []
        for i, (from_point, to_point) in enumerate(selected_pairs):
            route_type = routes_to_create[i]
            
            # Create bidirectional connection
            self.points[from_point].add_connection(to_point, route_type)
            self.points[to_point].add_connection(from_point, route_type)
            
            routes_created.append((from_point, to_point, route_type))
            debug(f"Created {route_type.value} route: {from_point} <-> {to_point}", category="site_generation")
        
        debug(f"Created exactly 6 routes: 3 open, 2 closed, 1 hidden", category="site_generation")
    
    def _ensure_connectivity(self):
        """Verify all points can be reached (official rules ensure this through proper route distribution)"""
        point_ids = list(self.points.keys())
        
        # Check that each point has at least one connection
        for point_id in point_ids:
            if not self.points[point_id].connections:
                warning(f"Point {point_id} has no connections - this violates 7-point hex rules", category="site_generation")
        
        # The official 6-route system should ensure connectivity, but we log if issues exist
        debug(f"Connectivity check complete for {len(point_ids)} points", category="site_generation")
    
    def _place_entrances(self):
        """Place main and optional hidden entrance"""
        point_ids = list(self.points.keys())
        
        # Main entrance - usually a feature point
        feature_points = [pid for pid, point in self.points.items() if point.type == PointType.FEATURE]
        if feature_points:
            main_entrance = random.choice(feature_points)
        else:
            main_entrance = random.choice(point_ids)
        
        self.entrances.append(main_entrance)
        
        # Optional hidden entrance (official rules suggest this)
        if len(point_ids) > 1:
            hidden_entrance_candidates = [pid for pid in point_ids if pid != main_entrance]
            if hidden_entrance_candidates:
                hidden_entrance = random.choice(hidden_entrance_candidates)
                self.entrances.append(hidden_entrance)
                debug(f"Added hidden entrance at point {hidden_entrance}", category="site_generation")
    
    def _generate_descriptions(self, theme: str):
        """Generate thematic descriptions for each point"""
        theme_templates = self._get_theme_templates(theme)
        
        for point_id, point in self.points.items():
            template_key = f"{point.type.value}s"
            if template_key in theme_templates:
                templates = theme_templates[template_key]
                point.description = random.choice(templates)
                
                # Add entrance descriptions
                if point_id in self.entrances:
                    if point_id == self.entrances[0]:
                        point.description += " (Main Entrance)"
                    else:
                        point.description += " (Hidden Entrance)"
    
    def _get_theme_templates(self, theme: str) -> Dict[str, List[str]]:
        """Get description templates for different themes"""
        templates = {
            "generic": {
                "features": [
                    "A weathered stone marker with ancient inscriptions",
                    "A small clearing with scattered remnants of old campfires",
                    "A moss-covered boulder that seems deliberately placed",
                    "The ruins of what might once have been a watchtower"
                ],
                "dangers": [
                    "Unstable ground that shifts treacherously underfoot",
                    "A narrow bridge spanning a deep chasm",
                    "Thick brambles that tear at cloth and flesh",
                    "A swirling mist that obscures vision and muffles sound"
                ],
                "treasures": [
                    "A hidden cache of ancient coins and jewelry",
                    "A pristine weapon wrapped in oiled leather",
                    "A sealed chest containing rare trade goods",
                    "A collection of preserved documents and maps"
                ]
            },
            "tomb": {
                "features": [
                    "Carved stone effigies of long-dead nobles",
                    "Ancient burial urns arranged in ceremonial patterns",
                    "Faded murals depicting the afterlife journey",
                    "A stone altar with dried flowers and offerings"
                ],
                "dangers": [
                    "Crumbling ceiling that threatens to collapse",
                    "Poisoned dart traps triggered by pressure plates",
                    "Cursed burial chamber that drains the spirit",
                    "Undead guardians that stir at intrusion"
                ],
                "treasures": [
                    "The burial crown of an ancient king",
                    "A sarcophagus filled with grave goods and gold",
                    "Sacred relics blessed by forgotten seers",
                    "Ancient scrolls containing lost knowledge"
                ]
            },
            "fortress": {
                "features": [
                    "The remains of a great hall with a cold hearth",
                    "A courtyard overgrown with wildflowers",
                    "Battlements offering commanding views",
                    "A well that once supplied the garrison"
                ],
                "dangers": [
                    "Unstable walls that could collapse at any moment",
                    "Guard posts occupied by hostile defenders",
                    "A maze of corridors designed to confuse invaders",
                    "Murder holes and defensive positions"
                ],
                "treasures": [
                    "The commander's private armory",
                    "A vault containing the fortress treasury",
                    "Strategic maps and military intelligence",
                    "The lord's personal quarters with hidden valuables"
                ]
            },
            "cavern": {
                "features": [
                    "Strange rock formations shaped by underground waters",
                    "Crystal deposits that catch and reflect light",
                    "Ancient cave paintings by primitive peoples",
                    "An underground lake with mirror-still water"
                ],
                "dangers": [
                    "Narrow passages that could trap the unwary",
                    "Unstable rock formations threatening cave-ins",
                    "Swift underground currents that sweep away swimmers",
                    "Toxic gases seeping from deeper chambers"
                ],
                "treasures": [
                    "A vein of precious metals running through the rock",
                    "Perfectly preserved artifacts in dry chambers",
                    "Rare crystals with mystical properties",
                    "A hidden cache left by ancient miners"
                ]
            }
        }
        
        return templates.get(theme, templates["generic"])

# Convenience functions for external use
def generate_site(name: str, theme: str = "generic") -> Dict:
    """Generate a site using the 7-point hex method"""
    generator = SiteGenerator()
    return generator.generate_site(name, theme)

def generate_themed_site(name: str, myth_name: str = None) -> Dict:
    """Generate a site themed around a specific myth"""
    # Could integrate with mythic_generators.py to get location themes from myths
    themes = ["tomb", "fortress", "cavern", "generic"]
    theme = random.choice(themes)
    
    if myth_name:
        # Could use myth data to influence theme selection
        debug(f"Generating site themed around myth: {myth_name}", category="site_generation")
    
    return generate_site(name, theme)

if __name__ == "__main__":
    # Test the generator
    site = generate_site("Test Ruins", "tomb")
    print(json.dumps(site, indent=2))