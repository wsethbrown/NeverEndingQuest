#!/usr/bin/env python3
"""
Script to clean up verbose CampaignPathManager logging from game_debug.log
"""

import re

def clean_debug_log():
    """Remove repetitive CampaignPathManager lines from game_debug.log"""
    
    input_file = "game_debug.log"
    output_file = "game_debug.log.cleaned"
    
    # Patterns to match the verbose logging lines
    patterns = [
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - DEBUG - CampaignPathManager loaded campaign '[^']+' from party_tracker\.json$",
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - DEBUG - ModulePathManager loaded module '[^']+' from party_tracker\.json$"
    ]
    
    lines_removed = 0
    lines_kept = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    # Check if line matches any of the verbose patterns
                    should_remove = False
                    for pattern in patterns:
                        if re.match(pattern, line.strip()):
                            should_remove = True
                            break
                    
                    if should_remove:
                        lines_removed += 1
                        # Skip this line (don't write it to output)
                        continue
                    else:
                        outfile.write(line)
                        lines_kept += 1
        
        print(f"Cleaning complete!")
        print(f"Lines removed: {lines_removed}")
        print(f"Lines kept: {lines_kept}")
        print(f"Cleaned file saved as: {output_file}")
        print(f"To replace original: mv {output_file} {input_file}")
        
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_debug_log()