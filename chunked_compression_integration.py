#!/usr/bin/env python3
"""
Integration module for chunked compression with the main game system.
This module adds chunked compression checks after location transitions.
"""

import json
import os
from chunked_compression import chunked_compression
from encoding_utils import safe_json_load, safe_json_dump
from chunked_compression_config import (
    COMPRESSION_TRIGGER, 
    ENABLE_AUTO_COMPRESSION,
    CREATE_BACKUPS
)

def check_and_perform_chunked_compression(conversation_file="conversation_history.json"):
    """
    Check if chunked compression is needed and perform it if necessary.
    This is called after location transitions when new location summaries are added.
    
    Args:
        conversation_file: Path to the conversation history file (default: conversation_history.json)
    
    Returns:
        bool: True if compression was performed, False otherwise
    """
    print("DEBUG: Checking if chunked compression is needed...")
    
    # Check if auto compression is enabled
    if not ENABLE_AUTO_COMPRESSION:
        print("DEBUG: Auto compression is disabled in configuration")
        return False
    
    try:
        # Load conversation history
        conversation_history = safe_json_load(conversation_file)
        if not conversation_history:
            print("DEBUG: No conversation history found")
            return False
        
        # Count location summaries
        location_summary_count = 0
        last_chronicle_idx = -1
        
        for i, msg in enumerate(conversation_history):
            content = msg.get('content', '')
            if '=== LOCATION SUMMARY ===' in content:
                if '[AI-Generated Chronicle Summary]' in content:
                    last_chronicle_idx = i
                else:
                    # Only count summaries after the last chronicle
                    if i > last_chronicle_idx:
                        location_summary_count += 1
        
        print(f"DEBUG: Found {location_summary_count} location summaries after last chronicle")
        
        # Check if we've hit the trigger threshold
        if location_summary_count >= COMPRESSION_TRIGGER:
            print(f"DEBUG: Compression trigger reached ({location_summary_count} >= {COMPRESSION_TRIGGER})! Performing chunked compression...")
            
            # Create a backup before compression if enabled
            if CREATE_BACKUPS:
                backup_file = f"conversation_history_backup_{os.path.getmtime(conversation_file)}.json"
                safe_json_dump(conversation_history, backup_file)
                print(f"DEBUG: Created backup: {backup_file}")
            
            # Perform compression
            success = chunked_compression(conversation_file)
            
            if success:
                print("DEBUG: Chunked compression completed successfully!")
                
                # Load the compressed file that was created
                import glob
                compressed_files = sorted(glob.glob("conversation_history_chunked_*.json"))
                if compressed_files:
                    latest_compressed = compressed_files[-1]
                    print(f"DEBUG: Using compressed file: {latest_compressed}")
                    
                    # Copy the compressed version back to the main file
                    compressed_data = safe_json_load(latest_compressed)
                    if compressed_data:
                        safe_json_dump(compressed_data, conversation_file)
                        print(f"DEBUG: Updated {conversation_file} with compressed version")
                        return True
                    else:
                        print("DEBUG: Failed to load compressed data")
                        return False
                else:
                    print("DEBUG: No compressed file found")
                    return False
            else:
                print("DEBUG: Chunked compression failed")
                return False
        else:
            print(f"DEBUG: No compression needed yet ({location_summary_count} < {COMPRESSION_TRIGGER})")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to check/perform chunked compression: {e}")
        import traceback
        traceback.print_exc()
        return False

def integrate_with_cumulative_summary():
    """
    This function should be called at the end of compress_conversation_history_on_transition
    in cumulative_summary.py to check if chunked compression is needed.
    """
    return check_and_perform_chunked_compression()