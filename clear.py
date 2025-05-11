import json
import shutil
import os

# Define the file paths
original_locations_file = "EM001.json"
backup_locations_file = "EM001_BU.json"
original_plot_file = "plot_EM001.json"
backup_plot_file = "plot_EM001_BU.json"
party_tracker_file = "party_tracker.json"

# Function to restore from backup
def restore_from_backup(original_file, backup_file):
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, original_file)
        print(f"Restored {original_file} from {backup_file}")
    else:
        print(f"Backup file {backup_file} not found. No changes made to {original_file}.")

# Restore locations file
restore_from_backup(original_locations_file, backup_locations_file)

# Restore plot file
restore_from_backup(original_plot_file, backup_plot_file)

# Delete combat_conversation_history.json and conversation_history.json
files_to_delete = ['combat_conversation_history.json', 'conversation_history.json']
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
    party_tracker['worldConditions']['currentLocation'] = "Hidden Entrance to Dwarven Complex"
    party_tracker['worldConditions']['currentLocationId'] = "R14"
    party_tracker['worldConditions']['currentArea'] = "Old Mines of Ember Hollow"
    party_tracker['worldConditions']['currentAreaId'] = "EM001"  # This is the correct area ID

    # Reset quests to blank
    party_tracker['activeQuests'] = []

    # Save the updated party tracker
    with open(party_tracker_file, 'w', encoding='utf-8') as f:
        json.dump(party_tracker, f, indent=2, ensure_ascii=False)
    
    print("Party tracker updated with new location, removed encounter ID, and reset quests to blank.")
else:
    print(f"{party_tracker_file} not found. No changes made to party tracker.")

print("Reset complete. Files restored from backups, conversation history files deleted, and party tracker updated.")