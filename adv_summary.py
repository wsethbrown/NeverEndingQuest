import json
import os
import sys
from openai import OpenAI
from jsonschema import validate, ValidationError
from config import OPENAI_API_KEY

# Constants
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.8

client = OpenAI(api_key=OPENAI_API_KEY)

def get_current_location():
    try:
        with open("current_location.json", "r") as file:
            current_location = json.load(file)
        return current_location
    except FileNotFoundError:
        print("DEBUG: ERROR: current_location.json not found")
        return None
    except json.JSONDecodeError:
        print("DEBUG: ERROR: Invalid JSON in current_location.json")
        return None

def debug_print(text):
    print(f"DEBUG: {text}")

def load_json_file(file_path):
    #debug_print(f"Loading JSON file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        #debug_print(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        debug_print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        debug_print(f"Error: Invalid JSON in {file_path}.")
        sys.exit(1)

def get_game_time():
    #debug_print("Getting game time")
    party_tracker = load_json_file("party_tracker.json")
    world_conditions = party_tracker.get("worldConditions", {})
    year = world_conditions.get("year", "Unknown")
    month = world_conditions.get("month", "Unknown")
    day = world_conditions.get("day", "Unknown")
    time = world_conditions.get("time", "Unknown")
    game_time = f"{year} {month} {day}, {time}"
    #debug_print(f"Game time: {game_time}")
    return game_time

def validate_location_json(location_data, schema):
    #debug_print("Validating location JSON")
    try:
        validate(instance=location_data, schema=schema)
        #debug_print("Location JSON validation successful")
    except ValidationError as e:
        debug_print(f"Error: Invalid location data structure. {e}")
        sys.exit(1)

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

def update_location_json(adventure_summary, location_info):
    debug_print(f"Updating location JSON for {location_info['name']} with all changes")

    loca_schema = load_json_file("loca_schema.json")
    game_time = get_game_time()

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
        {json.dumps(loca_schema[0]['properties']['locations']['items'], indent=2)}

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
                model=MODEL,
                temperature=TEMPERATURE,
                messages=location_updater_prompt
            )

            location_updates = response.choices[0].message.content.strip()
            #debug_print("Location Updater Model Output received")

            location_updates = location_updates.replace("```json", "").replace("```", "").strip()

            updated_location = json.loads(location_updates)
            
            # Ensure the name hasn't been changed
            if updated_location["name"] != location_info["name"]:
                debug_print(f"WARNING: Location name was changed. Reverting to original name: {location_info['name']}")
                updated_location["name"] = location_info["name"]

            validate_location_json(updated_location, loca_schema[0]['properties']['locations']['items'])
            #debug_print("Valid JSON schema received")

            party_tracker_data = load_json_file("party_tracker.json")
            current_area = party_tracker_data["worldConditions"]["currentArea"]
            all_locations = load_json_file(f"{current_area_id}.json")
            
            for i, location in enumerate(all_locations["locations"]):
                if location["name"] == location_info["name"]:
                    changes = compare_and_update(all_locations["locations"][i], updated_location)
                    deep_update(all_locations["locations"][i], changes)
                    #debug_print(f"Updated {updated_location['name']} in all_locations")
                    #debug_print("Changes made")
                    break

            try:
                #debug_print(f"Writing updated {updated_location['name']} to {current_area.lower().replace(' ', '_')}.json")
                with open(f"{current_area_id}.json", "w", encoding="utf-8") as file:
                    json.dump(all_locations, file, indent=2, ensure_ascii=False)
                #debug_print(f"{updated_location['name']} updated in {current_area.lower().replace(' ', '_')}.json file")
            except IOError as e:
                debug_print(f"Error writing to location.json: {e}")
                sys.exit(1)

            return updated_location

        except json.JSONDecodeError:
            debug_print(f"Invalid JSON schema received. Attempt {attempt + 1} of {max_retries}")
            if attempt < max_retries - 1:
                location_updater_prompt.append({"role": "assistant", "content": location_updates})
                location_updater_prompt.append({"role": "user", "content": "The JSON schema you provided is invalid. Please try again and ensure the output is a valid JSON format."})
            else:
                debug_print("Max retries reached. Unable to generate valid JSON.")
                sys.exit(1)
        except ValidationError as e:
            debug_print(f"JSON schema validation failed. Attempt {attempt + 1} of {max_retries}")
            if attempt < max_retries - 1:
                location_updater_prompt.append({"role": "assistant", "content": location_updates})
                location_updater_prompt.append({"role": "user", "content": f"The JSON schema you provided does not match the required structure. Error: {e}. Please try again."})
            else:
                debug_print("Max retries reached. Unable to generate valid JSON.")
                sys.exit(1)
        except Exception as e:
            debug_print(f"Unexpected error occurred: {str(e)}")
            if attempt < max_retries - 1:
                debug_print(f"Retrying... Attempt {attempt + 2} of {max_retries}")
            else:
                debug_print("Max retries reached. Unable to update location JSON.")
                sys.exit(1)

