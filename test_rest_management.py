#!/usr/bin/env python3
"""
Test Rest Management Implementation

Tests the enhanced rest management system to ensure:
1. System prompt provides comprehensive rest guidelines
2. Validation prompt correctly enforces rest rules
3. Class-specific recovery rules are accurately implemented
"""

def test_system_prompt_rest_content():
    """Test that system prompt contains comprehensive rest guidelines"""
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for key rest management sections
    required_sections = [
        "## Rest Management Rules (D&D 5e)",
        "### Short Rest (1 hour minimum):",
        "### Long Rest (8 hours minimum):",
        "### Class-Specific Rest Recovery Rules:",
        "### Rest Implementation Guidelines:",
        "### Rest Validation Checklist:"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    print(f"✓ System Prompt Test Results:")
    if missing_sections:
        print(f"  ❌ Missing sections: {missing_sections}")
        return False
    else:
        print(f"  ✅ All required rest management sections present")
    
    # Check for specific class rules
    required_classes = [
        "**FIGHTER:**", "**RANGER:**", "**WIZARD:**", "**WARLOCK:**",
        "**SORCERER:**", "**CLERIC:**", "**PALADIN:**", "**BARD:**",
        "**BARBARIAN:**", "**MONK:**", "**DRUID:**"
    ]
    
    missing_classes = []
    for class_name in required_classes:
        if class_name not in content:
            missing_classes.append(class_name)
    
    if missing_classes:
        print(f"  ❌ Missing class rules: {missing_classes}")
        return False
    else:
        print(f"  ✅ All D&D classes have specific rest rules")
    
    return True

def test_validation_prompt_rest_enforcement():
    """Test that validation prompt enforces rest rules"""
    with open("validation_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for rest validation sections
    required_validation = [
        "## REST MANAGEMENT VALIDATION RULES",
        "### Short Rest Validation (1 hour):",
        "### Long Rest Validation (8 hours):",
        "### Class-Specific Recovery Validation:",
        "### Rest Validation Failures:"
    ]
    
    missing_validation = []
    for section in required_validation:
        if section not in content:
            missing_validation.append(section)
    
    print(f"✓ Validation Prompt Test Results:")
    if missing_validation:
        print(f"  ❌ Missing validation sections: {missing_validation}")
        return False
    else:
        print(f"  ✅ All required rest validation sections present")
    
    # Check for specific validation rules
    key_rules = [
        "INVALID: Spell slot recovery for most classes (only Warlocks",
        "REQUIRED: updateTime action with timeEstimate: 60",
        "REQUIRED: updateTime action with timeEstimate: 480",
        "**WARLOCK:** Short rest = ALL spell slots recover",
        "**ALL OTHER CLASSES:** Short rest = NO spell slot recovery"
    ]
    
    missing_rules = []
    for rule in key_rules:
        if rule not in content:
            missing_rules.append(rule)
    
    if missing_rules:
        print(f"  ❌ Missing validation rules: {missing_rules}")
        return False
    else:
        print(f"  ✅ All critical rest validation rules present")
    
    return True

def test_class_specific_rules():
    """Test specific class rest recovery rules"""
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"✓ Class-Specific Rules Test Results:")
    
    # Test key class distinctions
    test_cases = [
        ("Warlock short rest spell recovery", r"\*\*WARLOCK:\*\*.*Short Rest: ALL spell slots recover"),
        ("Wizard Arcane Recovery", r"\*\*WIZARD:\*\*.*Arcane Recovery.*half wizard level"),
        ("Fighter Second Wind", r"\*\*FIGHTER:\*\*.*Second Wind.*Action Surge"),
        ("Monk Ki recovery", r"\*\*MONK:\*\*.*Ki points recharge"),
        ("Rangers no short rest slots", r"\*\*RANGER:\*\*.*Short Rest: No spell slot recovery")
    ]
    
    import re
    all_passed = True
    
    for test_name, pattern in test_cases:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            print(f"  ✅ {test_name}")
        else:
            print(f"  ❌ {test_name} - pattern not found")
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all rest management tests"""
    print("="*60)
    print("REST MANAGEMENT IMPLEMENTATION TESTING")
    print("="*60)
    
    tests = [
        ("System Prompt Content", test_system_prompt_rest_content),
        ("Validation Prompt Enforcement", test_validation_prompt_rest_enforcement),
        ("Class-Specific Rules", test_class_specific_rules)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*60)
    print("FINAL TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Rest management implementation is complete!")
        print("The AI should now handle rest mechanics correctly with proper validation.")
    else:
        print("⚠️  SOME TESTS FAILED - Review implementation for missing elements.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()