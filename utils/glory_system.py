# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Glory System
Replaces D&D 5e XP/Level progression
"""

import json
import os
from .module_path_manager import ModulePathManager

# Glory to Rank mapping
GLORY_RANKS = {
    0: "Knight-Errant",
    3: "Knight-Gallant", 
    6: "Knight-Tenant",
    9: "Knight-Dominant",
    12: "Knight-Radiant"
}

def get_rank_for_glory(glory):
    """Get the Knight rank for a given Glory value."""
    for required_glory in sorted(GLORY_RANKS.keys(), reverse=True):
        if glory >= required_glory:
            return GLORY_RANKS[required_glory]
    return "Knight-Errant"

def get_glory_for_rank(rank):
    """Get the minimum Glory required for a rank."""
    for glory, rank_name in GLORY_RANKS.items():
        if rank_name == rank:
            return glory
    return 0

def award_glory_for_myth(party_tracker, myth_name):
    """Award 1 Glory to all Knights who participated in resolving a Myth."""
    narrative_parts = []
    
    for member in party_tracker.get('partyMembers', []):
        # Load character data
        current_module = party_tracker.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(current_module)
        char_file = path_manager.get_character_path(member)
        
        if os.path.exists(char_file):
            with open(char_file, 'r') as f:
                character = json.load(f)
            
            old_glory = character.get('glory', 0)
            old_rank = character.get('rank', 'Knight-Errant')
            
            # Award 1 Glory
            new_glory = min(old_glory + 1, 12)  # Cap at 12
            new_rank = get_rank_for_glory(new_glory)
            
            character['glory'] = new_glory
            character['rank'] = new_rank
            
            # Save updated character
            with open(char_file, 'w') as f:
                json.dump(character, f, indent=2)
            
            # Create narrative
            if new_rank != old_rank:
                narrative_parts.append(f"{member} gains 1 Glory for resolving the {myth_name} myth and advances to {new_rank}!")
            else:
                narrative_parts.append(f"{member} gains 1 Glory for resolving the {myth_name} myth (Glory: {new_glory}).")
    
    return " ".join(narrative_parts)

def award_glory_for_duel(winner, loser, party_tracker):
    """Award Glory for a public duel - winner gains 1, loser loses 1."""
    current_module = party_tracker.get("module", "").replace(" ", "_")
    path_manager = ModulePathManager(current_module)
    
    narrative_parts = []
    
    # Handle winner
    winner_file = path_manager.get_character_path(winner)
    if os.path.exists(winner_file):
        with open(winner_file, 'r') as f:
            character = json.load(f)
        
        old_glory = character.get('glory', 0)
        new_glory = min(old_glory + 1, 12)
        new_rank = get_rank_for_glory(new_glory)
        
        character['glory'] = new_glory
        character['rank'] = new_rank
        
        with open(winner_file, 'w') as f:
            json.dump(character, f, indent=2)
        
        narrative_parts.append(f"{winner} wins the duel and gains 1 Glory ({new_rank}).")
    
    # Handle loser
    loser_file = path_manager.get_character_path(loser)
    if os.path.exists(loser_file):
        with open(loser_file, 'r') as f:
            character = json.load(f)
        
        old_glory = character.get('glory', 0)
        new_glory = max(old_glory - 1, 0)  # Cannot go below 0
        new_rank = get_rank_for_glory(new_glory)
        
        character['glory'] = new_glory
        character['rank'] = new_rank
        
        with open(loser_file, 'w') as f:
            json.dump(character, f, indent=2)
        
        narrative_parts.append(f"{loser} loses the duel and loses 1 Glory ({new_rank}).")
    
    return " ".join(narrative_parts)

def award_glory_for_tournament(winner, party_tracker):
    """Award 1 Glory for winning a tournament with significant spectators."""
    current_module = party_tracker.get("module", "").replace(" ", "_")
    path_manager = ModulePathManager(current_module)
    
    winner_file = path_manager.get_character_path(winner)
    if os.path.exists(winner_file):
        with open(winner_file, 'r') as f:
            character = json.load(f)
        
        old_glory = character.get('glory', 0)
        old_rank = character.get('rank', 'Knight-Errant')
        new_glory = min(old_glory + 1, 12)
        new_rank = get_rank_for_glory(new_glory)
        
        character['glory'] = new_glory
        character['rank'] = new_rank
        
        with open(winner_file, 'w') as f:
            json.dump(character, f, indent=2)
        
        if new_rank != old_rank:
            return f"{winner} wins the tournament and gains 1 Glory, advancing to {new_rank}!"
        else:
            return f"{winner} wins the tournament and gains 1 Glory (Glory: {new_glory})."
    
    return f"{winner} wins the tournament but their Glory could not be updated."

def award_glory_for_historic_battle(party_tracker, battle_name):
    """Award 1 Glory to all Knights on the victorious side of a historic battle."""
    narrative_parts = []
    
    for member in party_tracker.get('partyMembers', []):
        current_module = party_tracker.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(current_module)
        char_file = path_manager.get_character_path(member)
        
        if os.path.exists(char_file):
            with open(char_file, 'r') as f:
                character = json.load(f)
            
            old_glory = character.get('glory', 0)
            old_rank = character.get('rank', 'Knight-Errant')
            new_glory = min(old_glory + 1, 12)
            new_rank = get_rank_for_glory(new_glory)
            
            character['glory'] = new_glory
            character['rank'] = new_rank
            
            with open(char_file, 'w') as f:
                json.dump(character, f, indent=2)
            
            if new_rank != old_rank:
                narrative_parts.append(f"{member} gains 1 Glory for victory in the {battle_name} and advances to {new_rank}!")
            else:
                narrative_parts.append(f"{member} gains 1 Glory for victory in the {battle_name} (Glory: {new_glory}).")
    
    return " ".join(narrative_parts)

def award_glory_for_new_age(party_tracker):
    """Award 1 Glory to all Knights when moving to a new Age."""
    narrative_parts = []
    
    for member in party_tracker.get('partyMembers', []):
        current_module = party_tracker.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(current_module)
        char_file = path_manager.get_character_path(member)
        
        if os.path.exists(char_file):
            with open(char_file, 'r') as f:
                character = json.load(f)
            
            old_glory = character.get('glory', 0)
            old_rank = character.get('rank', 'Knight-Errant')
            new_glory = min(old_glory + 1, 12)
            new_rank = get_rank_for_glory(new_glory)
            
            character['glory'] = new_glory
            character['rank'] = new_rank
            
            with open(char_file, 'w') as f:
                json.dump(character, f, indent=2)
            
            if new_rank != old_rank:
                narrative_parts.append(f"{member} gains 1 Glory for service through the Age and advances to {new_rank}!")
            else:
                narrative_parts.append(f"{member} gains 1 Glory for service through the Age (Glory: {new_glory}).")
    
    return " ".join(narrative_parts)

def get_worthiness_narrative(character_name, rank, position):
    """Get narrative about worthiness for positions."""
    worthiness_map = {
        "Knight-Errant": "leading a Warband",
        "Knight-Gallant": "a seat in Council or Court", 
        "Knight-Tenant": "ruling a Holding",
        "Knight-Dominant": "ruling a Seat of Power",
        "Knight-Radiant": "the City Quest"
    }
    
    worthy_of = worthiness_map.get(rank, "unknown position")
    
    if position and position.lower() in worthy_of.lower():
        return f"{character_name} holds the rank of {rank}, proving their worthiness for {position}."
    else:
        return f"{character_name} holds the rank of {rank}, worthy of {worthy_of}."