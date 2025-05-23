import json
import os
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, ADVENTURE_SUMMARY_MODEL
from campaign_path_manager import CampaignPathManager
from file_operations import safe_write_json, safe_read_json

TEMPERATURE = 0.8
client = OpenAI(api_key=OPENAI_API_KEY)

def debug_print(text, log_to_file=True):
    """Print debug message and optionally log to file"""
    print(f"DEBUG: {text}")
    if log_to_file:
        try:
            with open("cumulative_summary_debug.log", "a") as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
        except Exception as e:
            print(f"DEBUG: Could not write to debug log file: {str(e)}")

def load_json_file(file_path):
    """Load a JSON file with error handling"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        debug_print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        debug_print(f"Invalid JSON in {file_path}: {str(e)}")
        return None
    except Exception as e:
        debug_print(f"Error loading {file_path}: {str(e)}")
        return None

def save_json_file(file_path, data):
    """Save data to a JSON file with error handling"""
    return safe_write_json(file_path, data)

def extract_location_from_conversation(conversation_history):
    """Extract the current location from recent conversation messages"""
    for msg in reversed(conversation_history):
        if msg.get("role") == "user" and "Current location:" in msg.get("content", ""):
            # Extract location from DM note
            content = msg["content"]
            loc_match = content.find("Current location:")
            if loc_match != -1:
                loc_text = content[loc_match:].split(".")[0]
                # Extract location name (before the ID in parentheses)
                if "(" in loc_text:
                    location_name = loc_text.split("(")[0].replace("Current location:", "").strip()
                    return location_name
    return "Unknown Location"

def get_session_start_index(conversation_history):
    """Find where the current play session starts in conversation history"""
    # Look for the first user message after the system prompts
    for i, msg in enumerate(conversation_history):
        if msg.get("role") == "user" and not msg.get("content", "").startswith("Adventure History Context:"):
            # This is likely the first actual player input of the session
            return i
    return 0

def build_location_summaries_from_conversation(conversation_history):
    """
    Build location summaries from the current conversation history only.
    This creates summaries for each location visited during the current play session.
    """
    debug_print("Building location summaries from current conversation")
    
    session_start = get_session_start_index(conversation_history)
    debug_print(f"Session starts at index {session_start}")
    
    # Track location changes and collect messages for each location
    location_segments = []
    current_location = None
    current_segment = []
    
    for i in range(session_start, len(conversation_history)):
        msg = conversation_history[i]
        
        # Check for location changes in user messages (DM notes)
        if msg.get("role") == "user" and "Current location:" in msg.get("content", ""):
            new_location = extract_location_from_conversation([msg])
            
            if current_location and current_location != new_location and current_segment:
                # Save the previous location's messages
                location_segments.append({
                    "location": current_location,
                    "messages": current_segment.copy()
                })
                current_segment = []
            
            current_location = new_location
        
        # Add message to current segment (skip system messages and adventure history)
        if msg.get("role") != "system" and not (
            msg.get("role") == "user" and msg.get("content", "").startswith("Adventure History Context:")
        ):
            current_segment.append(msg)
    
    # Save the final location segment
    if current_location and current_segment:
        location_segments.append({
            "location": current_location,
            "messages": current_segment
        })
    
    debug_print(f"Found {len(location_segments)} location segments in current session")
    
    # Generate summaries for each location
    summaries = []
    for segment in location_segments:
        if len(segment["messages"]) > 2:  # Only summarize if there's meaningful content
            summary = generate_location_summary(segment["location"], segment["messages"])
            if summary:
                summaries.append({
                    "location": segment["location"],
                    "summary": summary
                })
    
    return summaries

def generate_location_summary(location_name, messages):
    """Generate a summary for what happened in a specific location"""
    debug_print(f"Generating summary for {location_name}")
    
    # Extract conversation content
    dialogue = f"Events in {location_name}:\n\n"
    for message in messages:
        role = message.get('role')
        content = message.get('content', '')
        
        if role == 'assistant':
            # Extract narration from JSON if present
            if content.strip().startswith("{"):
                try:
                    parsed = json.loads(content)
                    narration = parsed.get("narration", content)
                    dialogue += f"Dungeon Master: {narration}\n\n"
                except:
                    dialogue += f"Dungeon Master: {content}\n\n"
            else:
                dialogue += f"Dungeon Master: {content}\n\n"
        elif role == 'user':
            # Extract player content from DM notes
            if "Player:" in content:
                player_part = content.split("Player:", 1)[1].strip()
                dialogue += f"Player: {player_part}\n\n"
    
    # Create summary prompt
    messages = [
        {"role": "system", "content": f"""You are a chronicler documenting a D&D adventure. Create a concise but comprehensive summary of what happened in '{location_name}'.

