#!/usr/bin/env python3
"""
Migration script to convert character and NPC data to PHB-compliant structure.

This script will:
1. Remove deprecated 'features' and 'specialAbilities' arrays
2. Categorize abilities into proper PHB-compliant arrays
3. Add missing arrays with empty values
4. Preserve all data by moving items to appropriate categories
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any
from file_operations import safe_write_json, safe_read_json

# Create backup directory
BACKUP_DIR = f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def create_backup_dir():
    """Create backup directory for original files"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    print(f"Created backup directory: {BACKUP_DIR}")

def backup_file(filepath: str):
    """Create backup of file before migration"""
    if os.path.exists(filepath):
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(filepath))
        shutil.copy2(filepath, backup_path)
        print(f"Backed up: {filepath} -> {backup_path}")

def is_class_feature(feature_name: str) -> bool:
    """Determine if a feature is a class feature based on common patterns"""
    class_features = [
        "fighting style", "second wind", "action surge", "extra attack",
        "indomitable", "martial archetype", "champion", "improved critical",
        "remarkable athlete", "additional fighting style", "superior critical",
        "survivor", "rage", "unarmored defense", "reckless attack", "danger sense",
        "primal path", "brutal critical", "relentless rage", "persistent rage",
        "bardic inspiration", "jack of all trades", "song of rest", "expertise",
        "font of inspiration", "countercharm", "magical secrets", "superior inspiration",
        "sneak attack", "thieves' cant", "cunning action", "roguish archetype",
        "uncanny dodge", "evasion", "reliable talent", "blindsense", "slippery mind",
        "stroke of luck", "divine domain", "channel divinity", "divine strike",
        "divine intervention", "spellcasting", "arcane recovery", "arcane tradition",
        "spell mastery", "signature spells", "sorcerous origin", "font of magic",
        "metamagic", "sorcerous restoration", "eldritch invocations", "pact magic",
        "pact boon", "mystic arcanum", "eldritch master", "favored enemy",
        "natural explorer", "primeval awareness", "land's stride", "hide in plain sight",
        "vanish", "feral senses", "foe slayer", "divine sense", "lay on hands",
        "divine health", "sacred oath", "divine smite", "aura of protection",
        "aura of courage", "cleansing touch", "ki", "unarmored movement",
        "martial arts", "deflect missiles", "slow fall", "stunning strike",
        "ki-empowered strikes", "wholeness of body", "tranquility", "monastic tradition",
        "wild shape", "druidic", "timeless body", "beast spells", "archdruid"
    ]
    
    feature_lower = feature_name.lower()
    return any(cf in feature_lower for cf in class_features)

def is_temporary_effect(feature_name: str) -> bool:
    """Determine if a feature is a temporary effect"""
    temp_keywords = [
        "ritual", "blessing", "curse", "ward", "completed", "performing",
        "hours", "minutes", "days", "temporary", "until", "duration",
        "fortitude", "advantage on", "disadvantage on", "for 24 hours"
    ]
    
    feature_lower = feature_name.lower()
    return any(tk in feature_lower for tk in temp_keywords)

def categorize_feature(feature: Any, character_data: Dict[str, Any]) -> str:
    """Categorize a feature into the appropriate array"""
    # Convert to dict if string
    if isinstance(feature, str):
        feature_dict = {"name": feature, "description": feature}
    else:
        feature_dict = feature
    
    feature_name = feature_dict.get("name", "")
    
    # Check if it's a temporary effect
    if is_temporary_effect(feature_name):
        return "temporaryEffects"
    
    # Check if it's a class feature
    if is_class_feature(feature_name):
        return "classFeatures"
    
    # Default to temporaryEffects for uncategorized abilities
    return "temporaryEffects"

