#!/usr/bin/env python
# A simple test script to check location matching in different ways

import json
import sys
from campaign_path_manager import CampaignPathManager

def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def test_location_match(area_id, location_name_or_id, exact_only=False):
    """Test different methods of matching a location in an area"""
    print(f"Testing location match for area '{area_id}', looking for '{location_name_or_id}'")
    
    path_manager = CampaignPathManager()
    area_file = path_manager.get_area_path(area_id)
    print(f"Using area file: {area_file}")
    
    area_data = load_json_file(area_file)
    if not area_data or "locations" not in area_data:
        print(f"ERROR: Failed to load area data from {area_file}")
        return None
    
    # Test 1: Exact name match
    print("\nMethod 1: Exact name match")
    location = next((loc for loc in area_data["locations"] if loc["name"] == location_name_or_id), None)
    if location:
        print(f"Found location by exact name match: {location['name']} (ID: {location['locationId']})")
    else:
        print(f"No exact name match found for '{location_name_or_id}'")
        
        # Print similar names
        for loc in area_data["locations"]:
            sim_score = string_similarity(loc["name"].lower(), location_name_or_id.lower())
            if sim_score > 0.5:  # Arbitrary threshold
                print(f"  Similar: '{loc['name']}' (similarity: {sim_score:.2f})")
    
    # Test 2: ID match
    print("\nMethod 2: ID match")
    location = next((loc for loc in area_data["locations"] if loc["locationId"] == location_name_or_id), None)
    if location:
        print(f"Found location by ID match: {location['name']} (ID: {location['locationId']})")
    else:
        print(f"No ID match found for '{location_name_or_id}'")
    
    if not exact_only:
        # Test 3: Substring match
        print("\nMethod 3: Substring match (is target a substring of location name)")
        location = next((loc for loc in area_data["locations"] if location_name_or_id in loc["name"]), None)
        if location:
            print(f"Found location by substring match: {location['name']} (ID: {location['locationId']})")
        else:
            print(f"No substring match found for '{location_name_or_id}'")
            
        # Test 4: Reverse substring match
        print("\nMethod 4: Reverse substring match (is location name a substring of target)")
        locations = [loc for loc in area_data["locations"] if loc["name"] in location_name_or_id]
        if locations:
            print(f"Found {len(locations)} locations by reverse substring match:")
            for loc in locations:
                print(f"  {loc['name']} (ID: {loc['locationId']})")
        else:
            print(f"No reverse substring match found for '{location_name_or_id}'")
    
    # Print all available locations for reference
    print("\nAll available locations in this area:")
    for loc in area_data["locations"]:
        print(f"  {loc['locationId']}: '{loc['name']}'")

def string_similarity(s1, s2):
    """Return a similarity score between 0 and 1 for two strings"""
    # Use a simple method for rough similarity - longer common substrings mean more similar
    if not s1 or not s2:
        return 0.0
    
    longer = s1 if len(s1) > len(s2) else s2
    shorter = s2 if len(s1) > len(s2) else s1
    
    # Find longest common substring
    # This is not efficient for long strings but works for our purposes
    longest_common = 0
    for i in range(len(shorter)):
        for j in range(i+1, len(shorter)+1):
            substring = shorter[i:j]
            if substring in longer:
                longest_common = max(longest_common, len(substring))
    
    return longest_common / len(longer)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_location_match.py <area_id> <location_name_or_id> [exact_only]")
        print("Example: python test_location_match.py HH001 'Harrow's Hollow Town Square'")
        sys.exit(1)
    
    area_id = sys.argv[1]
    location_name_or_id = sys.argv[2]
    exact_only = len(sys.argv) > 3 and sys.argv[3].lower() == 'true'
    
    test_location_match(area_id, location_name_or_id, exact_only)