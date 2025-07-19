#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Comprehensive script to fix all file path issues after code reorganization.
This fixes paths for .txt files, schema files, and data files.
"""

import os
import re
import sys

def fix_file_content(file_path, replacements):
    """Apply replacements to a file and return if changes were made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        for pattern, replacement, description in replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(description)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        return False, []
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, []

def main():
    """Fix all file path issues systematically."""
    
    fixes_applied = 0
    files_modified = []
    
    # Define all the fixes needed
    file_fixes = {
        # Text file fixes
        'core/ai/conversation_utils.py': [
            (r'with open\("prompts/system_prompt\.txt"', 
             'with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "prompts", "system_prompt.txt")',
             "Fixed system_prompt.txt path with proper root joining")
        ],
        
        'core/generators/npc_builder.py': [
            (r'"prompts/generators/npc_builder_prompt\.txt"',
             'os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "prompts", "generators", "npc_builder_prompt.txt")',
             "Fixed npc_builder_prompt.txt path")
        ],
        
        'utils/startup_wizard.py': [
            (r'"leveling_info\.txt"',
             '"prompts/leveling/leveling_info.txt"',
             "Fixed leveling_info.txt path"),
            (r'"npc_builder_prompt\.txt"',
             '"prompts/generators/npc_builder_prompt.txt"',
             "Fixed npc_builder_prompt.txt path"),
            (r'safe_json_load\("char_schema\.json"\)',
             'safe_json_load("schemas/char_schema.json")',
             "Fixed char_schema.json paths")
        ],
        
        'utils/location_path_finder.py': [
            (r'with open\("debug\.txt"',
             'with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug", "location_pathfinder_debug.txt")',
             "Fixed debug.txt location")
        ],
        
        # Schema file fixes
        'core/ai/action_handler.py': [
            (r'with open\("loca_schema\.json"',
             'with open("schemas/loca_schema.json"',
             "Fixed loca_schema.json path")
        ],
        
        'core/ai/adv_summary.py': [
            (r'load_json_file\("loca_schema\.json"\)',
             'load_json_file("schemas/loca_schema.json")',
             "Fixed loca_schema.json path"),
            (r'load_json_file\("journal_schema\.json"\)',
             'load_json_file("schemas/journal_schema.json")',
             "Fixed journal_schema.json path")
        ],
        
        'core/generators/location_generator.py': [
            (r'with open\("loca_schema\.json"',
             'with open("schemas/loca_schema.json"',
             "Fixed loca_schema.json path")
        ],
        
        'core/generators/module_generator.py': [
            (r'with open\("module_schema\.json"',
             'with open("schemas/module_schema.json"',
             "Fixed module_schema.json path")
        ],
        
        'core/generators/monster_builder.py': [
            (r'load_schema\("mon_schema\.json"\)',
             'load_schema("schemas/mon_schema.json")',
             "Fixed mon_schema.json path")
        ],
        
        'core/generators/npc_builder.py': [
            (r'load_schema\("char_schema\.json"\)',
             'load_schema("schemas/char_schema.json")',
             "Fixed char_schema.json path")
        ],
        
        'core/generators/plot_generator.py': [
            (r'with open\("plot_schema\.json"',
             'with open("schemas/plot_schema.json"',
             "Fixed plot_schema.json path")
        ],
        
        'core/managers/storage_manager.py': [
            (r'self\.schema_file = "storage_action_schema\.json"',
             'self.schema_file = "schemas/storage_action_schema.json"',
             "Fixed storage_action_schema.json path")
        ],
        
        'core/managers/storage_processor.py': [
            (r'self\.schema_file = "storage_action_schema\.json"',
             'self.schema_file = "schemas/storage_action_schema.json"',
             "Fixed storage_action_schema.json path")
        ],
        
        'updates/plot_update.py': [
            (r'with open\("plot_schema\.json"',
             'with open("schemas/plot_schema.json"',
             "Fixed plot_schema.json path")
        ],
        
        'updates/update_character_info.py': [
            (r'with open\("char_schema\.json"',
             'with open("schemas/char_schema.json"',
             "Fixed char_schema.json path")
        ],
        
        'updates/update_encounter.py': [
            (r'with open\("encounter_schema\.json"',
             'with open("schemas/encounter_schema.json"',
             "Fixed encounter_schema.json path")
        ],
        
        'modify.py': [
            (r'with open\("char_schema\.json"',
             'with open("schemas/char_schema.json"',
             "Fixed char_schema.json path"),
            (r'with open\("mon_schema\.json"',
             'with open("schemas/mon_schema.json"',
             "Fixed mon_schema.json path")
        ],
        
        'test_storage_schema.py': [
            (r'safe_json_load\("storage_action_schema\.json"\)',
             'safe_json_load("schemas/storage_action_schema.json")',
             "Fixed storage_action_schema.json path")
        ],
        
        # Data file fixes
        'web/web_interface.py': [
            (r"with open\('spell_repository\.json'",
             "with open('data/spell_repository.json'",
             "Fixed spell_repository.json path")
        ],
        
        'updates/save_game_manager.py': [
            (r'"spell_repository\.json"',
             '"data/spell_repository.json"',
             "Fixed spell_repository.json path in exclusion list")
        ]
    }
    
    print("Fixing file paths after code reorganization...")
    print("=" * 60)
    
    for file_path, replacements in file_fixes.items():
        if os.path.exists(file_path):
            modified, changes = fix_file_content(file_path, replacements)
            if modified:
                fixes_applied += len(changes)
                files_modified.append(file_path)
                print(f"\n✅ {file_path}:")
                for change in changes:
                    print(f"   - {change}")
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print("\n" + "=" * 60)
    print(f"\nSummary:")
    print(f"- Files modified: {len(files_modified)}")
    print(f"- Total fixes applied: {fixes_applied}")
    
    if files_modified:
        print("\nModified files:")
        for f in sorted(files_modified):
            print(f"  - {f}")

if __name__ == "__main__":
    main()