def get_background_feature(background: str) -> Dict[str, str]:
    """Get the standard background feature for a given background"""
    background_features = {
        "soldier": {
            "name": "Military Rank",
            "description": "Soldiers loyal to your former military organization still recognize your authority and military rank. They will defer to you if they are of a lower rank, and you can invoke your rank to exert influence over other soldiers and requisition simple equipment or horses for temporary use.",
            "source": "Soldier background"
        },
        "acolyte": {
            "name": "Shelter of the Faithful",
            "description": "As an acolyte, you command the respect of those who share your faith. You can perform religious ceremonies and have access to holy sites.",
            "source": "Acolyte background"
        },
        "criminal": {
            "name": "Criminal Contact",
            "description": "You have a reliable and trustworthy contact who acts as your liaison to a network of other criminals.",
            "source": "Criminal background"
        },
        "folk hero": {
            "name": "Rustic Hospitality",
            "description": "Since you come from the ranks of the common folk, you fit in among them with ease. Commoners will shield you from the law or anyone searching for you.",
            "source": "Folk Hero background"
        },
        "noble": {
            "name": "Position of Privilege",
            "description": "Thanks to your noble birth, people are inclined to think the best of you. You are welcome in high society.",
            "source": "Noble background"
        },
        "sage": {
            "name": "Researcher",
            "description": "When you attempt to learn or recall a piece of lore, if you don't know it, you often know where and from whom you can obtain it.",
            "source": "Sage background"
        },
        "hermit": {
            "name": "Discovery",
            "description": "The quiet seclusion of your extended hermitage gave you access to a unique and powerful discovery.",
            "source": "Hermit background"
        },
        "entertainer": {
            "name": "By Popular Demand",
            "description": "You can always find a place to perform. You receive free lodging and food of a modest or comfortable standard as long as you perform each night.",
            "source": "Entertainer background"
        },
        "guild artisan": {
            "name": "Guild Membership",
            "description": "As a member of your guild, you can rely on certain benefits that membership provides.",
            "source": "Guild Artisan background"
        },
        "outlander": {
            "name": "Wanderer",
            "description": "You have an excellent memory for maps and geography. You can find food and fresh water for yourself and up to five other people each day.",
            "source": "Outlander background"
        }
    }
    
    # Return the feature if found, otherwise a generic one
    bg_lower = background.lower()
    return background_features.get(bg_lower, {
        "name": f"{background} Feature",
        "description": f"A special feature from your {background} background.",
        "source": f"{background} background"
    })

def get_racial_traits(race: str, character_class: str = None) -> List[Dict[str, str]]:
    """Get standard racial traits for a given race"""
    racial_traits = {
        "human": [
            {
                "name": "Ability Score Increase",
                "description": "Your ability scores each increase by 1.",
                "source": "Human"
            },
            {
                "name": "Languages",
                "description": "You can speak, read, and write Common and one extra language of your choice.",
                "source": "Human"
            }
        ],
        "elf": [
            {
                "name": "Ability Score Increase",
                "description": "Your Dexterity score increases by 2.",
                "source": "Elf"
            },
            {
                "name": "Darkvision",
                "description": "You can see in dim light within 60 feet as if it were bright light.",
                "source": "Elf"
            },
            {
                "name": "Keen Senses",
                "description": "You have proficiency in the Perception skill.",
                "source": "Elf"
            },
            {
                "name": "Fey Ancestry",
                "description": "You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
                "source": "Elf"
            },
            {
                "name": "Trance",
                "description": "You don't need to sleep. Instead, you meditate deeply for 4 hours a day.",
                "source": "Elf"
            }
        ],
        "dwarf": [
            {
                "name": "Ability Score Increase",
                "description": "Your Constitution score increases by 2.",
                "source": "Dwarf"
            },
            {
                "name": "Darkvision",
                "description": "You can see in dim light within 60 feet as if it were bright light.",
                "source": "Dwarf"
            },
            {
                "name": "Dwarven Resilience",
                "description": "You have advantage on saving throws against poison, and resistance against poison damage.",
                "source": "Dwarf"
            },
            {
                "name": "Stonecunning",
                "description": "You have proficiency on History checks related to stonework.",
                "source": "Dwarf"
            }
        ],
        "halfling": [
            {
                "name": "Ability Score Increase",
                "description": "Your Dexterity score increases by 2.",
                "source": "Halfling"
            },
            {
                "name": "Lucky",
                "description": "When you roll a 1 on an attack roll, ability check, or saving throw, you can reroll the die.",
                "source": "Halfling"
            },
            {
                "name": "Brave",
                "description": "You have advantage on saving throws against being frightened.",
                "source": "Halfling"
            },
            {
                "name": "Halfling Nimbleness",
                "description": "You can move through the space of any creature that is of a size larger than yours.",
                "source": "Halfling"
            }
        ]
    }
    
    # Get traits for the race, or empty list if not found
    race_lower = race.lower()
    traits = []
    
    # Check for standard races
    for key, value in racial_traits.items():
        if key in race_lower:
            traits = value
            break
    
    # For variant humans, might have fewer traits
    if "variant" in race_lower and "human" in race_lower:
        traits = [
            {
                "name": "Ability Score Increase",
                "description": "Two different ability scores of your choice increase by 1.",
                "source": "Variant Human"
            },
            {
                "name": "Skills",
                "description": "You gain proficiency in one skill of your choice.",
                "source": "Variant Human"
            },
            {
                "name": "Feat",
                "description": "You gain one feat of your choice.",
                "source": "Variant Human"
            }
        ]
    
    return traits

