import json
import subprocess
import os

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
        print(f"DEBUG: Welcome to the world! Creating {file_path} for the first time.")
        return None
    except json.JSONDecodeError:
        print(f"DEBUG: Invalid JSON in {file_path}.")
        return None
    except UnicodeDecodeError:
        print(f"DEBUG: Unable to decode {file_path} using UTF-8 encoding.")
        return None

def get_location_info(location_name, current_area, current_area_id):
    """Get location information based on name and area"""
    area_file = f"{current_area_id}.json" # Corrected file naming convention
    area_data = load_json_file(area_file)
    if area_data and "locations" in area_data:
        for location in area_data["locations"]:
            if location["name"] == location_name:
                return location
    return None

def get_location_data(location_id, area_id):
    """Get location data based on location ID and area ID"""
    area_file = f"{area_id}.json"
    try:
        with open(area_file, "r") as file:
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
            "weather": location_info.get("weatherConditions", ""), # Ensure consistent naming
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
    """Handle transition between locations, potentially across areas"""
    print(f"DEBUG: Handling location transition from '{current_location}' to '{new_location}'")
    print(f"DEBUG: Current area: '{current_area}', Current area ID: '{current_area_id}'")
    print(f"DEBUG: Area Connectivity ID provided: '{area_connectivity_id}'")

    party_tracker = load_json_file("party_tracker.json")
    if party_tracker:
        print("DEBUG: Successfully loaded party_tracker.json")

        current_area_file = f"{current_area_id}.json"
        print(f"DEBUG: Searching for current location in file: {current_area_file}")
        current_area_data = load_json_file(current_area_file)

        if current_area_data and "locations" in current_area_data:
            current_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == current_location), None)
            print(f"DEBUG: Current location info: {current_location_info}")
        else:
            print(f"ERROR: Failed to load current area data or 'locations' not found in {current_area_file}")
            return None

        new_location_info = None # Initialize to handle cases where it might not be set
        new_area_data = None # Initialize

        if area_connectivity_id:
            print(f"DEBUG: Transitioning to new area with ID: {area_connectivity_id}")
            new_area_file = f"{area_connectivity_id}.json"
            new_area_data = load_json_file(new_area_file)
            if new_area_data and "locations" in new_area_data:
                new_location_info = next((loc for loc in new_area_data["locations"] if loc["name"] == new_location), None)
                if new_location_info:
                    print(f"DEBUG: New location '{new_location}' found in new area {area_connectivity_id}")
                else:
                    print(f"DEBUG: New location '{new_location}' not found in new area {area_connectivity_id}")
                    # Attempt to find the location by ID if name fails, assuming new_location could be an ID
                    new_location_info = next((loc for loc in new_area_data["locations"] if loc["locationId"] == new_location), None)
                    if new_location_info:
                         print(f"DEBUG: New location with ID '{new_location}' found in new area {area_connectivity_id}")
                    else:
                        print(f"DEBUG: New location with ID '{new_location}' also not found in new area {area_connectivity_id}")
                        return None # Location not found in new area
            else:
                print(f"DEBUG: Failed to load new area data or 'locations' not found in {new_area_file}")
                return None
        else: # Transition within the same area
            new_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == new_location), None)
            if not new_location_info:
                # Attempt to find the location by ID if name fails
                new_location_info = next((loc for loc in current_area_data["locations"] if loc["locationId"] == new_location), None)

        print(f"DEBUG: New location info: {new_location_info}")

    if current_location_info:
        print(f"DEBUG: Attempting to update current_location.json")
        try:
            with open("current_location.json", "w") as file:
                json.dump(current_location_info, file, indent=2)
            print("DEBUG: Successfully updated current_location.json")
        except Exception as e:
            print(f"ERROR: Failed to update current_location.json. Error: {str(e)}")

        try:
            print("DEBUG: Running adv_summary.py to update area JSON")
            result = subprocess.run(["python", "adv_summary.py", "conversation_history.json", "current_location.json", current_location, current_area_id],
                        check=True, capture_output=True, text=True)
            print("DEBUG: adv_summary.py output:", result.stdout)
            print("DEBUG: adv_summary.py debug info:", result.stderr)
            print("DEBUG: adv_summary.py completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Error occurred while running adv_summary.py: {e}")
            print("ERROR: Error output:", e.stderr)
            print("ERROR: Standard output:", e.stdout)

        if party_tracker and new_location_info:
            print("DEBUG: Updating party_tracker with new location information")
            # Determine which area data to use for world conditions update
            area_for_conditions = new_area_data if area_connectivity_id and new_area_data else current_area_data
            area_id_for_conditions = area_connectivity_id if area_connectivity_id else current_area_id
            
            party_tracker["worldConditions"] = update_world_conditions(
                party_tracker["worldConditions"],
                new_location_info["name"], # Use name from new_location_info
                area_for_conditions.get("areaName", current_area if not area_connectivity_id else "Unknown Area"),
                area_id_for_conditions
            )
            party_tracker["worldConditions"]["currentLocation"] = new_location_info["name"] # Ensure this uses the name

            if area_connectivity_id and new_area_data:
                party_tracker["worldConditions"]["currentArea"] = new_area_data.get("areaName", "Unknown Area")
                party_tracker["worldConditions"]["currentAreaId"] = area_connectivity_id
            # else, currentArea and currentAreaId remain as they were if no area transition

            party_tracker["worldConditions"]["currentLocationId"] = new_location_info["locationId"]
            party_tracker["worldConditions"]["weatherConditions"] = new_location_info.get("weatherConditions", "") # Ensure consistent naming

            print(f"DEBUG: Attempting to update party_tracker.json")
            try:
                with open("party_tracker.json", "w") as file:
                    json.dump(party_tracker, file, indent=2)
                print("DEBUG: Successfully updated party_tracker.json")
            except Exception as e:
                print(f"ERROR: Failed to update party_tracker.json. Error: {str(e)}")

        return f"Describe the immediate surroundings and any notable features or encounters in {new_location_info['name']}, based on its recent history and current state."
    else:
        print(f"ERROR: Could not find information for current location: {current_location} or new location: {new_location}")
        return None