import json
from cumulative_summary import check_and_compact_missing_summaries
from file_operations import safe_read_json, safe_write_json

# Load conversation history and party tracker
conversation_history = safe_read_json('conversation_history.json')
party_tracker = safe_read_json('party_tracker.json')

print(f'Total messages: {len(conversation_history)}')

# Run the compact function
print('\nRunning check_and_compact_missing_summaries...')
updated_history = check_and_compact_missing_summaries(conversation_history, party_tracker)

# Check if anything changed
if len(updated_history) != len(conversation_history):
    print(f'\nHistory updated: {len(conversation_history)} -> {len(updated_history)} messages')
    
    # Count how many summaries were added
    original_summaries = sum(1 for msg in conversation_history 
                           if msg.get("role") == "assistant" 
                           and "=== LOCATION SUMMARY ===" in msg.get("content", ""))
    new_summaries = sum(1 for msg in updated_history 
                       if msg.get("role") == "assistant" 
                       and "=== LOCATION SUMMARY ===" in msg.get("content", ""))
    
    print(f'Original summaries: {original_summaries}')
    print(f'New summaries: {new_summaries}')
    print(f'Summaries added: {new_summaries - original_summaries}')
    
    # Save the updated history
    safe_write_json('conversation_history.json', updated_history)
    print('Saved updated conversation history')
    
    # Show where summaries were inserted
    print('\nSummary locations:')
    for i, msg in enumerate(updated_history):
        if msg.get("role") == "assistant" and "=== LOCATION SUMMARY ===" in msg.get("content", ""):
            # Get the location name from the summary
            content = msg.get("content", "")
            lines = content.split('\n')
            if len(lines) > 2:
                location_line = lines[2]
                print(f'  Index {i}: {location_line}')
else:
    print('No changes made to history')