def trim_conversation(summary_dump):
    # Keep the system message and first two user messages
    trimmed_data = summary_dump[:3]
    
    # Find the last location transition
    last_transition_index = -1
    for i, message in enumerate(summary_dump[3:], start=3):
        if message['role'] == 'user' and 'Location transition:' in message['content']:
            last_transition_index = i

    # If a transition was found, trim everything before it
    if last_transition_index != -1:
        summary_dump = summary_dump[last_transition_index + 1:]
    else:
        summary_dump = summary_dump[3:]  # If no transition, start after initial messages

    # Find the first assistant message after the transition
    first_assistant_index = -1
    for i, message in enumerate(summary_dump):
        if message['role'] == 'assistant':
            first_assistant_index = i
            break

    # If an assistant message was found, trim everything before it
    if first_assistant_index != -1:
        summary_dump = summary_dump[first_assistant_index:]

    # Combine the initial messages with the trimmed conversation
    trimmed_data.extend(summary_dump)

    return trimmed_data

def convert_to_dialogue(trimmed_data):
    dialogue = "Summarize this conversation per instructions:\n\n"
    for message in trimmed_data[3:]:  # Skip the first 3 messages (system and 2 user messages with data)
        if message['role'] == 'assistant':
            dialogue += "Dungeon Master: " + message['content'] + "\n\n"
        elif message['role'] == 'user':
            dialogue += "Player: " + message['content'] + "\n\n"
        elif message['role'] == 'user' and 'Location transition:' in message['content']:
            dialogue += "[" + message['content'] + "]\n\n"
    
    return [
        trimmed_data[0],  # Keep the system message
        {
            "role": "user",
            "content": dialogue.strip()
        }
    ]

def generate_adventure_summary(conversation_history, party_tracker_data, leaving_location_name):
    #debug_print(f"Generating adventure summary for {leaving_location_name}")
    
    # Prepare the messages to be sent to the model
    messages = [
        {"role": "system", "content": f"""You are a historian documenting the historic events of a 5th Edition roleplaying game encounter as a narrative. Provide a single, detailed and past tense narrative paragraph summarizing all factual events that occurred in '{leaving_location_name}'. Do not include in your narrative any information from prior areas or areas encountered after '{leaving_location_name}'. Include descriptions of the environment, character interactions, discoveries, and consequences of actions. Focus exclusively on what transpired in this location before the party moved to a new area. Cover all significant occurrences chronologically, including environmental details, character actions, reactions, and any information gained. Do not include dialogue, headings, bullet points, or speculation about future events. Describe only what actually happened, without editorializing or asking questions. The summary should read like a comprehensive, factual journal entry recounting past events in third-person perspective, providing a complete picture of the scene and events in {leaving_location_name}. Do not include DM notes or JSON schemas."""},
        {"role": "user", "content": "Summarize this conversation per instructions:"},
        *conversation_history
    ]
    
    # Clear the dump file if it exists
    dump_file_path = "summary_dump.json"
    if os.path.exists(dump_file_path):
        os.remove(dump_file_path)
        #debug_print("Cleared existing summary_dump.json")
    
    # Dump the messages to a file for debugging
    with open(dump_file_path, "w", encoding="utf-8") as dump_file:
        json.dump(messages, dump_file, ensure_ascii=False, indent=2)
    #debug_print("Dumped model input to summary_dump.json")
    
    # Trim the conversation
    trimmed_data = trim_conversation(messages)

    # Save the trimmed summary to a new file
    with open('trimmed_summary_dump.json', 'w') as f:
        json.dump(trimmed_data, f, indent=2)
    #debug_print("Trimmed summary has been saved to 'trimmed_summary_dump.json'")

    # Convert trimmed data to dialogue format
    dialogue_data = convert_to_dialogue(trimmed_data)

    # Save the dialogue format to a new file
    with open('dialogue_summary.json', 'w') as f:
        json.dump(dialogue_data, f, indent=2)
    #debug_print("Dialogue summary has been saved to 'dialogue_summary.json'")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            messages=dialogue_data
        )
        adventure_summary = response.choices[0].message.content.strip()
        #debug_print("Generated summary")
        return adventure_summary
    except Exception as e:
        debug_print(f"ERROR: Failed to generate adventure summary. Error: {str(e)}")
        return None