def migrate_character_data(data: Dict[str, Any], is_npc: bool = False) -> Dict[str, Any]:
    """Migrate character or NPC data to PHB-compliant structure"""
    # Create a copy to avoid modifying original
    migrated = data.copy()
    
    # Initialize new arrays if they don't exist
    if "racialTraits" not in migrated:
        migrated["racialTraits"] = []
    if "temporaryEffects" not in migrated:
        migrated["temporaryEffects"] = []
    if "feats" not in migrated:
        migrated["feats"] = []
    if "backgroundFeature" not in migrated:
        migrated["backgroundFeature"] = {}
    
    # Ensure classFeatures exists and is properly formatted
    if "classFeatures" not in migrated:
        migrated["classFeatures"] = []
    
    # Get racial traits based on race
    if not migrated["racialTraits"] and "race" in migrated:
        migrated["racialTraits"] = get_racial_traits(
            migrated["race"], 
            migrated.get("class", "")
        )
    
    # Get background feature
    if not migrated["backgroundFeature"] and "background" in migrated:
        migrated["backgroundFeature"] = get_background_feature(migrated["background"])
    
    # Process features array if it exists
    if "features" in migrated:
        features = migrated["features"]
        for feature in features:
            # Skip if already migrated
            if isinstance(feature, str):
                feature_name = feature
            else:
                feature_name = feature.get("name", "")
            
            # Check if already exists in classFeatures
            already_exists = any(
                cf.get("name", "") == feature_name 
                for cf in migrated["classFeatures"]
            )
            
            if not already_exists:
                category = categorize_feature(feature, migrated)
                
                # Create proper object format
                if isinstance(feature, str):
                    feature_obj = {
                        "name": feature,
                        "description": feature
                    }
                else:
                    feature_obj = feature
                
                # Add source info for class features
                if category == "classFeatures" and "source" not in feature_obj:
                    feature_obj["source"] = f"{migrated.get('class', 'Unknown')} feature"
                
                # Add to appropriate array
                if category == "temporaryEffects" and "duration" not in feature_obj:
                    feature_obj["duration"] = "Unknown"
                    
                migrated[category].append(feature_obj)
        
        # Remove the deprecated features array
        del migrated["features"]
    
    # Process specialAbilities array if it exists
    if "specialAbilities" in migrated:
        for ability in migrated["specialAbilities"]:
            # Move to temporaryEffects
            temp_effect = ability.copy()
            if "duration" not in temp_effect:
                temp_effect["duration"] = "Unknown"
            if "source" not in temp_effect:
                temp_effect["source"] = "Special ability"
            migrated["temporaryEffects"].append(temp_effect)
        
        # Remove the deprecated specialAbilities array
        del migrated["specialAbilities"]
    
    # Ensure classFeatures have proper format and no duplicates
    seen_features = set()
    unique_class_features = []
    for cf in migrated["classFeatures"]:
        name = cf.get("name", "")
        if name and name not in seen_features:
            seen_features.add(name)
            # Ensure it has source
            if "source" not in cf:
                cf["source"] = f"{migrated.get('class', 'Unknown')} feature"
            unique_class_features.append(cf)
    migrated["classFeatures"] = unique_class_features
    
    # Fix negative currency values
    if "currency" in migrated:
        for coin in ["gold", "silver", "copper"]:
            if coin in migrated["currency"] and migrated["currency"][coin] < 0:
                print(f"  WARNING: {migrated['name']} has negative {coin}: {migrated['currency'][coin]}")
                migrated["currency"][coin] = 0
    
    return migrated

