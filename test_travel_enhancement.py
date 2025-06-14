#!/usr/bin/env python3
"""
Test Multi-Area Travel Enhancement

Tests the enhanced travel system to ensure:
1. System prompt contains multi-area travel guidelines
2. Validation prompt enforces multi-area travel rules
3. Examples demonstrate correct vs incorrect multi-area travel
"""

def test_system_prompt_travel_guidelines():
    """Test that system prompt contains multi-area travel guidelines"""
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for key travel sections
    required_sections = [
        "## Multi-Area Travel Guidelines",
        "### LEGITIMATE MULTI-AREA REQUESTS:",
        "### PROCESS FOR MULTI-AREA TRAVEL:",
        "### MULTI-AREA TRAVEL EXAMPLE:",
        "### ANTI-CHEATING SAFEGUARDS:"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    print(f"✓ System Prompt Travel Guidelines Test:")
    if missing_sections:
        print(f"  ❌ Missing sections: {missing_sections}")
        return False
    else:
        print(f"  ✅ All required travel guidelines sections present")
    
    # Check for specific travel patterns
    required_patterns = [
        "Let's go back to town/village/surface",
        "Return to where we started",
        "Previous Visit Requirement",
        "Logical Path Validation",
        "Single Transition"
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"  ❌ Missing travel patterns: {missing_patterns}")
        return False
    else:
        print(f"  ✅ All required travel patterns present")
    
    return True

def test_validation_prompt_travel_enforcement():
    """Test that validation prompt enforces multi-area travel rules"""
    with open("validation_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for travel validation sections
    required_validation = [
        "## MULTI-AREA TRAVEL VALIDATION RULES",
        "### Valid Multi-Area Travel Patterns:",
        "### Invalid Multi-Area Travel Patterns:",
        "### Multi-Area Travel Validation Requirements:",
        "### Example Valid Multi-Area Travel:"
    ]
    
    missing_validation = []
    for section in required_validation:
        if section not in content:
            missing_validation.append(section)
    
    print(f"✓ Validation Prompt Travel Enforcement Test:")
    if missing_validation:
        print(f"  ❌ Missing validation sections: {missing_validation}")
        return False
    else:
        print(f"  ✅ All required travel validation sections present")
    
    # Check for specific validation rules
    key_rules = [
        "INVALID: Multiple transitionLocation actions for single journey",
        "REQUIRED: Single transitionLocation action to final destination",
        "REQUIRED: Narrative description of journey through intermediate areas",
        "VALID: Single transitionLocation to final destination with full journey narrated"
    ]
    
    missing_rules = []
    for rule in key_rules:
        if rule not in content:
            missing_rules.append(rule)
    
    if missing_rules:
        print(f"  ❌ Missing validation rules: {missing_rules}")
        return False
    else:
        print(f"  ✅ All critical travel validation rules present")
    
    return True

def test_travel_examples():
    """Test that validation prompt has correct and incorrect travel examples"""
    with open("validation_prompt.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"✓ Travel Examples Test:")
    
    # Test for valid multi-area travel example
    valid_example_patterns = [
        "// Example 16: CORRECT Multi-Area Travel Implementation",
        "journey back to Harrow's Hollow",
        "past the Gaol's empty cells, up through the Dungeon Entrance",
        '"areaConnectivityId": "HH001"'
    ]
    
    # Test for invalid multi-area travel example  
    invalid_example_patterns = [
        "// Example 17: INVALID Multi-Area Travel - Multiple transitions",
        "// INVALID REASON: Multiple transitionLocation actions for single journey"
    ]
    
    all_patterns = valid_example_patterns + invalid_example_patterns
    missing_patterns = []
    
    for pattern in all_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"  ❌ Missing example patterns: {missing_patterns}")
        return False
    else:
        print(f"  ✅ All travel example patterns present")
        print(f"  ✅ Valid multi-area travel example included")
        print(f"  ✅ Invalid multi-area travel example included")
    
    return True

def run_all_tests():
    """Run all travel enhancement tests"""
    print("="*60)
    print("MULTI-AREA TRAVEL ENHANCEMENT TESTING")
    print("="*60)
    
    tests = [
        ("System Prompt Travel Guidelines", test_system_prompt_travel_guidelines),
        ("Validation Prompt Travel Enforcement", test_validation_prompt_travel_enforcement),
        ("Travel Examples", test_travel_examples)
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
        print("🎉 ALL TESTS PASSED - Multi-area travel enhancement is complete!")
        print("The AI should now handle multi-area travel requests correctly.")
        print("Players can request return journeys with single transitions and")
        print("proper narrative descriptions of the complete journey path.")
    else:
        print("⚠️  SOME TESTS FAILED - Review implementation for missing elements.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()