#!/usr/bin/env python3
"""
Complex DM Response Validator
Validates that the DM properly handled all requested functions in the complex test
"""

import json
import sys
from typing import Dict, List, Tuple, Any

class ComplexDMValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.required_actions = {
            'updateCharacterInfo': 2,  # Should have at least 2 (giving items, learning spell)
            'updateTime': 1,
            'updatePlot': 1,
            'levelUp': 1
        }
        
    def validate_response(self, response: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate the complete response"""
        # Check structure
        if not isinstance(response, dict):
            self.errors.append("Response is not a valid JSON object")
            return False, self.errors, self.warnings
            
        # Check required fields
        if 'narration' not in response:
            self.errors.append("Missing required field: 'narration'")
        if 'actions' not in response:
            self.errors.append("Missing required field: 'actions'")
            return False, self.errors, self.warnings
            
        # Validate narration
        self._validate_narration(response.get('narration', ''))
        
        # Validate actions
        self._validate_actions(response.get('actions', []))
        
        # Check for Unicode
        self._check_unicode(response)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_narration(self, narration: str):
        """Validate the narration content"""
        if not narration:
            self.errors.append("Narration is empty")
            return
            
        # Check that key elements are mentioned
        expected_elements = [
            ('potion', 'Narration should mention giving potion'),
            ('gold', 'Narration should mention giving gold'),
            ('detect magic', 'Narration should mention Detect Magic spell'),
            ('journal', 'Narration should mention journal/symbol'),
            ('tome', 'Narration should mention magical tome'),
            ('shield', 'Narration should mention Shield spell'),
            ('curse', 'Narration should mention village curse'),
            ('level', 'Narration should mention leveling up or growth')
        ]
        
        narration_lower = narration.lower()
        for keyword, message in expected_elements:
            if keyword not in narration_lower:
                self.warnings.append(f"{message} (keyword: '{keyword}')")
    
    def _validate_actions(self, actions: List[Dict]):
        """Validate all actions"""
        if not actions:
            self.errors.append("No actions provided")
            return
            
        action_counts = {}
        for action in actions:
            if not isinstance(action, dict):
                self.errors.append(f"Invalid action format: {action}")
                continue
                
            action_type = action.get('action')
            if not action_type:
                self.errors.append("Action missing 'action' field")
                continue
                
            # Count actions
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # Validate specific action
            self._validate_specific_action(action)
        
        # Check required actions are present
        for action_type, min_count in self.required_actions.items():
            if action_counts.get(action_type, 0) < min_count:
                self.errors.append(f"Missing or insufficient '{action_type}' actions (expected {min_count}, found {action_counts.get(action_type, 0)})")
    
    def _validate_specific_action(self, action: Dict):
        """Validate individual action parameters"""
        action_type = action['action']
        params = action.get('parameters', {})
        
        if not params:
            self.errors.append(f"Action '{action_type}' missing parameters")
            return
            
        if action_type == 'updateCharacterInfo':
            if 'characterName' not in params:
                self.errors.append("updateCharacterInfo missing 'characterName'")
            if 'changes' not in params:
                self.errors.append("updateCharacterInfo missing 'changes'")
            else:
                # Validate specific changes
                changes = params['changes'].lower()
                character = params.get('characterName', '').lower()
                
                if character == 'norn':
                    if 'removed' not in changes or 'potion' not in changes:
                        self.warnings.append("Norn changes should mention removing potion")
                    if '50 gold' not in changes:
                        self.warnings.append("Norn changes should mention removing 50 gold")
                    if 'shield spell' not in changes:
                        self.warnings.append("Norn changes should mention learning Shield spell")
                        
                elif character == 'elen':
                    if 'added' not in changes or 'potion' not in changes:
                        self.warnings.append("Elen changes should mention adding potion")
                    if '50 gold' not in changes:
                        self.warnings.append("Elen changes should mention adding 50 gold")
                    if 'detect magic' not in changes:
                        self.warnings.append("Elen changes should mention casting Detect Magic")
                        
        elif action_type == 'updateTime':
            if 'hoursToAdd' not in params:
                self.errors.append("updateTime missing 'hoursToAdd'")
            elif params['hoursToAdd'] != 2:
                self.warnings.append(f"Expected 2 hours to pass, got {params['hoursToAdd']}")
                
        elif action_type == 'updatePlot':
            required_fields = ['plotKey', 'description']
            for field in required_fields:
                if field not in params:
                    self.errors.append(f"updatePlot missing '{field}'")
            
            desc = params.get('description', '').lower()
            if 'curse' not in desc:
                self.warnings.append("Plot update should mention curse")
            if 'village' not in desc:
                self.warnings.append("Plot update should mention village")
                
        elif action_type == 'levelUp':
            if 'characterName' not in params:
                self.errors.append("levelUp missing 'characterName'")
            elif params['characterName'].lower() != 'norn':
                self.warnings.append("Level up should be for Norn")
    
    def _check_unicode(self, obj: Any, path: str = ""):
        """Recursively check for Unicode characters"""
        if isinstance(obj, str):
            for i, char in enumerate(obj):
                if ord(char) > 127:
                    self.errors.append(f"Unicode character '{char}' found at {path} position {i}")
        elif isinstance(obj, dict):
            for key, value in obj.items():
                self._check_unicode(key, f"{path}.{key}")
                self._check_unicode(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._check_unicode(item, f"{path}[{i}]")

def main():
    if len(sys.argv) < 2:
        print("Usage: python dm_complex_validator.py <response_file>")
        sys.exit(1)
        
    response_file = sys.argv[1]
    
    try:
        with open(response_file, 'r') as f:
            response = json.load(f)
    except Exception as e:
        print(f"Error loading response file: {e}")
        sys.exit(1)
    
    validator = ComplexDMValidator()
    is_valid, errors, warnings = validator.validate_response(response)
    
    print("=== DM Complex Response Validation ===")
    print(f"Response file: {response_file}")
    print(f"Validation result: {'PASSED' if is_valid else 'FAILED'}")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  [ERROR] {error}")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  [WARN] {warning}")
    
    if is_valid and not warnings:
        print("\nPerfect! All functions handled correctly.")
    
    # Save detailed report
    report = {
        "validation_passed": is_valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "expected_functions": list(validator.required_actions.keys()),
        "validation_criteria": [
            "All required actions present",
            "Proper parameter structure",
            "No Unicode characters",
            "Narrative covers all elements",
            "Inventory changes tracked properly"
        ]
    }
    
    report_file = response_file.replace('.json', '_validation_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()