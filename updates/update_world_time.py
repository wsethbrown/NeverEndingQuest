# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

from datetime import datetime, timedelta
import json
from utils.encoding_utils import safe_json_load, safe_json_dump

def update_world_time(time_estimate_str):
    # Read the party tracker data from the JSON file with safe encoding
    party_tracker_data = safe_json_load("party_tracker.json")
    if party_tracker_data is None:
        print("Error: Could not load party_tracker.json")
        return

    # Get the current world time and day from the party tracker data
    current_time = datetime.strptime(party_tracker_data["worldConditions"]["time"], "%H:%M:%S")
    current_day = party_tracker_data["worldConditions"]["day"]
    current_month = party_tracker_data["worldConditions"].get("month", "Springmonth")
    current_year = party_tracker_data["worldConditions"].get("year", 1492)

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

    # Update the day and handle month/year transitions
    new_day = current_day + days_passed
    new_month = current_month
    new_year = current_year

    # Define the calendar months in order
    months = [
        "Firstmonth", "Coldmonth", "Thawmonth", "Springmonth",
        "Bloommonth", "Sunmonth", "Heatmonth", "Harvestmonth",
        "Autumnmonth", "Fademonth", "Frostmonth", "Yearend"
    ]
    
    # Handle month transitions (28 days per month)
    while new_day > 28:
        new_day -= 28
        # Find current month index and advance to next month
        try:
            month_index = months.index(new_month)
            month_index = (month_index + 1) % 12
            new_month = months[month_index]
            # If we wrapped around to Firstmonth, increment year
            if month_index == 0:
                new_year += 1
        except ValueError:
            # If month name not found, default to next in sequence
            print(f"Warning: Unknown month '{new_month}', defaulting to Springmonth")
            new_month = "Springmonth"

    # Update the world conditions with the new time, day, month, and year
    party_tracker_data["worldConditions"]["time"] = updated_time.strftime("%H:%M:%S")
    party_tracker_data["worldConditions"]["day"] = new_day
    party_tracker_data["worldConditions"]["month"] = new_month
    party_tracker_data["worldConditions"]["year"] = new_year

    # Save the updated party tracker data to the JSON file with safe encoding
    safe_json_dump(party_tracker_data, "party_tracker.json", indent=4)

    # Debug print line in orange color
    if current_month != new_month:
        print(f"\033[38;5;208mCurrent Time: {current_time.strftime('%H:%M:%S')}, Time Advanced: {time_estimate_minutes} minutes, New Time: {updated_time.strftime('%H:%M:%S')}, Date: {new_year} {new_month} {new_day}\033[0m")
    else:
        print(f"\033[38;5;208mCurrent Time: {current_time.strftime('%H:%M:%S')}, Time Advanced: {time_estimate_minutes} minutes, New Time: {updated_time.strftime('%H:%M:%S')}, Days Passed: {days_passed}\033[0m")