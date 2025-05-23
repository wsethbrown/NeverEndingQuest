import json
import os
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, ADVENTURE_SUMMARY_MODEL
from campaign_path_manager import CampaignPathManager

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
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        debug_print(f"Error saving to {file_path}: {str(e)}")
        return False

def get_cumulative_adventure_summary():
    """
    Build a cumulative adventure summary from all journal entries.
    Returns a formatted string containing all adventure summaries in chronological order.
    """
    debug_print("Building cumulative adventure summary from journal entries")
    
    journal_data = load_json_file("journal.json")
    if not journal_data or "entries" not in journal_data:
        debug_print("No journal entries found")
        return ""
    
    entries = journal_data.get("entries", [])
    if not entries:
        debug_print("Journal has no entries")
        return ""
    
    debug_print(f"Found {len(entries)} journal entries")
    
    # Build the cumulative summary
    summary_parts = []
    summary_parts.append("=== ADVENTURE HISTORY ===\n")
    summary_parts.append("The following is a chronological record of the party's adventures:\n")
    
    for i, entry in enumerate(entries):
        date = entry.get("date", "Unknown date")
        time = entry.get("time", "Unknown time")
        location = entry.get("location", "Unknown location")
        summary = entry.get("summary", "")
        
        # Skip entries with JSON content (these are action logs, not summaries)
        if summary.strip().startswith("{"):
            debug_print(f"Skipping entry {i+1} - contains JSON action data")
            continue
            
        # Format the entry
        entry_header = f"\n[{date}, {time}] - {location}"
        summary_parts.append(entry_header)
        summary_parts.append("-" * len(entry_header))
        summary_parts.append(summary)
        summary_parts.append("")  # Add blank line between entries
    
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
        # Skip old-style summary messages
        if (msg.get("role") == "user" and 
            msg.get("content", "").startswith("Summary of previous interactions:")):
            removed_count += 1
            continue
        cleaned_history.append(msg)
    
    if removed_count > 0:
        debug_print(f"Removed {removed_count} old-style summary messages")
    
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
    
    # Get the cumulative summary
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
    Generate an enhanced adventure summary that captures more essential details.
    """
    debug_print(f"Generating enhanced adventure summary for {leaving_location_name}")
    
    # Extract recent conversation for this location
    dialogue = "Recent events in this location:\n\n"
    for message in conversation_history_data:
        role = message.get('role')
        content = message.get('content', '')
        
        # Skip system messages and location transitions
        if role == 'system' or 'Location transition:' in content:
            continue
            
        if role == 'assistant':
            dialogue += f"Dungeon Master: {content}\n\n"
        elif role == 'user':
            # Extract player content from DM notes
            if "Player:" in content:
                player_part = content.split("Player:", 1)[1].strip()
                dialogue += f"Player: {player_part}\n\n"
    
    messages = [
        {"role": "system", "content": f"""You are a meticulous chronicler documenting a D&D 5th Edition adventure. Create a comprehensive narrative summary of ALL events that occurred in '{leaving_location_name}'.

Your summary must capture EVERYTHING that happened, organized chronologically:

1. **Setting & Atmosphere**: 
   - Initial description when party entered
   - Environmental details (lighting, temperature, sounds, smells)
   - Notable features, furniture, decorations
   - Any changes to the environment during their stay

2. **Characters & Creatures**:
   - Every NPC encountered (name, race, role, appearance, personality)
   - Initial attitudes and how they changed
   - Monsters or creatures present
   - What happened to each character by the end

3. **Player Actions & Consequences**:
   - Every action attempted (successful or failed)
   - All skill checks, saving throws, and their results
   - Combat rounds (who attacked whom, damage dealt, tactics used)
   - Spells cast and their effects
   - Items used or consumed
   - Environmental interactions (doors, levers, traps, etc.)

4. **Conversations & Information**:
   - Key dialogue exchanges and what was learned
   - Questions asked and answers received
   - Threats made or promises given
   - Any deception, persuasion, or intimidation attempts

5. **Discoveries & Loot**:
   - All items found (where and how)
   - Gold, gems, or valuables obtained
   - Secret doors, hidden compartments discovered
   - Maps, books, or documents found
   - Magical properties identified

6. **Plot Development**:
   - Story information revealed
   - Quests accepted or completed
   - Mysteries uncovered or deepened
   - Connections to larger narrative

7. **Party Changes**:
   - Damage taken or healed
   - Resources expended (spell slots, items, etc.)
   - Experience gained
   - Conditions acquired or removed
   - Inventory changes

8. **Unresolved Elements**:
   - Unopened doors or unexplored areas
   - NPCs whose fate is unknown
   - Questions left unanswered
   - Potential consequences of actions taken

Write as a detailed historical record in past tense, third person. Every fact matters - someone should be able to recreate the entire session from your summary. Be comprehensive but maintain narrative flow. Include specific numbers (damage, DC checks, gold amounts) where mentioned."""},
        {"role": "user", "content": dialogue}
    ]
    
    try:
        response = client.chat.completions.create(
            model=ADVENTURE_SUMMARY_MODEL,
            temperature=TEMPERATURE,
            messages=messages
        )
        adventure_summary = response.choices[0].message.content.strip()
        debug_print("Enhanced adventure summary generated successfully")
        return adventure_summary
    except Exception as e:
        debug_print(f"ERROR: Failed to generate enhanced adventure summary: {str(e)}")
        return None

def update_journal_with_summary(adventure_summary, party_tracker_data, location_name):
    """
    Update the journal with the new adventure summary.
    """
    debug_print(f"Updating journal with summary for {location_name}")
    
    journal_data = load_json_file("journal.json")
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
    
    if save_json_file("journal.json", journal_data):
        debug_print("Journal updated successfully")
        return True
    else:
        debug_print("Failed to update journal")
        return False