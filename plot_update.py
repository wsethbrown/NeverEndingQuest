import json
from jsonschema import validate, ValidationError
from openai import OpenAI
import time

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

def load_schema():
    with open("plot_schema.json", "r") as schema_file:
        return json.load(schema_file)

def update_party_tracker(plot_point_id, new_status, plot_impact, plot_filename):
    with open("party_tracker.json", "r") as file:
        party_tracker = json.load(file)
    
    with open(f"plot_{party_tracker['worldConditions']['currentAreaId']}.json", "r") as file:
        plot_info = json.load(file)
    
    # Find the relevant plot point
    plot_point = next((p for p in plot_info["plotPoints"] if p["id"] == plot_point_id), None)
    
    if plot_point:
        # Update or add the main plot point
        existing_quest = next((q for q in party_tracker["activeQuests"] if q["id"] == plot_point_id), None)
        if existing_quest:
            existing_quest["status"] = new_status
        elif new_status != "completed":
            party_tracker["activeQuests"].append({
                "id": plot_point_id,
                "title": plot_point["title"],
                "description": plot_point["description"],
                "status": new_status
            })
        
        # Update or add side quests
        for side_quest in plot_point.get("sideQuests", []):
            existing_side_quest = next((q for q in party_tracker["activeQuests"] if q["id"] == side_quest["id"]), None)
            if existing_side_quest:
                existing_side_quest["status"] = side_quest["status"]
            else:
                party_tracker["activeQuests"].append({
                    "id": side_quest["id"],
                    "title": side_quest["title"],
                    "description": side_quest["description"],
                    "status": side_quest["status"]
                })
    
    # Remove completed quests
    party_tracker["activeQuests"] = [q for q in party_tracker["activeQuests"] if q["status"] != "completed"]
    
    # Save the updated party tracker
    with open("party_tracker.json", "w") as file:
        json.dump(party_tracker, file, indent=2)
    
    print(f"{ORANGE}DEBUG: Party tracker updated for plot point {plot_point_id}{RESET}")

def update_plot(plot_point_id, new_status, plot_impact, plot_filename, max_retries=3):
    with open(plot_filename, "r") as file:
        plot_info = json.load(file)
    
    schema = load_schema()

    for attempt in range(max_retries):
        # Prepare the prompt for the AI with examples in the system message
        prompt = [
            {"role": "system", "content": """You are an assistant that updates plot information for a role playing game. Given the current plot information and a plot point ID with its new status and plot impact, return only the updated sections of the JSON. Ensure that the updates adhere to the provided schema. Pay close attention to enum values and required fields. Be sure to update both the 'status' and 'plotImpact' fields for the specified plot point. Return the updated sections as a JSON object with the plot point ID as the key.

Examples:
1. Input: Plot point to update: PP001, New status: in progress, Plot impact: The party has entered the mines and met Old Miner Gregor.
   Output: {"PP001": {"status": "in progress", "plotImpact": "The party has entered the mines and met Old Miner Gregor."}}

2. Input: Plot point to update: PP003, New status: completed, Plot impact: The party successfully navigated the collapsed passage and found signs of recent excavation.
   Output: {"PP003": {"status": "completed", "plotImpact": "The party successfully navigated the collapsed passage and found signs of recent excavation."}}

3. Input: Plot point to update: PP005, New status: in progress, Plot impact: The party is currently battling the Fire Beetles and investigating the strange energy source.
   Output: {"PP005": {"status": "in progress", "plotImpact": "The party is currently battling the Fire Beetles and investigating the strange energy source."}}

4. Input: Plot point to update: SQ001, New status: completed, Plot impact: The party found Old Miner Gregor's lost tools in the Equipment Storage.
   Output: {"PP001": {"sideQuests": [{"id": "SQ001", "status": "completed", "plotImpact": "The party found Old Miner Gregor's lost tools in the Equipment Storage."}]}}

5. Input: Plot point to update: PP011, New status: in progress, Plot impact: The party is exploring the Crystal Cavern and deciphering hidden messages left by the dwarves.
   Output: {"PP011": {"status": "in progress", "plotImpact": "The party is exploring the Crystal Cavern and deciphering hidden messages left by the dwarves."}}"""
            },
            {"role": "user", "content": f"Current plot info: {json.dumps(plot_info)}\n\nPlot point to update: {plot_point_id}\nNew status: {new_status}\nPlot impact: {plot_impact}"}
        ]

        # Get AI's response
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            messages=prompt
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        try:
            # Remove any possible markdown formatting
            if ai_response.startswith("```json"):
                ai_response = ai_response.split("```json", 1)[1]
            if ai_response.endswith("```"):
                ai_response = ai_response.rsplit("```", 1)[0]
            
            ai_response = ai_response.strip()
            
            updated_sections = json.loads(ai_response)
            
            # Update the plot_info with the changed sections
            for plot_point_id, updates in updated_sections.items():
                for plot_point in plot_info["plotPoints"]:
                    if plot_point["id"] == plot_point_id:
                        if "sideQuests" in updates:
                            for updated_quest in updates["sideQuests"]:
                                for quest in plot_point["sideQuests"]:
                                    if quest["id"] == updated_quest["id"]:
                                        quest.update(updated_quest)
                                        break
                        else:
                            plot_point.update(updates)
                        break
            
            # Validate the entire updated plot_info against the schema
            validate(instance=plot_info, schema=schema)
            
            # If we reach here, validation was successful
            print(f"{GREEN}DEBUG: Successfully updated and validated plot info on attempt {attempt + 1}{RESET}")
            
            # Save the updated plot info
            with open(plot_filename, "w") as file:
                json.dump(plot_info, file, indent=2)
            
            # Update the party tracker
            update_party_tracker(plot_point_id, new_status, plot_impact, plot_filename)
            
            print(f"{ORANGE}DEBUG: Plot information updated for plot point {plot_point_id}{RESET}")
            return plot_info
            
        except json.JSONDecodeError as e:
            print(f"{RED}DEBUG: AI response is not valid JSON. Error: {e}{RESET}")
            print(f"{ORANGE}DEBUG: Attempting to fix JSON...{RESET}")
            try:
                # Attempt to fix common JSON errors
                fixed_response = ai_response.replace("'", '"')  # Replace single quotes with double quotes
                fixed_response = fixed_response.replace("True", "true").replace("False", "false")  # Fix boolean values
                updated_sections = json.loads(fixed_response)
                print(f"{GREEN}DEBUG: Successfully fixed JSON{RESET}")
                # Proceed with updating and validation...
            except:
                print(f"{RED}DEBUG: Failed to fix JSON. Retrying...{RESET}")
        except ValidationError as e:
            print(f"{RED}ERROR: Updated info does not match the schema. Error: {e}{RESET}")
        
        # If we've reached the maximum number of retries, return the original plot info
        if attempt == max_retries - 1:
            print(f"{RED}ERROR: Failed to update plot info after {max_retries} attempts. Returning original plot info.{RESET}")
            return plot_info
        
        # Wait for a short time before retrying
        time.sleep(1)

    # This line should never be reached, but just in case:
    return plot_info