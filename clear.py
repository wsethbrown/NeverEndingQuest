import json
import shutil
import os
from module_path_manager import ModulePathManager

# Define the file paths
party_tracker_file = "party_tracker.json"

# Initialize path manager with current module for consistent path resolution
try:
    from encoding_utils import safe_json_load
    party_tracker = safe_json_load("party_tracker.json")
    current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
    path_manager = ModulePathManager(current_module)
except:
    path_manager = ModulePathManager()  # Fallback to reading from file

# Define all area IDs for Keep of Doom module
area_ids = ["HH001", "G001", "SK001", "TBM001", "TCD001"]

# Module-specific files for Keep of Doom
module_dir = path_manager.module_dir

# Function to restore from backup
def restore_from_backup(original_file, backup_file):
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, original_file)
        print(f"Restored {original_file} from {backup_file}")
    else:
        print(f"Backup file {backup_file} not found. No changes made to {original_file}.")


# Restore area files from backups
for area_id in area_ids:
    original_file = path_manager.get_area_path(area_id)
    backup_file = f"{module_dir}/{area_id}_BU.json"
    
    if os.path.exists(backup_file):
        restore_from_backup(original_file, backup_file)
    else:
        print(f"No backup found for {area_id}. Using existing file.")

# Restore module plot from backup
original_plot = path_manager.get_plot_path()
backup_plot = f"{module_dir}/module_plot_BU.json"

if os.path.exists(backup_plot):
    restore_from_backup(original_plot, backup_plot)
else:
    print(f"No backup found for module plot. Using existing file.")

# Restore party tracker from backup if available
party_tracker_backup = f"{module_dir}/party_tracker_BU.json"
if os.path.exists(party_tracker_backup):
    restore_from_backup(party_tracker_file, party_tracker_backup)
    print("Restored party tracker from backup")

# Restore norn character from backup
norn_file = path_manager.get_character_path("norn")
norn_backup = f"{module_dir}/norn_BU.json"

if os.path.exists(norn_backup):
    restore_from_backup(norn_file, norn_backup)
    print("Restored Norn character from backup")

# Clean encounter data is already handled by restoring from backups
# No need to clean again if we restored from clean backups
print("Area files restored from clean backups.")

# Delete conversation history and debug/log files
files_to_delete = [
    # Conversation history files
    'combat_conversation_history.json', 
    'conversation_history.json', 
    'chat_history.json',
    'player_conversation_history.json',
    
    # Debug log files
    'transition_debug.log', 
    'adv_summary_debug.log',
    'cumulative_summary_debug.log',
    'combat_builder.log',
    'debug_log.txt',
    'game_debug.log',
    'game_errors.log',
    'error.txt',
    
    # Summary dump files
    'summary_dump.json',
    'trimmed_summary_dump.json',
    
    # Model history files
    'second_model_history.json',
    'third_model_history.json',
    
    # Debug JSON files
    'debug_encounter_update.json',
    'debug_initial_response.json',
    'debug_npc_update.json',
    'debug_player_update.json',
    'debug_second_model.json',
    'npc_update_debug_log.json',
    'npc_update_detailed_log.json',
    'prompt_validation.json'
]

# Special handling for log files that might be in use
log_files_to_clear = ['game_debug.log', 'game_errors.log']

for file in files_to_delete:
    if os.path.exists(file):
        try:
            # For log files that might be in use, clear contents instead of deleting
            if file in log_files_to_clear:
                with open(file, 'w') as f:
                    f.write('')  # Clear the file contents
                print(f"Cleared contents of {file}")
            else:
                os.remove(file)
                print(f"Deleted {file}")
        except PermissionError:
            print(f"WARNING: Could not delete {file} - file is in use")
            # Try to clear contents if deletion fails
            if file in log_files_to_clear:
                try:
                    with open(file, 'w') as f:
                        f.write('')
                    print(f"Cleared contents of {file} instead")
                except:
                    print(f"ERROR: Could not clear {file}")
        except Exception as e:
            print(f"ERROR: Could not delete {file} - {str(e)}")
    else:
        print(f"{file} not found")

# Party tracker is restored from backup above, no manual updates needed

# Reset journal to empty state
journal_file = "journal.json"
if os.path.exists(journal_file):
    journal_data = {
        "module": "Keep_of_Doom",
        "entries": []
    }
    with open(journal_file, 'w', encoding='utf-8') as f:
        json.dump(journal_data, f, indent=2, ensure_ascii=False)
    print("Reset journal.json to empty state")

# Reset current_location.json to starting location
current_location_file = "current_location.json"
hh001_file = path_manager.get_area_path("HH001")
if os.path.exists(hh001_file):
    try:
        with open(hh001_file, 'r', encoding='utf-8') as f:
            area_data = json.load(f)
        
        # Find the starting location (A01 - General Store)
        for location in area_data.get('locations', []):
            if location.get('locationId') == 'A01':  # Updated to use new prefix
                with open(current_location_file, 'w', encoding='utf-8') as f:
                    json.dump(location, f, indent=2, ensure_ascii=False)
                print("Reset current_location.json to starting location (General Store)")
                break
    except Exception as e:
        print(f"Error resetting current_location.json: {str(e)}")

# Reset any module-specific debug files
debug_files = ['combat_validation_log.json', 'debug_ai_response.json', 'dialogue_summary.json']
for file in debug_files:
    if os.path.exists(file):
        try:
            os.remove(file)
            print(f"Deleted {file}")
        except PermissionError:
            print(f"WARNING: Could not delete {file} - file is in use")
        except Exception as e:
            print(f"ERROR: Could not delete {file} - {str(e)}")

# Character reset is handled by backup restoration above

# No longer need to clean individual plot files since we use unified plot system
# The module_plot.json is restored from backup above

# Also clean up any combat logs
combat_logs_dir = "combat_logs"
if os.path.exists(combat_logs_dir):
    for root, dirs, files in os.walk(combat_logs_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted combat log: {file_path}")
                except PermissionError:
                    print(f"WARNING: Could not delete {file_path} - file is in use")
                except Exception as e:
                    print(f"ERROR: Could not delete {file_path} - {str(e)}")

print("\nReset complete. Keep of Doom module ready to start fresh!")