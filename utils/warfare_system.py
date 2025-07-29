#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Warfare System

Implements the official Warfare rules from Mythic Bastionland (p11).
Handles Warbands, large-scale combat, siege equipment, and structures.

Key Features:
- Warband system (groups of ~24 combatants as single entities)
- Warband types: Militia, Skirmishers, Mercenaries, Riders, Knights
- Siege equipment and artillery
- Ship and structure combat
- Large-scale battle mechanics
"""

import random
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("warfare_system")

class WarbandType(Enum):
    """Types of Warbands available"""
    MILITIA = "militia"
    SKIRMISHERS = "skirmishers"
    MERCENARIES = "mercenaries"
    RIDERS = "riders"
    KNIGHTS = "knights"

class StructureType(Enum):
    """Types of structures in warfare"""
    GATE = "gate"
    RAMPART = "rampart"
    CASTLE_WALL = "castle_wall"
    ROWBOAT = "rowboat"
    LONGSHIP = "longship"
    WARSHIP = "warship"
    SIEGE_TOWER = "siege_tower"

class ArtilleryType(Enum):
    """Types of siege equipment"""
    BATTERING_RAM = "battering_ram"
    STONE_THROWER = "stone_thrower"
    BOLT_LAUNCHER = "bolt_launcher"
    TREBUCHET = "trebuchet"

class Warband:
    """Represents a Warband in large-scale combat"""
    
    def __init__(self, warband_type: WarbandType, name: str = ""):
        self.type = warband_type
        self.name = name or f"{warband_type.value.title()} Warband"
        
        # Set stats based on type (from official rules)
        self.stats = self._get_warband_stats(warband_type)
        
        # Current state
        self.current_vigour = self.stats["vigour"]
        self.current_clarity = self.stats["clarity"] 
        self.current_spirit = self.stats["spirit"]
        self.current_guard = self.stats["guard"]
        self.status = "active"  # active, routed, wiped_out, broken
        
        # Equipment and special abilities
        self.weapons = self.stats["weapons"]
        self.armor = self.stats["armor"]
        self.special_abilities = self.stats.get("special_abilities", [])
    
    def _get_warband_stats(self, warband_type: WarbandType) -> Dict:
        """Get official stats for warband types"""
        warband_stats = {
            WarbandType.MILITIA: {
                "vigour": 10,
                "clarity": 10,
                "spirit": 7,
                "guard": 3,
                "weapons": ["Crude polearm (d8 long)"],
                "armor": 0,
                "description": "Local militia with basic training"
            },
            WarbandType.SKIRMISHERS: {
                "vigour": 10,
                "clarity": 13,
                "spirit": 10,
                "guard": 2,
                "weapons": ["Shortbow (d6 long)"],
                "armor": 0,
                "description": "Mobile archers and light troops"
            },
            WarbandType.MERCENARIES: {
                "vigour": 13,
                "clarity": 10,
                "spirit": 10,
                "guard": 4,
                "weapons": ["Spear (d8 hefty)", "Shield (d4)"],
                "armor": 3,  # mail, helm, shield
                "description": "Professional soldiers for hire"
            },
            WarbandType.RIDERS: {
                "vigour": 10,
                "clarity": 13,
                "spirit": 10,
                "guard": 3,
                "weapons": ["Javelins (d6)", "Handaxe (d6)", "Steed trample"],
                "armor": 0,
                "special_abilities": ["Mounted", "Mobile"],
                "description": "Mounted warriors with superior mobility"
            },
            WarbandType.KNIGHTS: {
                "vigour": 13,
                "clarity": 10,
                "spirit": 13,
                "guard": 5,
                "weapons": ["Mace (d8 hefty)", "Shield (d4)", "Charger (d8 trample)"],
                "armor": 3,  # mail, helm, shield
                "special_abilities": ["Mounted", "Elite", "All Feats"],
                "description": "Elite heavy cavalry led by Knights"
            }
        }
        
        return warband_stats[warband_type]
    
    def is_active(self) -> bool:
        """Check if warband is still active in combat"""
        return self.status == "active"
    
    def take_damage(self, damage: int) -> str:
        """Apply damage to the warband, following warfare rules"""
        result_message = ""
        
        # Damage goes to Guard first
        if self.current_guard > 0:
            guard_damage = min(damage, self.current_guard)
            self.current_guard -= guard_damage
            damage -= guard_damage
            result_message += f"Guard reduced by {guard_damage} to {self.current_guard}. "
        
        # Remaining damage goes to Vigour
        if damage > 0:
            self.current_vigour -= damage
            result_message += f"Vigour reduced by {damage} to {self.current_vigour}. "
            
            # Check for special conditions
            if self.current_vigour <= 0:
                self.status = "wiped_out"
                result_message += "Warband is WIPED OUT entirely!"
            elif self.current_vigour <= self.stats["vigour"] // 2:
                self.status = "routed"
                result_message += "Warband is ROUTED from battle!"
        
        return result_message
    
    def check_morale(self) -> bool:
        """Check if warband maintains morale (SPI > 0)"""
        if self.current_spirit <= 0:
            self.status = "broken"
            return False
        return True
    
    def attack_individual(self) -> Dict:
        """Generate attack against individual target"""
        # Warband attacks against individuals get +d12 and cause Blast Damage
        base_weapon = self.weapons[0] if self.weapons else "d6"
        
        return {
            "attack_dice": [base_weapon, "d12"],  # +d12 for warband attack
            "blast": True,  # Causes blast damage
            "armor_value": self.armor
        }
    
    def recruit_cost(self) -> Dict:
        """Get recruitment requirements for this warband type"""
        recruitment_costs = {
            WarbandType.MILITIA: {
                "source": "loyal Vassals",
                "requirements": ["Basic needs met", "Local loyalty"],
                "cost": "Common trade goods"
            },
            WarbandType.SKIRMISHERS: {
                "source": "experienced hunters",
                "requirements": ["Basic needs met", "Ranged weapon supplies"],
                "cost": "Uncommon trade goods"
            },
            WarbandType.MERCENARIES: {
                "source": "professional soldiers",
                "requirements": ["Agreed price", "Good equipment", "Regular pay"],
                "cost": "Rare trade goods"
            },
            WarbandType.RIDERS: {
                "source": "mounted warriors",
                "requirements": ["Steeds", "Basic needs met", "Open terrain access"],
                "cost": "Rare trade goods + steeds"
            },
            WarbandType.KNIGHTS: {
                "source": "Knights that share a cause",
                "requirements": ["Shared cause", "Honor", "Glory opportunity"],
                "cost": "Service and loyalty"
            }
        }
        
        return recruitment_costs[self.type]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.type.value,
            "stats": self.stats,
            "current_state": {
                "vigour": self.current_vigour,
                "clarity": self.current_clarity,
                "spirit": self.current_spirit,
                "guard": self.current_guard
            },
            "status": self.status,
            "weapons": self.weapons,
            "armor": self.armor,
            "special_abilities": self.special_abilities
        }

class Structure:
    """Represents structures, ships, and fortifications in warfare"""
    
    def __init__(self, structure_type: StructureType, name: str = ""):
        self.type = structure_type
        self.name = name or f"{structure_type.value.replace('_', ' ').title()}"
        
        # Set stats based on type
        self.stats = self._get_structure_stats(structure_type)
        self.current_guard = self.stats["guard"]
        self.armor = self.stats["armor"]
        self.capacity = self.stats.get("capacity", 0)
        self.is_destroyed = False
    
    def _get_structure_stats(self, structure_type: StructureType) -> Dict:
        """Get official stats for structure types"""
        structure_stats = {
            StructureType.GATE: {
                "guard": 5,
                "armor": 2,
                "description": "Fortified entrance to a stronghold"
            },
            StructureType.RAMPART: {
                "guard": 10,
                "armor": 2,
                "description": "Defensive earthwork barrier"
            },
            StructureType.CASTLE_WALL: {
                "guard": 10,
                "armor": 3,
                "description": "Thick stone fortification",
                "special": "Cannot be breached by conventional means"
            },
            StructureType.ROWBOAT: {
                "guard": 4,
                "armor": 0,
                "capacity": 6,
                "description": "Small vessel for river or coastal travel"
            },
            StructureType.LONGSHIP: {
                "guard": 7,
                "armor": 1,
                "capacity": 24,  # Carries a Warband
                "description": "Swift raiding vessel"
            },
            StructureType.WARSHIP: {
                "guard": 10,
                "armor": 2,
                "capacity": 48,  # Carries 2 Warbands
                "description": "Large military vessel"
            },
            StructureType.SIEGE_TOWER: {
                "guard": 7,
                "armor": 2,
                "description": "Mobile siege platform"
            }
        }
        
        return structure_stats[structure_type]
    
    def take_damage(self, damage: int) -> str:
        """Apply damage to structure"""
        effective_damage = max(0, damage - self.armor)
        self.current_guard -= effective_damage
        
        if self.current_guard <= 0:
            self.is_destroyed = True
            return f"{self.name} is DESTROYED!"
        
        return f"{self.name} takes {effective_damage} damage, Guard now {self.current_guard}"
    
    def repair(self) -> str:
        """Repair structure (takes a day)"""
        if not self.is_destroyed:
            self.current_guard = self.stats["guard"]
            return f"{self.name} repaired to full Guard ({self.current_guard})"
        return f"{self.name} is destroyed and cannot be repaired"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.type.value,
            "stats": self.stats,
            "current_guard": self.current_guard,
            "armor": self.armor,
            "capacity": self.capacity,
            "is_destroyed": self.is_destroyed
        }

class Artillery:
    """Represents siege equipment and artillery"""
    
    def __init__(self, artillery_type: ArtilleryType, name: str = ""):
        self.type = artillery_type
        self.name = name or f"{artillery_type.value.replace('_', ' ').title()}"
        
        # Set stats based on type
        self.stats = self._get_artillery_stats(artillery_type)
        self.damage = self.stats["damage"]
        self.properties = self.stats.get("properties", [])
    
    def _get_artillery_stats(self, artillery_type: ArtilleryType) -> Dict:
        """Get official stats for artillery types"""
        artillery_stats = {
            ArtilleryType.BATTERING_RAM: {
                "damage": "d12",
                "description": "Heavy ram for breaking gates",
                "properties": ["Anti-structure"]
            },
            ArtilleryType.STONE_THROWER: {
                "damage": "d12",
                "description": "Catapult launching heavy stones",
                "properties": ["Blast"]
            },
            ArtilleryType.BOLT_LAUNCHER: {
                "damage": "2d12",
                "description": "Giant crossbow for precise shots",
                "properties": ["Long range", "Penetrating"]
            },
            ArtilleryType.TREBUCHET: {
                "damage": "3d12",
                "description": "Massive counterweight siege engine",
                "properties": ["Blast", "Immobile", "Long range"]
            }
        }
        
        return artillery_stats[artillery_type]
    
    def fire(self, target: str) -> Dict:
        """Fire artillery at target"""
        return {
            "damage": self.damage,
            "properties": self.properties,
            "target": target,
            "description": f"{self.name} fires at {target}"
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.type.value,
            "damage": self.damage,
            "properties": self.properties,
            "description": self.stats["description"]
        }

class WarfareManager:
    """Manages large-scale warfare scenarios"""
    
    def __init__(self):
        self.warbands = []
        self.structures = []
        self.artillery = []
        self.battle_log = []
    
    def add_warband(self, warband_type: WarbandType, name: str = "", allegiance: str = "neutral") -> Warband:
        """Add a warband to the battle"""
        warband = Warband(warband_type, name)
        warband.allegiance = allegiance
        self.warbands.append(warband)
        
        debug(f"Added {warband.name} ({allegiance}) to battle", category="warfare")
        return warband
    
    def add_structure(self, structure_type: StructureType, name: str = "") -> Structure:
        """Add a structure to the battlefield"""
        structure = Structure(structure_type, name)
        self.structures.append(structure)
        
        debug(f"Added {structure.name} to battlefield", category="warfare")
        return structure
    
    def add_artillery(self, artillery_type: ArtilleryType, name: str = "") -> Artillery:
        """Add artillery to the battle"""
        artillery = Artillery(artillery_type, name)
        self.artillery.append(artillery)
        
        debug(f"Added {artillery.name} to battle", category="warfare")
        return artillery
    
    def resolve_warband_attack(self, attacker: Warband, target) -> str:
        """Resolve an attack between warbands or warband vs individual"""
        if isinstance(target, Warband):
            return self._warband_vs_warband(attacker, target)
        else:
            return self._warband_vs_individual(attacker, target)
    
    def _warband_vs_warband(self, attacker: Warband, defender: Warband) -> str:
        """Resolve combat between two warbands"""
        result = f"{attacker.name} attacks {defender.name}:\n"
        
        # Both warbands attack simultaneously
        # Use their primary weapon damage
        attacker_damage = self._roll_damage(attacker.weapons[0] if attacker.weapons else "d6")
        defender_damage = self._roll_damage(defender.weapons[0] if defender.weapons else "d6")
        
        # Apply damage
        attacker_result = attacker.take_damage(defender_damage)
        defender_result = defender.take_damage(attacker_damage)
        
        result += f"- {defender.name}: {defender_result}\n"
        result += f"- {attacker.name}: {attacker_result}\n"
        
        self.battle_log.append(result)
        return result
    
    def _warband_vs_individual(self, attacker: Warband, target_name: str) -> str:
        """Resolve warband attack against individual"""
        attack_data = attacker.attack_individual()
        
        result = f"{attacker.name} attacks {target_name}:\n"
        result += f"- Attack: {' + '.join(attack_data['attack_dice'])} (Blast damage)\n"
        result += f"- Warband Armor: {attack_data['armor_value']}\n"
        
        if attack_data["blast"]:
            result += "- Blast effect: Hits all individuals in area\n"
        
        self.battle_log.append(result)
        return result
    
    def _roll_damage(self, damage_string: str) -> int:
        """Roll damage from damage string (e.g., 'd8', '2d6')"""
        # Simplified damage rolling - in practice would parse dice notation
        if "d12" in damage_string:
            return random.randint(1, 12)
        elif "d8" in damage_string:
            return random.randint(1, 8)
        elif "d6" in damage_string:
            return random.randint(1, 6)
        elif "d4" in damage_string:
            return random.randint(1, 4)
        else:
            return random.randint(1, 6)  # Default
    
    def check_battle_end(self) -> Tuple[bool, str]:
        """Check if the battle has ended"""
        active_allegiances = set()
        
        for warband in self.warbands:
            if warband.is_active():
                active_allegiances.add(getattr(warband, 'allegiance', 'neutral'))
        
        if len(active_allegiances) <= 1:
            winner = list(active_allegiances)[0] if active_allegiances else "no one"
            return True, f"Battle ended - {winner} victorious!"
        
        return False, "Battle continues"
    
    def generate_battle_report(self) -> Dict:
        """Generate a complete battle report"""
        return {
            "warbands": [w.to_dict() for w in self.warbands],
            "structures": [s.to_dict() for s in self.structures],
            "artillery": [a.to_dict() for a in self.artillery],
            "battle_log": self.battle_log,
            "battle_ended": self.check_battle_end()[0],
            "result": self.check_battle_end()[1]
        }

# Convenience functions for external use
def create_warband(warband_type: str, name: str = "") -> Warband:
    """Create a warband of the specified type"""
    warband_type_enum = WarbandType(warband_type.lower())
    return Warband(warband_type_enum, name)

def create_siege_scenario(defender_type: str = "castle") -> WarfareManager:
    """Create a typical siege scenario"""
    warfare = WarfareManager()
    
    if defender_type == "castle":
        # Add defensive structures
        warfare.add_structure(StructureType.CASTLE_WALL, "Main Wall")
        warfare.add_structure(StructureType.GATE, "Castle Gate")
        
        # Add defending forces
        warfare.add_warband(WarbandType.MERCENARIES, "Castle Guard", "defender")
        warfare.add_warband(WarbandType.MILITIA, "Local Militia", "defender")
        
        # Add attacking forces
        warfare.add_warband(WarbandType.KNIGHTS, "Attacking Knights", "attacker")
        warfare.add_warband(WarbandType.MERCENARIES, "Siege Force", "attacker")
        
        # Add siege equipment
        warfare.add_artillery(ArtilleryType.TREBUCHET, "Great Engine")
        warfare.add_artillery(ArtilleryType.BATTERING_RAM, "Iron Fist")
    
    return warfare

if __name__ == "__main__":
    # Test the warfare system
    warfare = create_siege_scenario("castle")
    report = warfare.generate_battle_report()
    print(json.dumps(report, indent=2))