def update_journal(adventure_summary, party_tracker_data, location_name):
    #debug_print("Updating journal")
    journal_schema = load_json_file("journal_schema.json")
    
    try:
        with open("journal.json", "r", encoding="utf-8") as journal_file:
            journal = json.load(journal_file)
    except FileNotFoundError:
        debug_print("journal.json not found, creating new journal")
        journal = {"entries": []}
    except json.JSONDecodeError:
        debug_print("journal.json is empty or invalid, creating new journal")
        journal = {"entries": []}

    world_conditions = party_tracker_data['worldConditions']
    new_entry = {
        "date": f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']}",
        "time": world_conditions['time'],
        "location": location_name,
        "summary": adventure_summary
    }

    journal["entries"].append(new_entry)

    try:
        validate(instance=journal, schema=journal_schema)
        #debug_print("Journal entry validation successful")
    except ValidationError as e:
        debug_print(f"Error: Invalid journal entry structure. {e}")
        return

    try:
        with open("journal.json", "w", encoding="utf-8") as journal_file:
            json.dump(journal, journal_file, indent=2, ensure_ascii=False)
        debug_print("Journal updated successfully")
    except IOError as e:
        debug_print(f"Error writing to journal.json: {e}")

    #debug_print("Current journal contents updated")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        debug_print("Usage: python adv_summary.py <conversation_history_file> <current_location_file> <leaving_location_name> <current_area_id>")
        sys.exit(1)

    conversation_history_file = sys.argv[1]
    current_location_file = sys.argv[2]
    leaving_location_name = sys.argv[3]
    current_area_id = sys.argv[4]

    #debug_print(f"Loading conversation history from {conversation_history_file}")
    conversation_history = load_json_file(conversation_history_file)
    #debug_print(f"Loading current location info from {current_location_file}")
    current_location = load_json_file(current_location_file)

    # Load party tracker data
    #debug_print("Loading party tracker data")
    party_tracker_data = load_json_file("party_tracker.json")

    current_area = party_tracker_data["worldConditions"]["currentArea"]
    #debug_print(f"Current area: {current_area}")
    #debug_print(f"Leaving location: {leaving_location_name}")

    adventure_summary = generate_adventure_summary(conversation_history, party_tracker_data, leaving_location_name)
    if adventure_summary is None:
        debug_print("ERROR: Unable to generate adventure summary. Exiting.")
        sys.exit(1)

    debug_print("Adventure Summary generated")
    #debug_print(f"Generated summary: {adventure_summary}")

    # Update journal
    update_journal(adventure_summary, party_tracker_data, leaving_location_name)

    # Load all locations for the current area
    all_locations = load_json_file(f"{current_area_id}.json")
    leaving_location = next((loc for loc in all_locations["locations"] if loc["name"] == leaving_location_name), None)

    if leaving_location:
        updated_location = update_location_json(adventure_summary, leaving_location)
        #debug_print(f"Updated Location: {leaving_location_name}")

        # Update the main location file
        #debug_print("Updating main location file")
        for i, location in enumerate(all_locations["locations"]):
            if location["name"] == leaving_location_name:
                all_locations["locations"][i] = updated_location
                break

        #debug_print(f"Writing updated locations to {current_area.lower().replace(' ', '_')}.json")
        with open(f"{current_area_id}.json", "w", encoding="utf-8") as file:
            json.dump(all_locations, file, indent=2, ensure_ascii=False)

        #debug_print(f"Updated {leaving_location_name} in {current_area.lower().replace(' ', '_')}.json file")
    else:
        debug_print(f"ERROR: Could not find location data for {leaving_location_name}")
        sys.exit(1)