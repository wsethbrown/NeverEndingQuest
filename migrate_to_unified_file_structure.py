#!/usr/bin/env python3
"""
File System Migration Script - Character Unification
Migrates from separate player/NPC directories to unified characters directory
Respects party_tracker.json as the single source of truth
"""

import os
import shutil
import json
from campaign_path_manager import CampaignPathManager

def load_party_tracker():
    """Load party tracker to identify characters"""
    try:
        with open("party_tracker.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading party_tracker.json: {e}")
        return None

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
        return True
    else:
        print(f"Directory already exists: {directory}")
        return False

def migrate_character_files():
    """Migrate character files to unified structure based on party_tracker.json"""
    path_manager = CampaignPathManager()
    party_data = load_party_tracker()
    
    if not party_data:
        print("Cannot proceed without party_tracker.json")
        return False
    
    campaign_dir = path_manager.campaign_dir
    characters_dir = f"{campaign_dir}/characters"
    
    # Create unified characters directory
    ensure_directory_exists(characters_dir)
    
    print(f"\n=== Migrating Characters for Campaign: {party_data.get('campaign', 'Unknown')} ===")
    
    migrated_characters = []
    
    # Migrate player characters (from party_tracker.json partyMembers)
    party_members = party_data.get("partyMembers", [])
    print(f"\n--- Migrating Player Characters: {party_members} ---")
    
    for player_name in party_members:
        legacy_path = path_manager.get_player_path(player_name)
        unified_path = path_manager.get_character_unified_path(player_name)
        
        if os.path.exists(legacy_path):
            print(f"Migrating player '{player_name}': {legacy_path} -> {unified_path}")
            
            # Create backup
            backup_path = f"{legacy_path}.backup_pre_unified"
            shutil.copy2(legacy_path, backup_path)
            print(f"  Created backup: {backup_path}")
            
            # Move to unified structure
            shutil.move(legacy_path, unified_path)
            print(f"  ✅ Successfully moved to: {unified_path}")
            
            migrated_characters.append(f"{player_name} (player)")
        else:
            print(f"⚠️  Player character file not found: {legacy_path}")
    
    # Migrate NPC characters (from party_tracker.json partyNPCs)
    party_npcs = party_data.get("partyNPCs", [])
    print(f"\n--- Migrating Party NPCs: {party_npcs} ---")
    
    for npc_name in party_npcs:
        legacy_path = path_manager.get_npc_path(npc_name)
        unified_path = path_manager.get_character_unified_path(npc_name)
        
        if os.path.exists(legacy_path):
            print(f"Migrating NPC '{npc_name}': {legacy_path} -> {unified_path}")
            
            # Create backup
            backup_path = f"{legacy_path}.backup_pre_unified"
            shutil.copy2(legacy_path, backup_path)
            print(f"  Created backup: {backup_path}")
            
            # Move to unified structure
            shutil.move(legacy_path, unified_path)
            print(f"  ✅ Successfully moved to: {unified_path}")
            
            migrated_characters.append(f"{npc_name} (npc)")
        else:
            print(f"⚠️  NPC character file not found: {legacy_path}")
    
    # Check for any other NPCs in the npcs directory (not in party)
    npcs_dir = f"{campaign_dir}/npcs"
    if os.path.exists(npcs_dir):
        other_npcs = [f.replace('.json', '') for f in os.listdir(npcs_dir) if f.endswith('.json')]
        if other_npcs:
            print(f"\n--- Found Additional NPCs not in party: {other_npcs} ---")
            
            for npc_name in other_npcs:
                legacy_path = path_manager.get_npc_path(npc_name)
                unified_path = path_manager.get_character_unified_path(npc_name)
                
                print(f"Migrating additional NPC '{npc_name}': {legacy_path} -> {unified_path}")
                
                # Create backup
                backup_path = f"{legacy_path}.backup_pre_unified"
                shutil.copy2(legacy_path, backup_path)
                print(f"  Created backup: {backup_path}")
                
                # Move to unified structure
                shutil.move(legacy_path, unified_path)
                print(f"  ✅ Successfully moved to: {unified_path}")
                
                migrated_characters.append(f"{npc_name} (npc)")
        
        # Remove empty npcs directory
        if not os.listdir(npcs_dir):
            print(f"Removing empty directory: {npcs_dir}")
            os.rmdir(npcs_dir)
    
    return migrated_characters

def verify_migration():
    """Verify migration was successful and characters are accessible"""
    path_manager = CampaignPathManager()
    party_data = load_party_tracker()
    
    if not party_data:
        return False
    
    print("\n=== Verifying Migration ===")
    
    all_characters = party_data.get("partyMembers", []) + party_data.get("partyNPCs", [])
    success = True
    
    for character_name in all_characters:
        # Test that the new path manager can find the character
        character_path = path_manager.get_character_path(character_name)
        
        if os.path.exists(character_path):
            try:
                with open(character_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    character_role = data.get('character_role', 'unknown')
                    print(f"  ✅ {character_name} ({character_role}): {character_path}")
            except Exception as e:
                print(f"  ❌ {character_name}: Error reading file - {e}")
                success = False
        else:
            print(f"  ❌ {character_name}: File not found at {character_path}")
            success = False
    
    return success

def main():
    """Main migration function"""
    print("=== Character File System Unification Migration ===")
    print("Migrates characters to unified directory structure based on party_tracker.json")
    print("This respects party_tracker.json as the single source of truth.\n")
    
    # Load party tracker to show what will be migrated
    party_data = load_party_tracker()
    if not party_data:
        return
    
    print(f"Campaign: {party_data.get('campaign', 'Unknown')}")
    print(f"Party Members: {party_data.get('partyMembers', [])}")
    print(f"Party NPCs: {party_data.get('partyNPCs', [])}")
    
    # Check if migration needed
    path_manager = CampaignPathManager()
    characters_dir = f"{path_manager.campaign_dir}/characters"
    
    if os.path.exists(characters_dir) and os.listdir(characters_dir):
        print(f"\n⚠️  Characters directory already exists with files:")
        for f in os.listdir(characters_dir):
            if f.endswith('.json'):
                print(f"   - {f}")
        
        response = input("\nProceed with migration anyway? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    try:
        # Perform migration
        migrated_characters = migrate_character_files()
        
        # Verify migration
        if verify_migration():
            print(f"\n🎉 Migration completed successfully!")
            print(f"   - Migrated {len(migrated_characters)} character(s):")
            for char in migrated_characters:
                print(f"     • {char}")
            print(f"   - All files now in: {characters_dir}")
            print(f"   - Backups created for all moved files")
            print(f"   - party_tracker.json unchanged (still the source of truth)")
        else:
            print("\n❌ Migration verification failed!")
            
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        print("Check backups and manually verify file integrity.")

if __name__ == "__main__":
    main()