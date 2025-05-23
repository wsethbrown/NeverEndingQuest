import json
import os

class CampaignPathManager:
    """Manages file paths for campaign-specific resources"""
    
    def __init__(self, campaign_name=None):
        self.campaign_name = campaign_name or self._get_active_campaign()
        self.campaign_dir = f"campaigns/{self.campaign_name}"
        
    def _get_active_campaign(self):
        """Read the active campaign from party_tracker.json"""
        try:
            with open("party_tracker.json", 'r') as file:
                data = json.load(file)
                return data.get("campaign", "Echoes_of_the_Elemental_Forge")
        except:
            return "Echoes_of_the_Elemental_Forge"  # Default fallback
    
    def format_filename(self, name):
        """Convert a name to a valid filename format"""
        return name.lower().replace(' ', '_')
    
    # Monster and NPC paths
    def get_monster_path(self, monster_name):
        """Get the path to a monster file"""
        return f"{self.campaign_dir}/monsters/{self.format_filename(monster_name)}.json"
    
    def get_npc_path(self, npc_name):
        """Get the path to an NPC file"""
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
        """Get the path to a player character file"""
        return f"{self.campaign_dir}/{self.format_filename(player_name)}.json"
    
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