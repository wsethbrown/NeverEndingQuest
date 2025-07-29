#!/usr/bin/env python3
"""
Script to fix broken quotes in mythic_knights.json
"""

import re

def fix_knights_json():
    with open('data/mythic_knights.json', 'r') as f:
        content = f.read()
    
    # Find and fix quotes that span multiple lines without proper \n escaping
    # Pattern: "quote": "text\ntext", where \n is an actual newline not escaped
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a quote that might be broken
        if '"quote":' in line and line.rstrip().endswith('"') is False:
            # This quote line doesn't end with a quote, so it's likely broken
            quote_start = line.find('"quote": "') + len('"quote": "')
            if quote_start > len('"quote": "') - 1:  # Found the pattern
                # Find the text after "quote": "
                text_part = line[quote_start:]
                
                # Look ahead to find the closing quote
                full_quote_text = text_part
                j = i + 1
                while j < len(lines) and not lines[j].strip().endswith('",'):
                    full_quote_text += '\n' + lines[j].strip()
                    j += 1
                
                # Add the final line that ends with ",
                if j < len(lines):
                    final_line = lines[j].strip()
                    if final_line.endswith('",'):
                        full_quote_text += '\n' + final_line[:-2]  # Remove ", at end
                        
                        # Now construct the fixed line
                        escaped_text = full_quote_text.replace('\n', '\\n')
                        fixed_line = line[:quote_start] + escaped_text + '",'
                        fixed_lines.append(fixed_line)
                        
                        # Skip the lines we just processed
                        i = j + 1
                        continue
        
        # If we get here, just add the line as-is
        fixed_lines.append(line)
        i += 1
    
    # Write the fixed content
    with open('data/mythic_knights.json', 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("Fixed broken quotes in knights JSON file")

if __name__ == '__main__':
    fix_knights_json()