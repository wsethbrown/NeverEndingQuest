import json
import os
import sys
from openai import OpenAI
from jsonschema import validate, ValidationError
from config import OPENAI_API_KEY, ADVENTURE_SUMMARY_MODEL

TEMPERATURE = 0.8
client = OpenAI(api_key=OPENAI_API_KEY)

def get_current_location():
    try:
        with open("current_location.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("DEBUG: ERROR: current_location.json not found")
        return None
    except json.JSONDecodeError:
        print("DEBUG: ERROR: Invalid JSON in current_location.json")
        return None

def debug_print(text):
    print(f"DEBUG: {text}")

def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        debug_print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        debug_print(f"Error: Invalid JSON in {file_path}.")
        sys.exit(1)

def get_game_time():
    party_tracker = load_json_file("party_tracker.json")
    world_conditions = party_tracker.get("worldConditions", {})
    year = world_conditions.get("year", "Unknown")
    month = world_conditions.get("month", "Unknown")
    day = world_conditions.get("day", "Unknown")
    time = world_conditions.get("time", "Unknown")
    return f"{year} {month} {day}, {time}"

def validate_location_json(location_data, schema):
    try:
        validate(instance=location_data, schema=schema)
    except ValidationError as e:
        debug_print(f"Error: Invalid location data structure. {e}")
        sys.exit(1) # Or raise the error to be caught by the caller

def deep_update(original, updates):
    for key, value in updates.items():
        if isinstance(value, dict) and key in original and isinstance(original[key], dict):
            deep_update(original[key], value)
        else:
            original[key] = value

def compare_and_update(original, updates):
    changes = {}
    for key, value in updates.items():
        if key not in original or original[key] != value:
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                nested_changes = compare_and_update(original[key], value)
                if nested_changes:
                    changes[key] = nested_changes
            else:
                changes[key] = value
    return changes

def update_location_json(adventure_summary, location_info, current_area_id_from_main): # Added current_area_id from main
    debug_print(f"Updating location JSON for {location_info['name']} with all changes")

    loca_schema_full = load_json_file("loca_schema.json") # Load the full schema
    game_time = get_game_time()

    # --- CORRECTED SCHEMA ACCESS ---
    loca_single_item_schema = None
    if loca_schema_full and isinstance(loca_schema_full, dict) and \
       'properties' in loca_schema_full and \
       'locations' in loca_schema_full['properties'] and \
       isinstance(loca_schema_full['properties']['locations'], dict) and \
       'items' in loca_schema_full['properties']['locations']:
        loca_single_item_schema = loca_schema_full['properties']['locations']['items']
    else:
        debug_print(f"ERROR: Could not extract single item schema from loca_schema.json. Structure is not as expected ('properties.locations.items').")
        sys.exit("Fatal: loca_schema.json does not have the expected structure for a single location item.")
    # --- END OF CORRECTED SCHEMA ACCESS ---

    location_updater_prompt = [
        {"role": "system", "content": f"""Given an adventure summary and the current location information, update the JSON schema for the corresponding location.
        The location name is "{location_info['name']}" and should not be changed.
        Update all relevant fields based on the events that have occurred, including but not limited to:
        - Update the 'adventureSummary' field with the new summary and game time.
        - Modify 'description' if the location has changed significantly.
        - Update 'npcs', 'monsters', 'resourcesAvailable', 'plotHooks', etc., based on recent events. Be aware of any mispellings of NPCs or monsters and make sure to not create new entities if the player commands it, directs it, or mispells. For example, if the area started with an NPC called Mordenkainen, and the player refers to the NPC as Mordy, don't add Mordy to the NPC list in addition to Mordenkainen.
        - Create a new 'encounter' entry for this update. The encounterId should be the locationId appended with '-E' and then the next sequential number (e.g., if locationId is 'forest-1' and there are 2 existing encounters, the new encounterId should be 'forest-1-E3').
        - Adjust 'dangerLevel' if applicable.
        - Update any other fields that may have changed due to the party's actions such as items removed or added, damage to the location, traps disabled, doors smashed, or anything else impacting the area.

        Your output must strictly adhere to the provided JSON structure for a single location, containing no text or information before or after the JSON document.

        Location Schema (return only a single location object, not the entire schema):
        {json.dumps(loca_single_item_schema, indent=2)}

        Adventure Summary:
        {adventure_summary}

        Current Game Time:
        {game_time}

        Current Location JSON:
        {json.dumps(location_info, indent=2)}

        IMPORTANT: Always create a new encounter entry for this update, using the provided adventure summary. The encounterId should follow the format: [locationId]-[next sequential number].
        """}
    ]

    max_retries = 3
    for attempt in range(max_retries):
        debug_print(f"Attempt {attempt + 1} to update location JSON")
        try:
            response = client.chat.completions.create(
                model=ADVENTURE_SUMMARY_MODEL,
                temperature=TEMPERATURE,
                messages=location_updater_prompt
            )
            location_updates = response.choices[0].message.content.strip()
            location_updates = location_updates.replace("```json", "").replace("```", "").strip()
            updated_location = json.loads(location_updates)

            if updated_location.get("name") != location_info.get("name"): # Use .get for safety
                debug_print(f"WARNING: Location name was changed by AI or missing. Reverting/setting to original name: {location_info.get('name')}")
                updated_location["name"] = location_info.get("name") # Ensure name is present

            validate_location_json(updated_location, loca_single_item_schema)

            all_locations_file = f"{current_area_id_from_main}.json"
            all_locations = load_json_file(all_locations_file)

            found_and_updated = False
            for i, location in enumerate(all_locations.get("locations", [])): # Use .get for safety
                if location.get("name") == location_info.get("name"): # Use .get for safety
                    changes = compare_and_update(all_locations["locations"][i], updated_location)
                    deep_update(all_locations["locations"][i], changes)
                    found_and_updated = True
                    break
            
            if not found_and_updated:
                debug_print(f"ERROR: Could not find location '{location_info.get('name')}' in '{all_locations_file}' to update.")
                # Decide how to handle this: skip saving, or save anyway if structure allows, or exit.
                # For now, let's proceed to save if no structural error in all_locations occurred.

            try:
                with open(all_locations_file, "w", encoding="utf-8") as file:
                    json.dump(all_locations, file, indent=2, ensure_ascii=False)
            except IOError as e:
                debug_print(f"Error writing updated locations to {all_locations_file}: {e}")
                sys.exit(1)
            return updated_location
        except json.JSONDecodeError:
            debug_print(f"Invalid JSON from AI. Attempt {attempt + 1}/{max_retries}. Response: {location_updates}")
            if attempt < max_retries - 1:
                location_updater_prompt.append({"role": "assistant", "content": location_updates})
                location_updater_prompt.append({"role": "user", "content": "The JSON schema you provided is invalid. Please try again and ensure the output is a valid JSON format."})
            else:
                debug_print("Max retries reached. Unable to generate valid JSON.")
                sys.exit(1)
        except ValidationError as e_val: # Renamed to avoid conflict
            debug_print(f"JSON schema validation failed. Attempt {attempt + 1}/{max_retries}. Error: {e_val}")
            if attempt < max_retries - 1:
                location_updater_prompt.append({"role": "assistant", "content": location_updates}) # Send back faulty response
                location_updater_prompt.append({"role": "user", "content": f"The JSON schema you provided does not match the required structure. Error: {e_val}. Please try again."})
            else:
                debug_print("Max retries reached. Unable to generate valid JSON matching schema.")
                sys.exit(1)
        except Exception as e_gen: # Renamed to avoid conflict
            debug_print(f"Unexpected error in update_location_json: {str(e_gen)}")
            if attempt < max_retries - 1:
                debug_print(f"Retrying... Attempt {attempt + 2}/{max_retries}")
            else:
                debug_print("Max retries reached. Unable to update location JSON.")
                sys.exit(1)
    return None # Should only be reached if loop finishes without success (e.g. after retries)


def trim_conversation(summary_dump):
    trimmed_data = summary_dump[:3]
    relevant_messages = summary_dump[3:] # Messages after the initial system/user setup

    # Find the last 'Location transition:' message if any
    last_transition_index = -1
    for i, message in enumerate(relevant_messages):
        if message.get('role') == 'user' and 'Location transition:' in message.get('content', ''):
            last_transition_index = i
    
    # Start summarizing from after the last transition, or from the beginning of relevant messages
    start_summarize_from_index = last_transition_index + 1 if last_transition_index != -1 else 0
    messages_to_consider_for_summary = relevant_messages[start_summarize_from_index:]

    # Find the first assistant message in this considered segment
    first_assistant_index_in_segment = -1
    for i, message in enumerate(messages_to_consider_for_summary):
        if message.get('role') == 'assistant':
            first_assistant_index_in_segment = i
            break
            
    if first_assistant_index_in_segment != -1:
        # Take messages from the first assistant message onwards in this segment
        final_messages_for_dialogue = messages_to_consider_for_summary[first_assistant_index_in_segment:]
    else:
        # If no assistant message in the segment (e.g., only user messages after last transition),
        # then summarize what's available in that segment.
        final_messages_for_dialogue = messages_to_consider_for_summary

    trimmed_data.extend(final_messages_for_dialogue)
    return trimmed_data


def convert_to_dialogue(trimmed_data):
    dialogue = "Summarize this conversation per instructions:\n\n"
    # Iterate through messages intended for dialogue summary (those after the initial system setup)
    for message in trimmed_data[3:]: # Assuming first 3 are setup as before
        role = message.get('role')
        content = message.get('content', '')
        if role == 'assistant':
            dialogue += f"Dungeon Master: {content}\n\n"
        elif role == 'user':
            if 'Location transition:' in content: # This is a system note, not player dialogue for summary
                dialogue += f"[{content}]\n\n" # Keep as a note for context if needed by summarizer
            else: # Actual player input
                dialogue += f"Player: {content}\n\n"
    return [
        trimmed_data[0],
        {"role": "user", "content": dialogue.strip()}
    ]

def generate_adventure_summary(conversation_history_data, party_tracker_data, leaving_location_name):
    messages = [
        {"role": "system", "content": f"""You are a historian documenting the historic events of a 5th Edition roleplaying game encounter as a narrative. Provide a single, detailed and past tense narrative paragraph summarizing all factual events that occurred in '{leaving_location_name}'. Do not include in your narrative any information from prior areas or areas encountered after '{leaving_location_name}'. Include descriptions of the environment, character interactions, discoveries, and consequences of actions. Focus exclusively on what transpired in this location before the party moved to a new area. Cover all significant occurrences chronologically, including environmental details, character actions, reactions, and any information gained. Do not include dialogue, headings, bullet points, or speculation about future events. Describe only what actually happened, without editorializing or asking questions. The summary should read like a comprehensive, factual journal entry recounting past events in third-person perspective, providing a complete picture of the scene and events in {leaving_location_name}. Do not include DM notes or JSON schemas."""},
        {"role": "user", "content": "Summarize this conversation per instructions:"},
        *conversation_history_data
    ]
    dump_file_path = "summary_dump.json"
    if os.path.exists(dump_file_path):
        try:
            os.remove(dump_file_path)
        except OSError as e:
            debug_print(f"Error removing {dump_file_path}: {e}")

    try:
        with open(dump_file_path, "w", encoding="utf-8") as dump_file:
            json.dump(messages, dump_file, ensure_ascii=False, indent=2)
    except IOError as e:
        debug_print(f"Error writing to {dump_file_path}: {e}")

    trimmed_data = trim_conversation(messages)
    try:
        with open('trimmed_summary_dump.json', 'w', encoding="utf-8") as f: # Added encoding
            json.dump(trimmed_data, f, indent=2, ensure_ascii=False) # Added ensure_ascii
    except IOError as e:
        debug_print(f"Error writing to trimmed_summary_dump.json: {e}")

    dialogue_data = convert_to_dialogue(trimmed_data)
    try:
        with open('dialogue_summary.json', 'w', encoding="utf-8") as f: # Added encoding
            json.dump(dialogue_data, f, indent=2, ensure_ascii=False) # Added ensure_ascii
    except IOError as e:
        debug_print(f"Error writing to dialogue_summary.json: {e}")


    try:
        response = client.chat.completions.create(
            model=ADVENTURE_SUMMARY_MODEL,
            temperature=TEMPERATURE,
            messages=dialogue_data
        )
        adventure_summary = response.choices[0].message.content.strip()
        return adventure_summary
    except Exception as e:
        debug_print(f"ERROR: Failed to generate adventure summary. Error: {str(e)}")
        return None

def update_journal(adventure_summary, party_tracker_data, location_name):
    journal_schema = load_json_file("journal_schema.json")
    journal_data = {"entries": []} # Default to empty journal

    try:
        with open("journal.json", "r", encoding="utf-8") as journal_file:
            journal_data = json.load(journal_file)
            if not isinstance(journal_data, dict) or "entries" not in journal_data or not isinstance(journal_data["entries"], list):
                debug_print("journal.json has invalid structure, reinitializing.")
                journal_data = {"entries": []}
    except FileNotFoundError:
        debug_print("journal.json not found, creating new journal")
    except json.JSONDecodeError:
        debug_print("journal.json is empty or invalid, creating new journal")
    
    world_conditions = party_tracker_data.get('worldConditions', {}) # Use .get for safety
    new_entry = {
        "date": f"{world_conditions.get('year', 'N/A')} {world_conditions.get('month','N/A')} {world_conditions.get('day','N/A')}",
        "time": world_conditions.get('time', 'N/A'),
        "location": location_name,
        "summary": adventure_summary
    }
    journal_data["entries"].append(new_entry)

    try:
        if journal_schema: # Only validate if schema was loaded
            validate(instance=journal_data, schema=journal_schema)
    except ValidationError as e:
        debug_print(f"Error: Invalid journal entry structure. {e}")
        return # Or handle error, e.g., don't save if invalid

    try:
        with open("journal.json", "w", encoding="utf-8") as journal_file:
            json.dump(journal_data, journal_file, indent=2, ensure_ascii=False)
        debug_print("Journal updated successfully")
    except IOError as e:
        debug_print(f"Error writing to journal.json: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        debug_print("Usage: python adv_summary.py <conversation_history_file> <current_location_file> <leaving_location_name> <current_area_id>")
        sys.exit(1)

    conversation_history_file_arg = sys.argv[1]
    current_location_file_arg = sys.argv[2] # This is the JSON of the location *being left*
    leaving_location_name_arg = sys.argv[3]
    current_area_id_arg = sys.argv[4]

    conversation_history_content = load_json_file(conversation_history_file_arg)
    # The 'current_location_file_arg' contains the data for the location being left.
    # 'leaving_location_obj' will be this data.
    # We need to ensure `update_location_json` gets the correct `current_area_id` for loading `all_locations`.
    
    party_tracker_content = load_json_file("party_tracker.json")

    adventure_summary_text = generate_adventure_summary(conversation_history_content, party_tracker_content, leaving_location_name_arg)
    if adventure_summary_text is None:
        debug_print("ERROR: Unable to generate adventure summary. Exiting.")
        sys.exit(1)
    debug_print("Adventure Summary generated")

    update_journal(adventure_summary_text, party_tracker_content, leaving_location_name_arg)

    # Load the full data for the area being updated
    area_file_to_update = f"{current_area_id_arg}.json"
    all_locations_in_area = load_json_file(area_file_to_update)
    
    # Find the specific location object within that area's data that matches the name of the location being left
    leaving_location_obj_from_area = next((loc for loc in all_locations_in_area.get("locations", []) if loc.get("name") == leaving_location_name_arg), None)

    if leaving_location_obj_from_area:
        # Pass current_area_id_arg to update_location_json as it's needed to load the correct area file within that function
        updated_location_data = update_location_json(adventure_summary_text, leaving_location_obj_from_area, current_area_id_arg)
        
        if updated_location_data: # If update was successful
            # Update the main area file data in memory
            found_in_all_locations = False
            for i, location_in_list in enumerate(all_locations_in_area.get("locations", [])):
                if location_in_list.get("name") == leaving_location_name_arg:
                    all_locations_in_area["locations"][i] = updated_location_data
                    found_in_all_locations = True
                    break
            
            if found_in_all_locations:
                try:
                    with open(area_file_to_update, "w", encoding="utf-8") as file:
                        json.dump(all_locations_in_area, file, indent=2, ensure_ascii=False)
                    debug_print(f"Successfully updated {leaving_location_name_arg} in {area_file_to_update}")
                except IOError as e:
                    debug_print(f"Error writing updated area data to {area_file_to_update}: {e}")
            else:
                debug_print(f"ERROR: Could not find {leaving_location_name_arg} in {area_file_to_update} after attempting update.")
        else:
            debug_print(f"ERROR: update_location_json did not return updated data for {leaving_location_name_arg}.")
    else:
        debug_print(f"ERROR: Could not find location data for '{leaving_location_name_arg}' in '{area_file_to_update}'.")
        sys.exit(1)