def migrate_file(filepath: str, is_npc: bool = False):
    """Migrate a single character or NPC file"""
    print(f"\nMigrating: {filepath}")
    
    # Load the data
    data = safe_read_json(filepath)
    if not data:
        print(f"  ERROR: Could not read {filepath}")
        return False
    
    # Backup the original
    backup_file(filepath)
    
    # Migrate the data
    migrated_data = migrate_character_data(data, is_npc)
    
    # Save the migrated data
    if safe_write_json(filepath, migrated_data):
        print(f"  SUCCESS: Migrated {filepath}")
        return True
    else:
        print(f"  ERROR: Could not save migrated data to {filepath}")
        return False

def find_character_files():
    """Find all character and NPC JSON files in modules"""
    character_files = []
    npc_files = []
    
    modules_dir = "modules"
    if not os.path.exists(modules_dir):
        return character_files, npc_files
    
    for module in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module)
        if not os.path.isdir(module_path):
            continue
        
        # Look for character files in module root
        for file in os.listdir(module_path):
            if file.endswith(".json"):
                filepath = os.path.join(module_path, file)
                data = safe_read_json(filepath)
                if data:
                    # Check if it's a player character
                    if data.get("character_type") == "player" or data.get("type") == "player":
                        character_files.append(filepath)
        
        # Look for NPCs in npcs folder
        npcs_dir = os.path.join(module_path, "npcs")
        if os.path.exists(npcs_dir):
            for file in os.listdir(npcs_dir):
                if file.endswith(".json"):
                    npc_files.append(os.path.join(npcs_dir, file))
    
    return character_files, npc_files

def main():
    """Main migration function"""
    print("=== PHB Structure Migration Script ===")
    print("This will migrate all character and NPC files to PHB-compliant structure.")
    print(f"Backups will be created in: {BACKUP_DIR}")
    
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled.")
        return
    
    # Create backup directory
    create_backup_dir()
    
    # Find all files to migrate
    print("\nSearching for character and NPC files...")
    character_files, npc_files = find_character_files()
    
    print(f"Found {len(character_files)} character files")
    print(f"Found {len(npc_files)} NPC files")
    
    # Migrate character files
    success_count = 0
    print("\n=== Migrating Character Files ===")
    for filepath in character_files:
        if migrate_file(filepath, is_npc=False):
            success_count += 1
    
    print(f"\nMigrated {success_count}/{len(character_files)} character files successfully")
    
    # Migrate NPC files
    npc_success_count = 0
    print("\n=== Migrating NPC Files ===")
    for filepath in npc_files:
        if migrate_file(filepath, is_npc=True):
            npc_success_count += 1
    
    print(f"\nMigrated {npc_success_count}/{len(npc_files)} NPC files successfully")
    
    print(f"\n=== Migration Complete ===")
    print(f"Total files migrated: {success_count + npc_success_count}")
    print(f"Backups saved in: {BACKUP_DIR}")
    print("\nIMPORTANT: Please test the migrated files before deleting backups!")

if __name__ == "__main__":
    main()