Your summary should capture:
1. What the party did when they arrived
2. Who they encountered (NPCs, monsters)
3. Any combat or challenges faced
4. Important conversations or information learned
5. Items found or resources used
6. How the visit concluded

Write in past tense, third person. Be specific about outcomes and consequences. Keep it focused on what actually happened, not what might happen."""},
        {"role": "user", "content": dialogue}
    ]
    
    try:
        response = client.chat.completions.create(
            model=ADVENTURE_SUMMARY_MODEL,
            temperature=TEMPERATURE,
            messages=messages,
            max_tokens=500  # Keep summaries concise
        )
        summary = response.choices[0].message.content.strip()
        debug_print(f"Summary generated for {location_name}")
        return summary
    except Exception as e:
        debug_print(f"ERROR: Failed to generate summary for {location_name}: {str(e)}")
        return None

def get_cumulative_adventure_summary():
    """
    Build a cumulative adventure summary from the current play session only.
    Returns a formatted string containing summaries of locations visited this session.
    """
    debug_print("Building cumulative adventure summary for current session")
    
    # Load current conversation history
    conversation_history = safe_read_json("conversation_history.json")
    if not conversation_history:
        debug_print("No conversation history found")
        return ""
    
    # Get summaries for this session
    location_summaries = build_location_summaries_from_conversation(conversation_history)
    
    if not location_summaries:
        debug_print("No location summaries generated for current session")
        return ""
    
    # Build the cumulative summary
    summary_parts = []
    summary_parts.append("=== CURRENT SESSION SUMMARY ===\n")
    summary_parts.append("Summary of locations visited during this play session:\n")
    
    for loc_summary in location_summaries:
        summary_parts.append(f"\n{loc_summary['location']}:")
        summary_parts.append("-" * len(loc_summary['location'] + ":"))
        summary_parts.append(loc_summary['summary'])
        summary_parts.append("")  # Blank line between entries
    
    cumulative_summary = "\n".join(summary_parts)
    debug_print(f"Built cumulative summary with {len(cumulative_summary)} characters")
    
    return cumulative_summary

def clean_old_summaries_from_conversation(conversation_history):
    """
    Remove old-style summary messages from conversation history.
    """
    debug_print("Cleaning old-style summaries from conversation history")
    cleaned_history = []
    removed_count = 0
    
    for msg in conversation_history:
        # Skip old-style summary messages and adventure history messages
        if (msg.get("role") == "user" and 
            (msg.get("content", "").startswith("Summary of previous interactions:") or
             msg.get("content", "").startswith("Adventure History Context:"))):
            removed_count += 1
            continue
        cleaned_history.append(msg)
    
    if removed_count > 0:
        debug_print(f"Removed {removed_count} old summary messages")
    
    return cleaned_history

def insert_cumulative_summary_in_conversation(conversation_history):
    """
    Insert the cumulative adventure summary into the conversation history.
    Places it after the main system prompt but before other messages.
    Returns the updated conversation history.
    """
    debug_print("Inserting cumulative summary into conversation history")
    
    # First clean old summaries
    conversation_history = clean_old_summaries_from_conversation(conversation_history)
    
    # Get the cumulative summary for current session
    cumulative_summary = get_cumulative_adventure_summary()
    if not cumulative_summary:
        debug_print("No cumulative summary to insert")
        return conversation_history
    
    # Find where to insert the summary (after first system message)
    insert_index = 1  # Default to position 1
    for i, msg in enumerate(conversation_history):
        if msg.get("role") == "system":
            insert_index = i + 1
            break
    
    # Create the summary message
    summary_message = {
        "role": "user",
        "content": f"Adventure History Context:\n{cumulative_summary}"
    }
    
    # Check if a cumulative summary already exists and update it
    summary_exists = False
    for i, msg in enumerate(conversation_history):
        if msg.get("role") == "user" and "Adventure History Context:" in msg.get("content", ""):
            debug_print("Updating existing cumulative summary")
            conversation_history[i] = summary_message
            summary_exists = True
            break
    
    # If no existing summary, insert it
    if not summary_exists:
        debug_print(f"Inserting new cumulative summary at position {insert_index}")
        conversation_history.insert(insert_index, summary_message)
    
    return conversation_history

def generate_enhanced_adventure_summary(conversation_history_data, party_tracker_data, leaving_location_name):
    """
    Generate an enhanced adventure summary when leaving a location.
    This is called by the transition handler to create journal entries.
    """
    debug_print(f"Generating enhanced adventure summary for {leaving_location_name}")
    
    # Extract messages for this specific location
    location_messages = []
    in_location = False
    
    for msg in reversed(conversation_history_data):
        # Check if we're in the target location
        if msg.get("role") == "user" and "Current location:" in msg.get("content", ""):
            current_loc = extract_location_from_conversation([msg])
            if current_loc == leaving_location_name:
                in_location = True
            elif in_location:
                # We've gone back to a different location, stop collecting
                break
        
        if in_location and msg.get("role") != "system":
            location_messages.insert(0, msg)  # Insert at beginning to maintain order
    
    if not location_messages:
        debug_print(f"No messages found for location {leaving_location_name}")
        return None
    
    # Generate the summary using the same function
    summary = generate_location_summary(leaving_location_name, location_messages)
    
    # For journal entries, we want a more detailed summary
    if summary:
        # Enhance the summary with specific details
        messages = [
            {"role": "system", "content": """Expand this summary into a detailed journal entry that captures ALL important details:
