#!/usr/bin/env python3
"""
Extract all unique spells from leveling_info.txt for spell repository creation.
"""

import re
from collections import defaultdict

def extract_spells_from_leveling_info():
    """Extract all unique spells from leveling_info.txt"""
    
    with open('leveling_info.txt', 'r') as f:
        content = f.read()
    
    # Dictionary to store spells by class and level
    class_spells = defaultdict(lambda: defaultdict(list))
    
    # All unique spells
    all_spells = set()
    
    # Parse each class section
    current_class = None
    current_level = None
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
            
        # Detect class sections
        if 'Spells:' in line:
            current_class = line.replace(' Spells:', '').strip()
            continue
            
        # Detect spell levels
        level_match = re.match(r'^(Cantrips|1st|2nd|3rd|4th|5th|6th|7th|8th|9th):', line)
        if level_match:
            current_level = level_match.group(1)
            # Extract spells from this line
            spell_text = line.split(':', 1)[1].strip()
            if spell_text:
                spells = [s.strip() for s in spell_text.split(',')]
                for spell in spells:
                    if spell:  # Skip empty strings
                        all_spells.add(spell)
                        class_spells[current_class][current_level].append(spell)
            continue
    
    return all_spells, class_spells

def normalize_spell_name(spell_name):
    """Convert spell name to a normalized key format"""
    # Convert to lowercase, replace spaces/apostrophes with underscores
    key = spell_name.lower()
    key = re.sub(r"['\s/-]", '_', key)
    key = re.sub(r'_+', '_', key)  # Replace multiple underscores with single
    key = key.strip('_')  # Remove leading/trailing underscores
    return key

def main():
    print("Extracting spells from leveling_info.txt...")
    
    all_spells, class_spells = extract_spells_from_leveling_info()
    
    print(f"\nTotal unique spells found: {len(all_spells)}")
    
    # Show breakdown by class
    print("\nBreakdown by class:")
    for class_name, levels in class_spells.items():
        total_class_spells = sum(len(spells) for spells in levels.values())
        print(f"  {class_name}: {total_class_spells} spells")
        for level, spells in levels.items():
            print(f"    {level}: {len(spells)} spells")
    
    # Show all unique spells sorted
    print(f"\nAll {len(all_spells)} unique spells:")
    sorted_spells = sorted(all_spells)
    for i, spell in enumerate(sorted_spells, 1):
        key = normalize_spell_name(spell)
        print(f"{i:3d}. {spell} -> {key}")
    
    # Save to file for processing script
    with open('spell_list.txt', 'w') as f:
        for spell in sorted_spells:
            f.write(f"{spell}\n")
    
    print(f"\nSpell list saved to 'spell_list.txt'")
    
    # Create mapping file for reference
    with open('spell_class_mapping.txt', 'w') as f:
        f.write("Spell to Class Mapping:\n")
        f.write("=" * 40 + "\n\n")
        
        for spell in sorted_spells:
            f.write(f"{spell}:\n")
            spell_classes = []
            for class_name, levels in class_spells.items():
                for level, spells in levels.items():
                    if spell in spells:
                        spell_classes.append(f"{class_name} ({level})")
            f.write(f"  Classes: {', '.join(spell_classes)}\n\n")
    
    print("Class mapping saved to 'spell_class_mapping.txt'")

if __name__ == '__main__':
    main()