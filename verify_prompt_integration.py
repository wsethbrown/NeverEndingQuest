#!/usr/bin/env python3
"""
Verify that our storage currency fixes are properly integrated into the prompt files
"""

import os

def check_system_prompt():
    """Check if system prompt has the required storage currency instructions"""
    
    print("🔍 CHECKING SYSTEM PROMPT INTEGRATION")
    print("=" * 60)
    
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_patterns = [
            "Storage With Fees Protocol",
            "TWO separate actions in this exact order",
            "updateCharacterInfo - Handle currency payment",
            "storageInteraction - Handle the actual item storage", 
            "1 gold = 10 silver = 100 copper",
            "Convert gold to silver automatically if needed",
            "Show the conversion math in the changes description",
            "Convert 1 gold to 10 silver",
            "final: 155 gold, 8 silver, 0 copper",
            "Currency payment must always come before storage action"
        ]
        
        missing_patterns = []
        found_patterns = []
        
        for pattern in required_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ Found: '{pattern}'")
            else:
                missing_patterns.append(pattern)
                print(f"❌ Missing: '{pattern}'")
        
        print(f"\nSUMMARY: {len(found_patterns)}/{len(required_patterns)} patterns found")
        
        if missing_patterns:
            print("⚠️  MISSING PATTERNS:")
            for pattern in missing_patterns:
                print(f"   - {pattern}")
        else:
            print("✅ All required patterns found in system prompt!")
            
        return len(missing_patterns) == 0
        
    except FileNotFoundError:
        print("❌ system_prompt.txt not found!")
        return False
    except Exception as e:
        print(f"❌ Error reading system prompt: {e}")
        return False

def check_validation_prompt():
    """Check if validation prompt has the required validation rules"""
    
    print("\n🔍 CHECKING VALIDATION PROMPT INTEGRATION")
    print("=" * 60)
    
    try:
        with open("validation_prompt.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        required_patterns = [
            "STORAGE TRANSACTION VALIDATION",
            "CURRENCY MATH ACCURACY",
            "Check if character has sufficient total currency value",
            "1 gold = 10 silver = 100 copper",
            "ACTION SEQUENCE CORRECTNESS",
            "updateCharacterInfo) MUST come before storage",
            "ITEM VALIDATION",
            "Convert 1 gold to 10 silver",
            "COMMON STORAGE TRANSACTION ERRORS",
            "Currency deduction without conversion",
            "Wrong action order",
            "Missing currency math",
            "Insufficient funds",
            "gold times 10) + silver + (copper divided by 10)",
            "REJECT the response and explain the proper format"
        ]
        
        missing_patterns = []
        found_patterns = []
        
        for pattern in required_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ Found: '{pattern}'")
            else:
                missing_patterns.append(pattern)
                print(f"❌ Missing: '{pattern}'")
        
        print(f"\nSUMMARY: {len(found_patterns)}/{len(required_patterns)} patterns found")
        
        if missing_patterns:
            print("⚠️  MISSING PATTERNS:")
            for pattern in missing_patterns:
                print(f"   - {pattern}")
        else:
            print("✅ All required patterns found in validation prompt!")
            
        return len(missing_patterns) == 0
        
    except FileNotFoundError:
        print("❌ validation_prompt.txt not found!")
        return False
    except Exception as e:
        print(f"❌ Error reading validation prompt: {e}")
        return False

def check_prompt_consistency():
    """Check that both prompts use consistent terminology and examples"""
    
    print("\n🔍 CHECKING PROMPT CONSISTENCY")
    print("=" * 60)
    
    try:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            system_content = f.read()
        with open("validation_prompt.txt", "r", encoding="utf-8") as f:
            validation_content = f.read()
        
        # Check for consistent examples
        consistency_checks = [
            {
                "name": "Currency conversion rates",
                "pattern": "1 gold = 10 silver = 100 copper",
                "in_system": "1 gold = 10 silver = 100 copper" in system_content,
                "in_validation": "1 gold = 10 silver = 100 copper" in validation_content
            },
            {
                "name": "Example amounts (156 gold)",
                "pattern": "156 gold",
                "in_system": "156 gold" in system_content,
                "in_validation": "156 gold" in validation_content
            },
            {
                "name": "Final amounts (155 gold, 8 silver)",
                "pattern": "155 gold, 8 silver",
                "in_system": "155 gold, 8 silver" in system_content,
                "in_validation": "155 gold, 8 silver" in validation_content
            },
            {
                "name": "Action order requirement",
                "pattern": "updateCharacterInfo.*before.*storage",
                "in_system": "Currency payment must always come before storage" in system_content,
                "in_validation": "updateCharacterInfo) MUST come before storage" in validation_content
            }
        ]
        
        all_consistent = True
        for check in consistency_checks:
            if check["in_system"] and check["in_validation"]:
                print(f"✅ Consistent: {check['name']}")
            else:
                print(f"❌ Inconsistent: {check['name']}")
                print(f"   System: {check['in_system']}")
                print(f"   Validation: {check['in_validation']}")
                all_consistent = False
        
        return all_consistent
        
    except Exception as e:
        print(f"❌ Error checking consistency: {e}")
        return False

def run_integration_verification():
    """Run complete integration verification"""
    
    print("🧪 STORAGE CURRENCY PROMPT INTEGRATION VERIFICATION")
    print("=" * 80)
    
    system_ok = check_system_prompt()
    validation_ok = check_validation_prompt()
    consistency_ok = check_prompt_consistency()
    
    print("\n🎯 OVERALL INTEGRATION STATUS")
    print("=" * 60)
    
    if system_ok and validation_ok and consistency_ok:
        print("✅ INTEGRATION COMPLETE!")
        print("   - System prompt has all required instructions")
        print("   - Validation prompt has all required rules")
        print("   - Both prompts are consistent")
        print("\n🚀 Ready for testing storage currency scenarios!")
        return True
    else:
        print("❌ INTEGRATION INCOMPLETE!")
        if not system_ok:
            print("   - System prompt missing required patterns")
        if not validation_ok:
            print("   - Validation prompt missing required patterns")
        if not consistency_ok:
            print("   - Prompts are inconsistent")
        print("\n⚠️  Fix missing patterns before testing!")
        return False

if __name__ == "__main__":
    success = run_integration_verification()
    
    if success:
        print("\n✅ VERIFICATION COMPLETE - All systems integrated properly!")
        print("\nNext steps:")
        print("1. Run actual game test with storage + currency scenario")
        print("2. Verify DM generates proper two-action sequence") 
        print("3. Verify validation catches common errors")
        print("4. Confirm character data stays consistent")
    else:
        print("\n❌ VERIFICATION FAILED - Fix integration issues first!")
    
    exit(0 if success else 1)