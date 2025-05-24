import json
import os
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, ADVENTURE_SUMMARY_MODEL
from campaign_path_manager import CampaignPathManager
from file_operations import safe_write_json, safe_read_json
from encoding_utils import sanitize_text, safe_json_load, safe_json_dump

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
    """Load a JSON file with error handling and encoding sanitization"""
    try:
        return safe_json_load(file_path)
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
    """Save data to a JSON file with error handling and encoding sanitization"""
    try:
        safe_json_dump(data, file_path)
        return True
    except Exception as e:
        debug_print(f"Error saving {file_path}: {str(e)}")
        return False

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
                    # Handle encoding issues - normalize the location name
                    # Replace common problematic characters
                    location_name = location_name.replace('\u2019', "'")
                    location_name = location_name.replace('\u2018', "'")
                    location_name = location_name.replace('\u201c', '"')
                    location_name = location_name.replace('\u201d', '"')
                    location_name = location_name.replace('\u2014', '-')
                    location_name = location_name.replace('\u2013', '-')
                    location_name = location_name.replace('\u00e2\u20ac\u2122', "'")
                    location_name = location_name.replace('â€™', "'")
                    location_name = location_name.replace('â€"', '-')
                    location_name = location_name.replace('â€˜', "'")
                    location_name = location_name.replace('â€œ', '"')
                    location_name = location_name.replace('â€', '"')
                    return location_name
    return "Unknown Location"

