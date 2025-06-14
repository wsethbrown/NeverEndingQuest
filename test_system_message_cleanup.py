#!/usr/bin/env python3
"""
Test script to verify system message cleanup - ensuring HP and SPELL SLOTS are removed
while maintaining all other character information.
"""

import json
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conversation_utils import update_character_data

def test_system_message_cleanup():
    """Test that HP and SPELL SLOTS are removed from system messages"""
    print("🧪 Testing System Message Cleanup")
    print("=" * 50)
    
    # Mock party tracker data
    mock_party_tracker = {
        "partyMembers": ["TestCharacter"],
        "partyNPCs": [{"name": "TestNPC", "role": "Scout"}]
    }
    
    # Mock character files would be loaded, but for testing we can check the format strings
    # Let's verify the conversation_utils.py file directly
    
    with open("conversation_utils.py", "r") as f:
        content = f.read()
    
    # Check player character format
    player_format_start = content.find('formatted_data = f"""')
    if player_format_start != -1:
        player_format_end = content.find('"""', player_format_start + 20)
        player_format = content[player_format_start:player_format_end + 3]
        
        print("📋 Player Character System Message Format:")
        print("✅ Checking for removed fields...")
        
        if "HP:" in player_format:
            print("❌ FAIL: HP still in player format")
            return False
        else:
            print("✅ PASS: HP removed from player format")
            
        if "SPELL SLOTS:" in player_format:
            print("❌ FAIL: SPELL SLOTS still in player format")
            return False
        else:
            print("✅ PASS: SPELL SLOTS removed from player format")
            
        if "INIT:" in player_format:
            print("❌ FAIL: INIT still in player format (should be removed)")
            return False
        else:
            print("✅ PASS: INIT removed from player format")
    
    # Check NPC format
    npc_format_start = content.find('formatted_data = f"""', player_format_end)
    if npc_format_start != -1:
        npc_format_end = content.find('"""', npc_format_start + 20)
        npc_format = content[npc_format_start:npc_format_end + 3]
        
        print("\n📋 NPC System Message Format:")
        print("✅ Checking for removed fields...")
        
        if "HP:" in npc_format:
            print("❌ FAIL: HP still in NPC format")
            return False
        else:
            print("✅ PASS: HP removed from NPC format")
            
        if "SPELL SLOTS:" in npc_format:
            print("❌ FAIL: SPELL SLOTS still in NPC format")
            return False
        else:
            print("✅ PASS: SPELL SLOTS removed from NPC format")
            
        if "INIT:" in npc_format:
            print("❌ FAIL: INIT still in NPC format (should be removed)")
            return False
        else:
            print("✅ PASS: INIT removed from NPC format")
    
    # Check that important fields are still present
    print("\n📋 Verifying important fields are preserved:")
    essential_fields = ["AC:", "SPD:", "STATS:", "SPELLCASTING:", "SPELLS:", "CURRENCY:"]
    
    for field in essential_fields:
        if field in player_format and field in npc_format:
            print(f"✅ PASS: {field} preserved in both formats")
        else:
            print(f"❌ FAIL: {field} missing from formats")
            return False
    
    print(f"\n🎉 SUCCESS: System message cleanup completed correctly!")
    print("   • HP removed from both player and NPC system messages")
    print("   • SPELL SLOTS removed from both player and NPC system messages") 
    print("   • INIT removed from both player and NPC system messages")
    print("   • All other essential fields preserved")
    print("   • DM Note will now be the authoritative source for dynamic data")
    
    return True

if __name__ == "__main__":
    success = test_system_message_cleanup()
    sys.exit(0 if success else 1)