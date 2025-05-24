import json
import subprocess
import os
import unicodedata
import re
import traceback
from datetime import datetime
from campaign_path_manager import CampaignPathManager
import cumulative_summary

def load_json_file(file_path):
    """Load a JSON file, with error handling"""
    try:
        if file_path.endswith('.txt'):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
    except FileNotFoundError:
        # This message is misleading - we're not creating the file, just noting it doesn't exist
        print(f"DEBUG: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"DEBUG: Invalid JSON in {file_path}.")
        return None
    except UnicodeDecodeError:
        print(f"DEBUG: Unable to decode {file_path} using UTF-8 encoding.")
        return None

def normalize_string(s):
    """Simple string normalization for fallback comparison"""
    if not s:
        return ""
    s = unicodedata.normalize('NFC', s)
    s = s.lower().strip()
    return s

def get_location_info(location_name, current_area, current_area_id):
    """Get location information based on ID first, then name"""
    path_manager = CampaignPathManager()
    area_file = path_manager.get_area_path(current_area_id)
    area_data = load_json_file(area_file)
    if area_data and "locations" in area_data:
        # First try to find by locationId (most reliable)
        for location in area_data["locations"]:
            if location["locationId"] == location_name:
                return location
                
        # Then try exact name matching
        for location in area_data["locations"]:
            if location["name"] == location_name:
                return location
    return None

def get_location_data(location_id, area_id):
    """Get location data based on location ID and area ID"""
    path_manager = CampaignPathManager()
    area_file = path_manager.get_area_path(area_id)
    try:
        with open(area_file, "r", encoding="utf-8") as file:
            area_data = json.load(file)
        for location in area_data["locations"]:
            if location["locationId"] == location_id:
                return location
        print(f"ERROR: Location {location_id} not found in {area_file}")
    except FileNotFoundError:
        print(f"ERROR: Area file {area_file} not found")
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {area_file}")
    return None

def update_world_conditions(current_conditions, new_location, current_area, current_area_id):
    """Update world conditions based on location change"""
    from datetime import datetime, timedelta
    current_time = datetime.strptime(current_conditions["time"], "%H:%M:%S")
    new_time = (current_time + timedelta(hours=1)).strftime("%H:%M:%S")

    location_info = get_location_info(new_location, current_area, current_area_id)

    if location_info:
        return {
            "year": current_conditions["year"],
            "month": current_conditions["month"],
            "day": current_conditions["day"],
            "time": new_time,
            "weather": location_info.get("weatherConditions", ""), 
            "season": current_conditions["season"],
            "dayNightCycle": "Day" if 6 <= int(new_time[:2]) < 18 else "Night",
            "moonPhase": current_conditions["moonPhase"],
            "currentLocation": new_location,
            "currentLocationId": location_info["locationId"],
            "currentArea": current_area,
            "currentAreaId": current_area_id,
            "majorEventsUnderway": current_conditions["majorEventsUnderway"],
            "politicalClimate": "",
            "activeEncounter": "",
            "activeCombatEncounter": current_conditions.get("activeCombatEncounter", "")
        }
    else:
        return current_conditions

def handle_location_transition(current_location, new_location, current_area, current_area_id, area_connectivity_id=None):
    """Handle transition between locations, prioritizing ID matching"""
    print(f"DEBUG: Handling location transition from '{current_location}' to '{new_location}'")
    print(f"DEBUG: Current area: '{current_area}', Current area ID: '{current_area_id}'")

    party_tracker = load_json_file("party_tracker.json")
    if party_tracker:
        path_manager = CampaignPathManager()
        current_area_file = path_manager.get_area_path(current_area_id)
        current_area_data = load_json_file(current_area_file)

        if current_area_data and "locations" in current_area_data:
            # Find current location info 
            current_location_info = None
            for loc in current_area_data["locations"]:
                if loc["name"] == current_location or loc["locationId"] == current_location:
                    current_location_info = loc
                    break
                    
            if current_location_info:
                print(f"DEBUG: Current location identified: {current_location_info['name']} (ID: {current_location_info['locationId']})")
            else:
                print(f"ERROR: Current location '{current_location}' not found in area data")
                return None
        else:
            print(f"ERROR: Failed to load current area data from {current_area_file}")
            return None

        new_location_info = None
        new_area_data = None

        if area_connectivity_id:
            # Handle transition to a new area
            new_area_file = path_manager.get_area_path(area_connectivity_id)
            new_area_data = load_json_file(new_area_file)
            if new_area_data and "locations" in new_area_data:
                # Priority 1: Try to match by ID
                new_location_info = next((loc for loc in new_area_data["locations"] if loc["locationId"] == new_location), None)
                
                # Priority 2: Try to match by exact name
                if not new_location_info:
                    new_location_info = next((loc for loc in new_area_data["locations"] if loc["name"] == new_location), None)
                    
                # Priority 3: Check if the new_location is a connecting location ID
                if not new_location_info and "connectivity" in current_location_info:
                    for loc_id in current_location_info["connectivity"]:
                        if loc_id == new_location:
                            new_location_info = next((loc for loc in new_area_data["locations"] if loc["locationId"] == loc_id), None)
                            break
                
                if new_location_info:
                    print(f"DEBUG: Found new location in connected area: {new_location_info['name']} (ID: {new_location_info['locationId']})")
                else:
                    print(f"ERROR: New location '{new_location}' not found in connected area {area_connectivity_id}")
                    return None
            else:
                print(f"ERROR: Failed to load new area data from {new_area_file}")
                return None
        else:
            # Transition within the same area
            
            # Priority 1: Check if new_location is a location ID directly
            new_location_info = next((loc for loc in current_area_data["locations"] if loc["locationId"] == new_location), None)
            if new_location_info:
                print(f"DEBUG: Found new location by ID: {new_location_info['name']} (ID: {new_location_info['locationId']})")
            
            # Priority 2: Look for exact name match
            if not new_location_info:
                new_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == new_location), None)
                if new_location_info:
                    print(f"DEBUG: Found new location by exact name: {new_location_info['name']} (ID: {new_location_info['locationId']})")
            
            # Priority 3: Check if new_location matches a connecting location ID
            if not new_location_info and "connectivity" in current_location_info:
                connecting_ids = current_location_info["connectivity"]
                print(f"DEBUG: Checking against connecting location IDs: {connecting_ids}")
                
                for loc_id in connecting_ids:
                    connected_loc = next((loc for loc in current_area_data["locations"] if loc["locationId"] == loc_id), None)
                    if connected_loc:
                        # Check if the name of this connected location matches our target
                        if normalize_string(connected_loc["name"]) == normalize_string(new_location):
                            new_location_info = connected_loc
                            print(f"DEBUG: Found connection to location by name match: {new_location_info['name']} (ID: {new_location_info['locationId']})")
                            break
                
            # If still not found, check if the town square is in the list of connecting locations
            if not new_location_info and "town square" in normalize_string(new_location):
                print(f"DEBUG: Special case - looking for Town Square in connecting locations")
                for loc_id in current_location_info.get("connectivity", []):
                    connected_loc = next((loc for loc in current_area_data["locations"] if loc["locationId"] == loc_id), None)
                    if connected_loc and "square" in normalize_string(connected_loc["name"]):
                        new_location_info = connected_loc
                        print(f"DEBUG: Found Town Square as connected location: {new_location_info['name']}")
                        break

        if not new_location_info:
            print(f"ERROR: Could not find new location '{new_location}' by any method")
            return None

        print(f"DEBUG: New location info: {new_location_info['name']} (ID: {new_location_info['locationId']})")
    else:
        print("ERROR: Failed to load party_tracker.json")
        return None

    if current_location_info:
        # Update current_location.json with current location info
        try:
            with open("current_location.json", "w", encoding="utf-8") as file:
                json.dump(current_location_info, file, indent=2)
        except Exception as e:
            print(f"ERROR: Failed to update current_location.json. Error: {str(e)}")

        # Run adventure summary update
        try:
            result = subprocess.run(["python", "adv_summary.py", "conversation_history.json", "current_location.json", current_location, current_area_id],
                        check=True, capture_output=True, text=True)
            print("DEBUG: Adventure summary updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Error occurred while running adv_summary.py: {e}")
            print(f"ERROR: stdout: {e.stdout}")
            print(f"ERROR: stderr: {e.stderr}")

        # Log the transition for debugging
        debug_log_file = "transition_debug.log"
        try:
            with open(debug_log_file, "a", encoding="utf-8") as debug_file:
                debug_file.write(f"\n--- TRANSITION DEBUG: {current_location} to {new_location} ---\n")
                debug_file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                debug_file.write(f"Area ID: {current_area_id}\n")
                debug_file.write(f"Adventure summary has been generated\n")
        except Exception as e:
            print(f"ERROR: Failed to write to debug log: {str(e)}")

        # Update party tracker with new location information
        if party_tracker and new_location_info:
            area_for_conditions = new_area_data if area_connectivity_id and new_area_data else current_area_data
            area_id_for_conditions = area_connectivity_id if area_connectivity_id else current_area_id
            
            party_tracker["worldConditions"] = update_world_conditions(
                party_tracker["worldConditions"],
                new_location_info["name"],
                area_for_conditions.get("areaName", current_area if not area_connectivity_id else "Unknown Area"),
                area_id_for_conditions
            )
            
            # Explicitly set these values to ensure they're correct
            party_tracker["worldConditions"]["currentLocation"] = new_location_info["name"]
            party_tracker["worldConditions"]["currentLocationId"] = new_location_info["locationId"]

            if area_connectivity_id and new_area_data:
                party_tracker["worldConditions"]["currentArea"] = new_area_data.get("areaName", "Unknown Area")
                party_tracker["worldConditions"]["currentAreaId"] = area_connectivity_id

            try:
                with open("party_tracker.json", "w", encoding="utf-8") as file:
                    json.dump(party_tracker, file, indent=2)
                print("DEBUG: Successfully updated party_tracker.json")
            except Exception as e:
                print(f"ERROR: Failed to update party_tracker.json. Error: {str(e)}")

        return f"Describe the immediate surroundings and any notable features or encounters in {new_location_info['name']}, based on its recent history and current state."
    else:
        print(f"ERROR: Could not find information for current location: {current_location}")
        return None