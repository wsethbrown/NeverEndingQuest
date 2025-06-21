#!/usr/bin/env python3
"""
Analyze Module Options from Test Results

This script extracts and compares the specific adventure options presented
in each AI response to identify patterns.
"""

import json
import re
from collections import defaultdict

def extract_adventure_options(response):
    """Extract adventure options from a response"""
    options = []
    
    # Look for location names in various patterns
    # Pattern 1: Quoted names
    quoted_names = re.findall(r'"([A-Z][^"]+)"', response)
    
    # Pattern 2: Names with asterisks (italics)
    italic_names = re.findall(r'\*([A-Z][^*]+)\*', response)
    
    # Pattern 3: Capitalized multi-word phrases
    cap_phrases = re.findall(r'(?:the |a )?([A-Z][a-z]+(?: [A-Z][a-z]+)+)', response)
    
    # Combine and filter
    all_names = quoted_names + italic_names + cap_phrases
    
    # Filter out common words and phrases
    exclude = ['Norn', 'Elen', 'Keep of Doom', 'Harrow\'s Hollow', 'The', 'First', 'Second', 'Third', 'Lastly', 'Then']
    
    for name in all_names:
        if name not in exclude and len(name) > 5:
            options.append(name)
    
    return list(set(options))  # Remove duplicates

def analyze_test_results(filename):
    """Load and analyze test results"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("MODULE OPTIONS ANALYSIS")
    print("="*50)
    print(f"Analyzing {len(data['responses'])} responses\n")
    
    all_options = []
    option_counts = defaultdict(int)
    
    for i, response in enumerate(data['responses'], 1):
        print(f"Response #{i}:")
        options = extract_adventure_options(response)
        all_options.extend(options)
        
        for opt in options:
            option_counts[opt] += 1
            print(f"  - {opt}")
        print()
    
    # Analysis summary
    print("SUMMARY")
    print("="*50)
    print(f"Total unique adventure locations: {len(set(all_options))}")
    print(f"Average options per response: {len(all_options) / len(data['responses']):.1f}")
    
    # Check for repeated options
    repeated = {k: v for k, v in option_counts.items() if v > 1}
    if repeated:
        print("\nRepeated locations across responses:")
        for loc, count in sorted(repeated.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {loc}: {count} times")
    else:
        print("\nNo repeated locations - excellent variety!")
    
    # Adventure types
    print("\nAdventure themes detected:")
    themes = {
        'wilderness': ['forest', 'woods', 'wild', 'grove'],
        'mountain': ['peak', 'mountain', 'summit'],
        'desert': ['sand', 'desert', 'expanse'],
        'cold': ['frozen', 'frost', 'ice', 'winter'],
        'ocean': ['sea', 'isle', 'island'],
        'urban': ['city', 'town', 'village'],
        'underground': ['cave', 'cavern', 'labyrinth'],
        'magical': ['magic', 'fey', 'crystal', 'ancient']
    }
    
    theme_counts = defaultdict(int)
    for response in data['responses']:
        response_lower = response.lower()
        for theme, keywords in themes.items():
            if any(keyword in response_lower for keyword in keywords):
                theme_counts[theme] += 1
    
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {theme}: {count}/{len(data['responses'])} responses")

if __name__ == "__main__":
    # Find the most recent test results
    import glob
    import os
    
    test_files = glob.glob("module_randomness_test_*.json")
    if test_files:
        latest_file = max(test_files, key=os.path.getmtime)
        print(f"Analyzing: {latest_file}\n")
        analyze_test_results(latest_file)
    else:
        print("No test result files found!")