- Exact sequence of events
- All NPCs encountered and their responses
- Combat details (who attacked, damage dealt, outcomes)
- Items found and their properties
- Information learned
- Decisions made and their immediate consequences
- State of the party when leaving

Keep the narrative engaging but factual."""},
            {"role": "user", "content": f"Original summary: {summary}\n\nPlease expand this into a comprehensive journal entry."}
        ]
        
        try:
            response = client.chat.completions.create(
                model=ADVENTURE_SUMMARY_MODEL,
                temperature=TEMPERATURE,
                messages=messages
            )
            enhanced_summary = response.choices[0].message.content.strip()
            debug_print("Enhanced adventure summary generated successfully")
            return enhanced_summary
        except Exception as e:
            debug_print(f"ERROR: Failed to enhance adventure summary: {str(e)}")
            return summary  # Return original if enhancement fails
    
    return None

def update_journal_with_summary(adventure_summary, party_tracker_data, location_name):
    """
    Update the journal with the new adventure summary.
    This adds to the journal but doesn't affect conversation history.
    """
    debug_print(f"Updating journal with summary for {location_name}")
    
    journal_data = safe_read_json("journal.json")
    if not journal_data:
        journal_data = {"entries": []}
    
    world_conditions = party_tracker_data.get('worldConditions', {})
    new_entry = {
        "date": f"{world_conditions.get('year', 'N/A')} {world_conditions.get('month','N/A')} {world_conditions.get('day','N/A')}",
        "time": world_conditions.get('time', 'N/A'),
        "location": location_name,
        "summary": adventure_summary
    }
    
    journal_data["entries"].append(new_entry)
    
    if safe_write_json("journal.json", journal_data):
        debug_print("Journal updated successfully")
        return True
    else:
        debug_print("Failed to update journal")
        return False