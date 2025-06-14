import json
# ============================================================================
# CAMPAIGN_PATH_MANAGER.PY - FILE SYSTEM ABSTRACTION LAYER
# ============================================================================
# 
# ARCHITECTURE ROLE: Data Management Layer - File System Abstraction
# 
# This module provides a unified interface for all file operations across the
# 5e system, implementing our "Campaign-Centric Organization" principle.
# It abstracts file path resolution and handles legacy migration seamlessly.
# 
# KEY RESPONSIBILITIES:
# - Centralized file path resolution for all campaign resources
# - Handle legacy vs. unified file structure migration
# - Ensure consistent naming conventions and directory organization
# - Provide atomic file operations with backup and recovery
# - Cross-platform compatibility for file system operations
# 
# FILE ORGANIZATION STRATEGY:
# campaigns/[campaign_name]/
# ├── areas/              # Location files (HH001.json, G001.json)
# ├── characters/         # Unified player/NPC storage
# ├── monsters/           # Campaign-specific creatures
# ├── encounters/         # Combat encounters
# └── meta files...       # Campaign plot, party tracker, etc.
# 
# ARCHITECTURAL INTEGRATION:
# - Used by all file operations throughout the system
# - Enables the Factory Pattern for content builders
# - Supports the "Data Integrity Above All" principle
# - Provides backward compatibility for legacy campaigns
# 
# DESIGN PATTERNS:
# - Factory Pattern: Creates proper file paths based on content type
# - Strategy Pattern: Different path strategies for legacy vs. unified structure
# - Singleton-like behavior: Shared path resolution across system
# 
# This module ensures our file system organization remains consistent
# and maintainable while supporting seamless legacy migration.
# ============================================================================

import os

class CampaignPathManager:
    """Manages file paths for campaign-specific resources"""
    
    def __init__(self, campaign_name=None):
        self.campaign_name = campaign_name or self._get_active_campaign()
        self.campaign_dir = f"campaigns/{self.campaign_name}"
        
    def _get_active_campaign(self):
        """Read the active campaign from party_tracker.json"""
        try:
            with open("party_tracker.json", 'r', encoding='utf-8') as file:
                data = json.load(file)
                campaign = data.get("campaign", "Keep_of_Doom")
                # Use logger if available, otherwise print
                try:
                    from enhanced_logger import debug
                    debug(f"CampaignPathManager loaded campaign '{campaign}' from party_tracker.json", category="campaign_loading")
                except:
                    print(f"DEBUG: CampaignPathManager loaded campaign '{campaign}' from party_tracker.json")
                return campaign
        except Exception as e:
            try:
                from enhanced_logger import error
                error(f"CampaignPathManager could not load party_tracker.json", exception=e)
            except:
                print(f"DEBUG: CampaignPathManager could not load party_tracker.json: {e}")
                print(f"DEBUG: Using default campaign 'Keep_of_Doom'")
            return "Keep_of_Doom"  # Default fallback
    
    def format_filename(self, name):
        """Convert a name to a valid filename format"""
        return name.lower().replace(' ', '_')
    
    # Monster and NPC paths
    def get_monster_path(self, monster_name):
        """Get the path to a monster file"""
        return f"{self.campaign_dir}/monsters/{self.format_filename(monster_name)}.json"
    
    def get_npc_path(self, npc_name):
        """Get the path to an NPC file (legacy support)"""
        return f"{self.campaign_dir}/npcs/{self.format_filename(npc_name)}.json"
    
    # Area-related paths
    def get_area_path(self, area_id):
        """Get the path to an area file"""
        return f"{self.campaign_dir}/{area_id}.json"
    
    def get_plot_path(self, area_id=None):
        """Get the path to the campaign plot file (no longer area-specific)"""
        return f"{self.campaign_dir}/campaign_plot.json"
    
    def get_map_path(self, area_id):
        """Get the path to a map file"""
        return f"{self.campaign_dir}/map_{area_id}.json"
    
    # Campaign-specific paths
    def get_campaign_file_path(self):
        """Get the path to the main campaign file"""
        return f"{self.campaign_dir}/{self.campaign_name}_campaign.json"
    
    # Player character paths
    def get_player_path(self, player_name):
        """Get the path to a player character file (legacy support)"""
        return f"{self.campaign_dir}/{self.format_filename(player_name)}.json"
    
    # Unified character paths with fallback support
    def get_character_path(self, character_name):
        """
        Get the path to a character file - tries unified structure first, 
        falls back to legacy structure if needed
        """
        # First try unified structure
        unified_path = f"{self.campaign_dir}/characters/{self.format_filename(character_name)}.json"
        if os.path.exists(unified_path):
            return unified_path
        
        # Fall back to legacy structure based on party_tracker.json
        character_role = self._determine_character_role(character_name)
        if character_role == 'player':
            return self.get_player_path(character_name)
        else:
            return self.get_npc_path(character_name)
    
    def _determine_character_role(self, character_name):
        """Determine character role from party_tracker.json"""
        try:
            with open("party_tracker.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                party_members = data.get("partyMembers", [])
                party_npcs = data.get("partyNPCs", [])
                
                if character_name.lower() in [name.lower() for name in party_members]:
                    return 'player'
                elif character_name.lower() in [name.lower() for name in party_npcs]:
                    return 'npc'
                else:
                    # Default to NPC if not in party members
                    return 'npc'
        except Exception:
            # If we can't read party_tracker, default to NPC
            return 'npc'
    
    def get_character_unified_path(self, character_name):
        """Get the unified path (whether file exists or not)"""
        return f"{self.campaign_dir}/characters/{self.format_filename(character_name)}.json"
    
    def get_character_legacy_path(self, character_name, character_role=None):
        """Get the legacy path for a character based on role"""
        if character_role is None:
            character_role = self._determine_character_role(character_name)
            
        if character_role == 'player':
            return self.get_player_path(character_name)
        else:
            return self.get_npc_path(character_name)
    
    # Encounter paths
    def get_encounter_path(self, location_id, encounter_num):
        """Get the path to an encounter file"""
        return f"encounter_{location_id}-E{encounter_num}.json"
    
    # Random encounter paths
    def get_random_encounter_path(self):
        """Get the path to the random encounter file"""
        return "random_encounter.json"
    
    # Directory creation methods
    def ensure_campaign_dirs(self):
        """Ensure all necessary campaign directories exist"""
        os.makedirs(f"{self.campaign_dir}/monsters", exist_ok=True)
        os.makedirs(f"{self.campaign_dir}/npcs", exist_ok=True)
        os.makedirs(f"{self.campaign_dir}/characters", exist_ok=True)  # Unified character storage
    
    # Check if a file exists
    def file_exists(self, path):
        """Check if a file exists"""
        return os.path.exists(path)
    
    # Get list of files in a directory
    def list_monsters(self):
        """List all monster files in the campaign"""
        monster_dir = f"{self.campaign_dir}/monsters"
        if os.path.exists(monster_dir):
            return [f for f in os.listdir(monster_dir) if f.endswith('.json')]
        return []
    
    def list_npcs(self):
        """List all NPC files in the campaign"""
        npc_dir = f"{self.campaign_dir}/npcs"
        if os.path.exists(npc_dir):
            return [f for f in os.listdir(npc_dir) if f.endswith('.json')]
        return []