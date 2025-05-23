import json
import shutil
import os
from campaign_path_manager import CampaignPathManager

# Define the file paths
party_tracker_file = "party_tracker.json"

# Initialize path manager
path_manager = CampaignPathManager()

# Define all area IDs for Keep of Doom campaign
area_ids = ["HH001", "G001", "SK001", "TBM001", "TCD001"]

# Campaign-specific files for Keep of Doom - we'll focus on HH001 for backup/restore
original_locations_file = path_manager.get_area_path("HH001")
backup_locations_file = f"{path_manager.campaign_dir}/HH001_BU.json"
original_plot_file = path_manager.get_plot_path("HH001")
backup_plot_file = f"{path_manager.campaign_dir}/plot_HH001_BU.json"

# Function to restore from backup
def restore_from_backup(original_file, backup_file):
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, original_file)
        print(f"Restored {original_file} from {backup_file}")
    else:
        print(f"Backup file {backup_file} not found. No changes made to {original_file}.")

# Function to clean encounter data from location files
def clean_encounter_data_from_areas():
    """Remove generated encounter entries and adventure summaries from all area files"""
    for area_id in area_ids:
        area_file = path_manager.get_area_path(area_id)
        if os.path.exists(area_file):
            try:
                with open(area_file, 'r', encoding='utf-8') as f:
                    area_data = json.load(f)
                
                # Clean each location in the area
                if 'locations' in area_data:
                    for location in area_data['locations']:
                        # Clear encounters array - these are generated during gameplay
                        if 'encounters' in location:
                            location['encounters'] = []
                        
                        # Clear adventure summary - this is also generated during gameplay
                        if 'adventureSummary' in location:
                            location['adventureSummary'] = ""
                        
                        # Optional: Reset description if it was modified during gameplay
                        # (Only uncomment if you want to reset descriptions to original state)
                        # if 'originalDescription' in location:
                        #     location['description'] = location['originalDescription']
                
                # Save the cleaned area file
                with open(area_file, 'w', encoding='utf-8') as f:
                    json.dump(area_data, f, indent=2, ensure_ascii=False)
                
                print(f"Cleaned encounter data from {area_file}")
                
            except Exception as e:
                print(f"Error cleaning encounter data from {area_file}: {str(e)}")
        else:
            print(f"Area file {area_file} not found")

# Create backup files if they don't exist
if not os.path.exists(backup_locations_file) and os.path.exists(original_locations_file):
    shutil.copy2(original_locations_file, backup_locations_file)
    print(f"Created backup: {backup_locations_file}")

if not os.path.exists(backup_plot_file) and os.path.exists(original_plot_file):
    shutil.copy2(original_plot_file, backup_plot_file)
    print(f"Created backup: {backup_plot_file}")

# Only restore from backup if backup files exist
if os.path.exists(backup_locations_file):
    restore_from_backup(original_locations_file, backup_locations_file)
else:
    print(f"No backup found for locations file. Using existing {original_locations_file}")

if os.path.exists(backup_plot_file):
    restore_from_backup(original_plot_file, backup_plot_file)
else:
    print(f"No backup found for plot file. Using existing {original_plot_file}")

# Clean encounter data from all area files
print("Cleaning encounter data from all area files...")
clean_encounter_data_from_areas()

# Delete combat_conversation_history.json and conversation_history.json
files_to_delete = ['combat_conversation_history.json', 'conversation_history.json', 'chat_history.json', 
                   'transition_debug.log', 'adv_summary_debug.log']
for file in files_to_delete:
    if os.path.exists(file):
        os.remove(file)
        print(f"Deleted {file}")
    else:
        print(f"{file} not found")

# Update party tracker
if os.path.exists(party_tracker_file):
    with open(party_tracker_file, 'r', encoding='utf-8') as f:
        party_tracker = json.load(f)

    # Remove encounter ID and update current location in party tracker
    party_tracker['worldConditions']['activeCombatEncounter'] = ""
    party_tracker['worldConditions']['currentLocation'] = "Harrow's Hollow General Store"
    party_tracker['worldConditions']['currentLocationId'] = "R01"
    party_tracker['worldConditions']['currentArea'] = "Harrow's Hollow"
    party_tracker['worldConditions']['currentAreaId'] = "HH001"
    party_tracker['worldConditions']['activeEncounter'] = ""
    
    # Reset time to morning
    party_tracker['worldConditions']['day'] = 1
    party_tracker['worldConditions']['time'] = "08:00:00"
    party_tracker['worldConditions']['dayNightCycle'] = "Morning"
    party_tracker['worldConditions']['weather'] = "Overcast"
    party_tracker['worldConditions']['weatherConditions'] = "Overcast with morning mist"

    # Reset quests to initial Keep of Doom state
    party_tracker['activeQuests'] = [
        {
            "id": "PP001",
            "title": "Shadows Over Harrow's Hollow",
            "description": "The party arrives in Harrow's Hollow, a small, anxious village gripped by fear. Elder Mirna Harrow asks the characters to investigate recent disappearances, including that of Scout Elen. Tensions run high as rumors of curses, spirits, and the haunted Keep of Doom swirl among the villagers. Players must gather information, win trust, and follow leads to piece together the mystery.",
            "status": "in progress"
        },
        {
            "id": "SQ001",
            "title": "Superstition and Shadows",
            "description": "Old Tommen believes a wandering spirit haunts the village. If the party investigates, they may encounter the Wandering Shade—a restless ghost whose cryptic words offer hints about the keep and the missing villagers.",
            "status": "not started"
        },
        {
            "id": "SQ002",
            "title": "Trouble at the Hearth",
            "description": "Cira the Innkeeper's cellar is plagued by minor poltergeist activity. Calming the spirit earns Cira's gratitude and a helpful clue about Scout Elen's last known movements.",
            "status": "not started"
        }
    ]

    # Ensure we're using the Keep of Doom campaign
    party_tracker['campaign'] = "Keep_of_Doom"
    party_tracker['partyMembers'] = ["norn"]
    party_tracker['partyNPCs'] = []

    # Save the updated party tracker
    with open(party_tracker_file, 'w', encoding='utf-8') as f:
        json.dump(party_tracker, f, indent=2, ensure_ascii=False)
    
    print("Party tracker updated for Keep of Doom campaign.")
else:
    print(f"{party_tracker_file} not found. No changes made to party tracker.")

# Reset any campaign-specific debug files
debug_files = ['combat_validation_log.json', 'debug_ai_response.json', 'dialogue_summary.json']
for file in debug_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"Deleted {file}")

# Reset character file to starting state
character_file = path_manager.get_player_path("norn")
if os.path.exists(character_file):
    with open(character_file, 'r', encoding='utf-8') as f:
        norn_data = json.load(f)
    
    # Reset HP to max
    norn_data['hitPoints'] = norn_data['maxHitPoints']
    
    # Reset any temporary conditions
    if 'temporaryHitPoints' in norn_data:
        norn_data['temporaryHitPoints'] = 0
    
    # Reset status and conditions
    norn_data['status'] = 'alive'
    norn_data['condition'] = 'none'
    norn_data['condition_affected'] = []
    
    # Clear gameplay-acquired equipment (items picked up during play)
    norn_data['equipment'] = []
    
    # Save the updated character
    with open(character_file, 'w', encoding='utf-8') as f:
        json.dump(norn_data, f, indent=2, ensure_ascii=False)
    
    print("Reset Norn's character to full health and cleared equipment.")

print("Reset complete. Keep of Doom campaign ready to start fresh!")