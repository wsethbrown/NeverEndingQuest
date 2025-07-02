#!/usr/bin/env python3
"""
Chat History Generator

This script reads the full conversation_history.json file and creates a lightweight 
chat_history.json file that only contains the user and assistant messages, 
omitting all system prompts. This is useful for debugging and saving context.

Usage:
  python chat_history_generator.py

The script will:
1. Read the conversation_history.json file
2. Filter out all system messages
3. Create a new chat_history.json file with only user and assistant messages
"""

import json
import os
from datetime import datetime
from enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("chat_history_generator")

def generate_chat_history():
    """Generate a lightweight chat history without system messages"""
    input_file = "conversation_history.json"
    output_file = "chat_history.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    try:
        # Read the full conversation history
        with open(input_file, "r", encoding="utf-8") as f:
            full_history = json.load(f)
        
        # Filter out system messages and keep only user and assistant messages
        chat_history = [msg for msg in full_history if msg["role"] != "system"]
        
        # Create a backup of the existing chat_history.json if it exists
        if os.path.exists(output_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"chat_history_backup_{timestamp}.json"
            os.rename(output_file, backup_file)
            print(f"Created backup: {backup_file}")
        
        # Write the filtered chat history to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2)
        
        # Print statistics
        system_count = len(full_history) - len(chat_history)
        total_count = len(full_history)
        user_count = sum(1 for msg in chat_history if msg["role"] == "user")
        assistant_count = sum(1 for msg in chat_history if msg["role"] == "assistant")
        
        info(f"SUCCESS: Chat history generated successfully!", category="chat_history")
        debug(f"Total messages: {total_count}", category="chat_history")
        debug(f"System messages removed: {system_count}", category="chat_history")
        debug(f"User messages: {user_count}", category="chat_history")
        debug(f"Assistant messages: {assistant_count}", category="chat_history")
        info(f"Output saved to: {output_file}", category="chat_history")
        
    except Exception as e:
        error(f"FAILURE: {str(e)}", exception=e, category="chat_history")

if __name__ == "__main__":
    generate_chat_history()