def extract_location_id_from_conversation(conversation_history):
    """Extract the current location ID (e.g., R01, R02) from recent conversation messages"""
    import re
    for msg in reversed(conversation_history):
        if msg.get("role") == "user" and "Current location:" in msg.get("content", ""):
            # Extract location ID from DM note
            content = msg["content"]
            # Look for pattern like (R01) or (R02) etc.
            id_match = re.search(r'\(([A-Z]\d+)\)', content)
            if id_match:
                return id_match.group(1)  # Return just the ID without parentheses
    return None

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
        
        # Also check for location transitions in assistant messages
        if msg.get("role") == "assistant" and "transitionLocation" in msg.get("content", ""):
            # This is a transition message, should trigger a segment save
            if current_location and current_segment and len(current_segment) > 2:
                # Make sure we haven't already saved this segment
                if not location_segments or location_segments[-1].get("location") != current_location:
                    location_segments.append({
                        "location": current_location,
                        "messages": current_segment.copy()
                    })
                    debug_print(f"Saved segment for {current_location} due to transition")
    
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
        # Sanitize AI response to prevent encoding issues
        summary = sanitize_text(summary)
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
    Remove old-style summary messages and error notes from conversation history.
    """
    debug_print("Cleaning old-style summaries from conversation history")
    cleaned_history = []
    removed_count = 0
    
    for msg in conversation_history:
        # Skip old-style summary messages, adventure history messages, and error notes
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if (content.startswith("Summary of previous interactions:") or
                content.startswith("Adventure History Context:") or
                content.startswith("Error Note:")):
                removed_count += 1
                continue
        cleaned_history.append(msg)
    
    if removed_count > 0:
        debug_print(f"Removed {removed_count} old summary messages and error notes")
    
    return cleaned_history

def compress_conversation_history_on_transition(conversation_history, leaving_location_name):
    """
    Compress conversation history when transitioning out of a location.
    Creates a summary of the location being left and removes those messages.
    Uses location transition messages as markers.
    Returns the compressed conversation history.
    """
    debug_print(f"Compressing conversation history when leaving {leaving_location_name}")
    debug_print(f"Total messages in history: {len(conversation_history)}")
    
    # First clean old summaries
    conversation_history = clean_old_summaries_from_conversation(conversation_history)
    
    # Find the most recent location transition message
    transition_index = None
    for i in range(len(conversation_history) - 1, -1, -1):
        msg = conversation_history[i]
        if msg.get("role") == "user" and "Location transition:" in msg.get("content", ""):
            transition_index = i
            debug_print(f"Found transition at index {i}: {msg.get('content', '')}")
            break
    
    if transition_index is None:
        debug_print("No location transition found in conversation history")
        return conversation_history
    
    # Find the previous marker (transition, adventure history, or last system message)
    previous_marker_index = None
    
    # Look backwards from the transition
    for i in range(transition_index - 1, -1, -1):
        msg = conversation_history[i]
        
        # Stop at previous transition
        if msg.get("role") == "user" and "Location transition:" in msg.get("content", ""):
            previous_marker_index = i
            debug_print(f"Found previous transition at index {i}")
            break
            
        # Stop at assistant summary (from previous compression)
        if msg.get("role") == "assistant" and "=== LOCATION SUMMARY ===" in msg.get("content", ""):
            previous_marker_index = i
            debug_print(f"Found previous summary at index {i}")
            break
    
    # If no previous marker found, find the last system message
    if previous_marker_index is None:
        for i in range(transition_index - 1, -1, -1):
            if conversation_history[i].get("role") == "system":
                previous_marker_index = i
                debug_print(f"Using last system message at index {i} as start marker")
    
    # If still nothing, start from beginning
    if previous_marker_index is None:
        previous_marker_index = -1
    
    debug_print(f"Collecting messages from index {previous_marker_index + 1} to {transition_index - 1}")
    
    # Collect messages to summarize (between markers, excluding the markers themselves)
    messages_to_summarize = []
    for i in range(previous_marker_index + 1, transition_index):
        msg = conversation_history[i]
        # Include all messages except system messages and error notes
        if msg.get("role") == "system":
            continue
        if msg.get("role") == "user" and msg.get("content", "").startswith("Error Note:"):
            continue
        messages_to_summarize.append(msg)
    
    debug_print(f"Found {len(messages_to_summarize)} messages to summarize")
    
    # Generate summary if we have messages to summarize
    if len(messages_to_summarize) > 0:
        summary = generate_location_summary(leaving_location_name, messages_to_summarize)
        
        if summary:
            # Build the new conversation history
            new_history = []
            
            # 1. Keep everything up to and including the previous marker
            for i in range(0, previous_marker_index + 1):
                new_history.append(conversation_history[i])
            
            # 2. Insert the summary as an assistant message
            summary_message = {
                "role": "assistant",
                "content": f"=== LOCATION SUMMARY ===\n\n{leaving_location_name}:\n{'-' * len(leaving_location_name + ':')}\n{summary}"
            }
            new_history.append(summary_message)
            
            # 3. Add everything from the transition onwards (including the transition itself)
            for i in range(transition_index, len(conversation_history)):
                new_history.append(conversation_history[i])
            
            debug_print(f"Compressed history from {len(conversation_history)} to {len(new_history)} messages")
            debug_print(f"Removed {len(messages_to_summarize)} messages from {leaving_location_name}")
            
            return new_history
        else:
            debug_print("Failed to generate summary")
            return conversation_history
    else:
        debug_print(f"No messages to summarize for {leaving_location_name}")
        return conversation_history

def generate_enhanced_adventure_summary(conversation_history_data, party_tracker_data, leaving_location_name):
    """
    Generate an enhanced adventure summary when leaving a location.
    This is called by the transition handler to create journal entries.
    """
    debug_print(f"Generating enhanced adventure summary for {leaving_location_name}")
    
    # Find the most recent location transition message
    transition_index = None
    for i in range(len(conversation_history_data) - 1, -1, -1):
        msg = conversation_history_data[i]
        if msg.get("role") == "user" and "Location transition:" in msg.get("content", ""):
            transition_index = i
            debug_print(f"Found most recent transition at index {i}: {msg.get('content', '')}")
            break
    
    if transition_index is None:
        debug_print("No location transition found in conversation history")
        return None
    
    # Find the previous boundary (either another transition or the last system message)
    previous_boundary_index = None
    
    # Look backwards from the current transition
    for i in range(transition_index - 1, -1, -1):
        msg = conversation_history_data[i]
        
        # Stop at previous transition
        if msg.get("role") == "user" and "Location transition:" in msg.get("content", ""):
            previous_boundary_index = i
            debug_print(f"Found previous transition at index {i}")
            break
            
        # Stop at location summary (from previous compression)
        if msg.get("role") == "assistant" and "=== LOCATION SUMMARY ===" in msg.get("content", ""):
            previous_boundary_index = i
            debug_print(f"Found previous location summary at index {i}")
            break
    
    # If no previous transition found, find the last system message
    if previous_boundary_index is None:
        for i in range(transition_index - 1, -1, -1):
            if conversation_history_data[i].get("role") == "system":
                previous_boundary_index = i
                debug_print(f"Using last system message at index {i} as boundary")
        
        # If still nothing, start from beginning
        if previous_boundary_index is None:
            previous_boundary_index = -1
            debug_print("Starting from beginning of conversation")
    
    # Collect messages between boundaries (excluding the boundaries themselves)
    location_messages = []
    for i in range(previous_boundary_index + 1, transition_index):
        msg = conversation_history_data[i]
        # Include all messages except system messages
        if msg.get("role") != "system":
            location_messages.append(msg)
    
    debug_print(f"Collected {len(location_messages)} messages for location summary")
    
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
            # Sanitize AI response to prevent encoding issues
            enhanced_summary = sanitize_text(enhanced_summary)
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