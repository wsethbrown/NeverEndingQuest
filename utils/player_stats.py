# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

import json
from datetime import datetime, timedelta
from .encoding_utils import safe_json_load, safe_json_dump
from .enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("player_stats")

def get_player_stat(player_name, stat_name, time_estimate):
    debug(f"STAT_REQUEST: get_player_stat called for {player_name}, stat: {stat_name}", category="player_stats")
    player_file = f"{player_name}.json"
    try:
        with open(player_file, "r", encoding="utf-8") as file:
            player_stats = json.load(file)
    except FileNotFoundError:
        print(f"{player_file} not found. Stat retrieval failed.")
        return "DM Note: Stat not found"
    except json.JSONDecodeError:
        print(f"{player_file} has an invalid JSON format. Stat retrieval failed.")
        return "DM Note: Stat not found"

    stat_value = None
    modifier_value = None

    if player_stats:
        if stat_name.lower() in player_stats["ability_scores"]:
            stat_value = player_stats["ability_scores"][stat_name.lower()]
            modifier_value = (stat_value - 10) // 2

    if stat_value is not None and modifier_value is not None:
        # Update the world time based on the time estimate (in minutes)
        data = safe_json_load('party_tracker.json')
        if data is None:
            print("Error: Could not load party_tracker.json")
            return "DM Note: Time update failed"

        time_str = data['worldConditions']['time']
        current_time = datetime.strptime(time_str, '%H:%M:%S')

        time_estimate_minutes = int(time_estimate)
        new_time = current_time + timedelta(minutes=time_estimate_minutes)

        data['worldConditions']['time'] = new_time.strftime('%H:%M:%S')

        safe_json_dump(data, 'party_tracker.json', indent=4)

        # Debug print line in orange color
        print(f"\033[38;5;208mCurrent Time: {current_time.strftime('%H:%M:%S')}, Time Advanced: {time_estimate_minutes} minutes, New Time: {new_time.strftime('%H:%M:%S')}\033[0m")

        return f"DM Note: Character's {stat_name.capitalize()}: {stat_value} (Modifier: {modifier_value}) | Time updated to {new_time.strftime('%H:%M:%S')}"
    else:
        return "DM Note: Stat not found"