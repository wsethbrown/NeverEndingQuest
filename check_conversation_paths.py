#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Script to check and fix all conversation history file paths
"""

import os
import re
import glob

# List of conversation files that should be in modules/conversation_history/
CONVERSATION_FILES = [
    'conversation_history.json',
    'chat_history.json',
    'combat_conversation_history.json',
    'combat_validation_log.json',
    'level_up_conversation.json',
    'startup_conversation.json',
    'second_model_history.json',
    'third_model_history.json'
]

def find_conversation_references(file_path):
    """Find all references to conversation history files in a Python file"""
    references = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Look for any of our conversation files
            for conv_file in CONVERSATION_FILES:
                # Various patterns to match file references
                patterns = [
                    rf'"{conv_file}"',
                    rf"'{conv_file}'",
                    rf'["\'].*{conv_file}["\']',
                    rf'conversation_file\s*=\s*["\'].*{conv_file}["\']',
                    rf'json_file\s*=\s*["\'].*{conv_file}["\']',
                    rf'file\s*=\s*["\'].*{conv_file}["\']',
                    rf'path.*{conv_file}',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line):
                        # Check if it already has the correct path
                        if 'modules/conversation_history/' in line:
                            status = "✅ CORRECT"
                        else:
                            status = "❌ NEEDS FIX"
                        
                        references.append({
                            'line_num': line_num,
                            'line': line.strip(),
                            'file': conv_file,
                            'status': status
                        })
                        break
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return references

def scan_all_python_files():
    """Scan all Python files for conversation history references"""
    all_references = {}
    
    # Scan all Python files
    for py_file in glob.glob('**/*.py', recursive=True):
        # Skip test files and this script
        if 'test' in py_file or py_file == 'check_conversation_paths.py':
            continue
        
        references = find_conversation_references(py_file)
        if references:
            all_references[py_file] = references
    
    return all_references

def main():
    print("🔍 Scanning for conversation history file references...")
    print("="*80)
    
    all_refs = scan_all_python_files()
    
    needs_fix = []
    correct = []
    
    for file_path, references in sorted(all_refs.items()):
        print(f"\n📄 {file_path}:")
        for ref in references:
            print(f"   Line {ref['line_num']}: {ref['status']}")
            print(f"      {ref['line']}")
            
            if ref['status'] == "❌ NEEDS FIX":
                needs_fix.append((file_path, ref))
            else:
                correct.append((file_path, ref))
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Correct paths: {len(correct)}")
    print(f"❌ Need fixing: {len(needs_fix)}")
    
    if needs_fix:
        print("\n🔧 Files that need path updates:")
        seen_files = set()
        for file_path, ref in needs_fix:
            if file_path not in seen_files:
                print(f"   - {file_path}")
                seen_files.add(file_path)
        
        # Generate fix script
        print("\n📝 Generating fix script...")
        generate_fix_script(needs_fix)

def generate_fix_script(needs_fix):
    """Generate a script to fix the paths"""
    fixes = {}
    
    for file_path, ref in needs_fix:
        if file_path not in fixes:
            fixes[file_path] = []
        
        # Determine the fix needed
        line = ref['line']
        conv_file = ref['file']
        
        # Common patterns and their fixes
        if f'"{conv_file}"' in line:
            old_pattern = f'"{conv_file}"'
            new_pattern = f'"modules/conversation_history/{conv_file}"'
        elif f"'{conv_file}'" in line:
            old_pattern = f"'{conv_file}'"
            new_pattern = f"'modules/conversation_history/{conv_file}'"
        else:
            # More complex pattern - extract the current path
            match = re.search(rf'["\']([^"\']*{conv_file})["\']', line)
            if match:
                old_pattern = f'"{match.group(1)}"'
                new_pattern = f'"modules/conversation_history/{conv_file}"'
            else:
                continue
        
        fixes[file_path].append({
            'line_num': ref['line_num'],
            'old': old_pattern,
            'new': new_pattern,
            'full_line': line
        })
    
    # Write fix script
    with open('fix_conversation_paths.py', 'w') as f:
        f.write('''#!/usr/bin/env python3
"""Auto-generated script to fix conversation history paths"""

import re

fixes = {
''')
        
        for file_path, file_fixes in fixes.items():
            f.write(f'    "{file_path}": [\n')
            for fix in file_fixes:
                f.write(f'        {{"line": {fix["line_num"]}, "old": {repr(fix["old"])}, "new": {repr(fix["new"])}}},\n')
            f.write('    ],\n')
        
        f.write('''}

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
''')
    
    print("✅ Fix script generated: fix_conversation_paths.py")

if __name__ == "__main__":
    main()