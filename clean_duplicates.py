#!/usr/bin/env python3
"""
Script to clean up duplicate myth entries in mythic_myths.json
Keeps only the entries with the highest d6/d12 values (which are the complete ones)
"""

import json
import sys
from collections import defaultdict

def clean_duplicates(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group myths by name and find the one with highest d12 value
    myth_groups = defaultdict(list)
    
    for myth_name, myth_data in data['myths'].items():
        d12_value = myth_data.get('d12', 0)
        myth_groups[myth_name].append((d12_value, myth_name, myth_data))
    
    # Create new myths dict with only the highest d12 value for each myth
    cleaned_myths = {}
    
    for myth_name, myth_list in myth_groups.items():
        # Sort by d12 value and take the highest one
        myth_list.sort(key=lambda x: x[0], reverse=True)
        highest_d12, name, myth_data = myth_list[0]
        
        # Report if we're removing duplicates
        if len(myth_list) > 1:
            print(f"Removing {len(myth_list)-1} duplicate(s) of '{myth_name}', keeping d12={highest_d12}")
            for d12_val, _, _ in myth_list[1:]:
                print(f"  Removed duplicate with d12={d12_val}")
        
        cleaned_myths[name] = myth_data
    
    # Update the data
    data['myths'] = cleaned_myths
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Cleaned file saved. Total myths: {len(cleaned_myths)}")

if __name__ == '__main__':
    clean_duplicates('data/mythic_myths.json')