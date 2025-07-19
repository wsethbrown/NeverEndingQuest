#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Script to fix all import issues in the reorganized codebase
"""

import os
import re

def fix_imports_in_file(file_path):
    """Fix import statements in a single file"""
    
    # Import replacements mapping
    replacements = {
        # utils imports
        r'from encoding_utils import': 'from utils.encoding_utils import',
        r'from file_operations import': 'from utils.file_operations import',
        r'from enhanced_logger import': 'from utils.enhanced_logger import',
        r'from module_path_manager import': 'from utils.module_path_manager import',
        r'from player_stats import': 'from utils.player_stats import',
        r'from module_context import': 'from utils.module_context import',
        r'from plot_formatting import': 'from utils.plot_formatting import',
        r'from token_estimator import': 'from utils.token_estimator import',
        r'from location_path_finder import': 'from utils.location_path_finder import',
        r'from action_predictor import': 'from utils.action_predictor import',
        r'from xp import': 'from utils.xp import',
        r'from startup_wizard import': 'from utils.startup_wizard import',
        r'from reset_campaign import': 'from utils.reset_campaign import',
        r'from sync_party_tracker import': 'from utils.sync_party_tracker import',
        r'from level_up import': 'from utils.level_up import',
        r'from analyze_module_options import': 'from utils.analyze_module_options import',
        r'from reconcile_location_state import': 'from utils.reconcile_location_state import',
        r'from redirect_debug_output import': 'from utils.redirect_debug_output import',
        
        # updates imports
        r'from update_character_info import': 'from updates.update_character_info import',
        r'from update_world_time import': 'from updates.update_world_time import',
        r'from update_encounter import': 'from updates.update_encounter import',
        r'from update_party_tracker import': 'from updates.update_party_tracker import',
        r'from plot_update import': 'from updates.plot_update import',
        r'from save_game_manager import': 'from updates.save_game_manager import',
        
        # core.managers imports
        r'from campaign_manager import': 'from core.managers.campaign_manager import',
        r'from combat_manager import': 'from core.managers.combat_manager import',
        r'from level_up_manager import': 'from core.managers.level_up_manager import',
        r'from location_manager import': 'from core.managers.location_manager import',
        r'from status_manager import': 'from core.managers.status_manager import',
        r'from storage_manager import': 'from core.managers.storage_manager import',
        r'from storage_processor import': 'from core.managers.storage_processor import',
        r'from initiative_tracker_ai import': 'from core.managers.initiative_tracker_ai import',
        r'import location_manager': 'from core.managers import location_manager',
        
        # core.generators imports
        r'from module_builder import': 'from core.generators.module_builder import',
        r'from module_generator import': 'from core.generators.module_generator import',
        r'from location_generator import': 'from core.generators.location_generator import',
        r'from location_summarizer import': 'from core.generators.location_summarizer import',
        r'from area_generator import': 'from core.generators.area_generator import',
        r'from npc_builder import': 'from core.generators.npc_builder import',
        r'from monster_builder import': 'from core.generators.monster_builder import',
        r'from plot_generator import': 'from core.generators.plot_generator import',
        r'from combat_builder import': 'from core.generators.combat_builder import',
        r'from module_stitcher import': 'from core.generators.module_stitcher import',
        r'from generate_prerolls import': 'from core.generators.generate_prerolls import',
        r'from chat_history_generator import': 'from core.generators.chat_history_generator import',
        r'from combat_history_generator import': 'from core.generators.combat_history_generator import',
        
        # core.ai imports
        r'from dm_wrapper import': 'from core.ai.dm_wrapper import',
        r'from enhanced_dm_wrapper import': 'from core.ai.enhanced_dm_wrapper import',
        r'from conversation_utils import': 'from core.ai.conversation_utils import',
        r'from cumulative_summary import': 'from core.ai.cumulative_summary import',
        r'from action_handler import': 'from core.ai.action_handler import',
        r'from adv_summary import': 'from core.ai.adv_summary import',
        r'from chunked_compression import': 'from core.ai.chunked_compression import',
        r'from chunked_compression_config import': 'from core.ai.chunked_compression_config import',
        r'from chunked_compression_integration import': 'from core.ai.chunked_compression_integration import',
        
        # core.validation imports
        r'from character_validator import': 'from core.validation.character_validator import',
        r'from dm_response_validator import': 'from core.validation.dm_response_validator import',
        r'from dm_complex_validator import': 'from core.validation.dm_complex_validator import',
        r'from npc_codex_generator import': 'from core.validation.npc_codex_generator import',
        r'from character_effects_validator import': 'from core.validation.character_effects_validator import',
        r'from validate_module_files import': 'from core.validation.validate_module_files import',
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Apply replacements
        for pattern, replacement in replacements.items():
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                # Find what was changed
                import_pattern = pattern.replace(r'from ', '').replace(r' import', '')
                changes_made.append(f"Fixed: {import_pattern}")
                content = new_content
        
        # Handle special case for main.py imports (add sys.path manipulation)
        main_import_pattern = r'(\s+)from main import ([^\n]+)'
        def main_import_replacer(match):
            indent = match.group(1)
            imports = match.group(2)
            return f'''{indent}import sys
{indent}if __name__ != "__main__":
{indent}    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
{indent}from main import {imports}'''
        
        new_content = re.sub(main_import_pattern, main_import_replacer, content)
        if new_content != content:
            changes_made.append("Fixed: main imports (added sys.path)")
            content = new_content
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        return False, []
    
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def scan_directory(directory):
    """Scan all Python files in a directory"""
    results = {}
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                changed, changes = fix_imports_in_file(file_path)
                if changed:
                    results[file_path] = changes
    
    return results

def main():
    """Main function to fix all imports"""
    print("🔧 Starting import fix process...")
    
    directories = ['core', 'utils', 'updates', 'web']
    all_results = {}
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n📁 Scanning {directory}/...")
            results = scan_directory(directory)
            all_results.update(results)
    
    # Summary
    print("\n" + "="*60)
    print("📊 IMPORT FIX SUMMARY")
    print("="*60)
    
    if all_results:
        total_files = len(all_results)
        total_fixes = sum(len(changes) for changes in all_results.values())
        
        print(f"\n✅ Fixed {total_fixes} imports in {total_files} files:\n")
        
        for file_path, changes in sorted(all_results.items()):
            print(f"\n📄 {file_path}:")
            for change in changes:
                print(f"   - {change}")
    else:
        print("\n✨ No import issues found! All imports are correct.")
    
    print("\n✅ Import fix process complete!")

if __name__ == "__main__":
    main()