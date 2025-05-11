from datetime import datetime, timedelta
import json

def update_world_time(time_estimate_str):
    # Read the party tracker data from the JSON file
    with open("party_tracker.json", "r") as file:
        party_tracker_data = json.load(file)

    # Get the current world time and day from the party tracker data
    current_time = datetime.strptime(party_tracker_data["worldConditions"]["time"], "%H:%M:%S")
    current_day = party_tracker_data["worldConditions"]["day"]

    # Convert the time estimate from string to integer
    try:
        time_estimate_minutes = int(time_estimate_str)
    except ValueError:
        print("Invalid time estimate. Skipping world time update.")
        return

    # Update the world time by adding the time delta
    updated_time = current_time + timedelta(minutes=time_estimate_minutes)

    # Calculate the number of days passed
    days_passed = (updated_time.date() - current_time.date()).days

    # Update the world conditions with the new time and day
    party_tracker_data["worldConditions"]["time"] = updated_time.strftime("%H:%M:%S")
    party_tracker_data["worldConditions"]["day"] = current_day + days_passed

    # Save the updated party tracker data to the JSON file
    with open("party_tracker.json", "w") as file:
        json.dump(party_tracker_data, file, indent=4)

    # Debug print line in orange color
    print(f"\033[38;5;208mCurrent Time: {current_time.strftime('%H:%M:%S')}, Time Advanced: {time_estimate_minutes} minutes, New Time: {updated_time.strftime('%H:%M:%S')}, Days Passed: {days_passed}\033[0m")