#!/usr/bin/env python3
"""Auto-generated script to fix conversation history paths"""

import re

fixes = {
    "clear.py": [
        {"line": 76, "old": '"player_conversation_history.json"', "new": '"modules/conversation_history/conversation_history.json"'},
    ],
    "conversation_analyzer.py": [
    ],
}

def apply_fixes():
    for file_path, file_fixes in fixes.items():
        print(f"Fixing {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for fix in file_fixes:
            line_idx = fix['line'] - 1
            if line_idx < len(lines):
                lines[line_idx] = lines[line_idx].replace(fix['old'], fix['new'])
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"  Fixed {len(file_fixes)} references")

if __name__ == "__main__":
    apply_fixes()
    print("✅ All conversation paths fixed!")
