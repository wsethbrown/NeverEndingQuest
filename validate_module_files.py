#!/usr/bin/env python3
"""
Comprehensive Module File Validation Script

This script validates all game files in a module directory against their corresponding schemas.
It provides detailed reporting on validation passes, failures, and missing schemas.

Supports module-centric architecture for 5th edition content validation.
Portions derived from SRD 5.2.1, licensed under CC BY 4.0.
"""

import json
import os
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
from collections import defaultdict
from datetime import datetime
import sys


class ModuleValidator:
    """Validates all module files against their schemas"""
    
    def __init__(self, module_path, schema_dir):
        self.module_path = Path(module_path)
        self.schema_dir = Path(schema_dir)
        self.results = defaultdict(lambda: {"files": [], "passed": 0, "failed": 0, "errors": []})
        self.schemas = {}
        
    def load_schemas(self):
        """Load all available schemas"""
        schema_mappings = {
            "module": "module_schema.json",
            "area": "locationfile_schema.json",  # Area files use locationfile schema
            "character": "char_schema.json",
            "monster": "mon_schema.json",  # Monsters have their own schema
            "map": "map_schema.json",
            "plot": "plot_schema.json",
            "party": "party_schema.json",
            "encounter": "encounter_schema.json",
            "plan": "plan_schema.json",
            "journal": "journal_schema.json",
            "random_encounter": "random_encounter_schema.json"
        }
        
        print("Loading schemas...")
        for file_type, schema_file in schema_mappings.items():
            schema_path = self.schema_dir / schema_file
            if schema_path.exists():
                try:
                    with open(schema_path, 'r') as f:
                        self.schemas[file_type] = json.load(f)
                    print(f"  ✓ Loaded {file_type} schema from {schema_file}")
                except Exception as e:
                    print(f"  ✗ Failed to load {file_type} schema: {e}")
            else:
                print(f"  - Schema not found: {schema_file}")
                
    def validate_file(self, file_path, schema_type):
        """Validate a single file against its schema"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if schema_type not in self.schemas:
                return False, f"No schema available for type: {schema_type}"
                
            # Create validator to get better error messages
            validator = Draft7Validator(self.schemas[schema_type])
            errors = list(validator.iter_errors(data))
            
            if errors:
                error_messages = []
                for error in errors:
                    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                    error_messages.append(f"{path}: {error.message}")
                return False, "; ".join(error_messages[:3])  # Limit to first 3 errors
            
            return True, None
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error: {str(e)}"
            
    def validate_module_files(self):
        """Validate the main module file"""
        module_files = list(self.module_path.glob("*_module.json"))
        
        for file_path in module_files:
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                continue
                
            success, error = self.validate_file(file_path, "module")
            self.results["module"]["files"].append(str(file_path.name))
            
            if success:
                self.results["module"]["passed"] += 1
            else:
                self.results["module"]["failed"] += 1
                self.results["module"]["errors"].append(f"{file_path.name}: {error}")
                
    def validate_area_files(self):
        """Validate area/location files"""
        # Area files are the JSON files in the root that match location patterns
        area_patterns = ["G001.json", "HH001.json", "SK001.json", "TBM001.json", "TCD001.json"]
        
        for pattern in area_patterns:
            file_path = self.module_path / pattern
            if file_path.exists() and not any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                success, error = self.validate_file(file_path, "area")
                self.results["area"]["files"].append(pattern)
                
                if success:
                    self.results["area"]["passed"] += 1
                else:
                    self.results["area"]["failed"] += 1
                    self.results["area"]["errors"].append(f"{pattern}: {error}")
                    
    def validate_character_files(self):
        """Validate character files"""
        char_dir = self.module_path / "characters"
        if not char_dir.exists():
            return
            
        for file_path in char_dir.glob("*.json"):
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp", "copy"]):
                continue
                
            success, error = self.validate_file(file_path, "character")
            self.results["character"]["files"].append(file_path.name)
            
            if success:
                self.results["character"]["passed"] += 1
            else:
                self.results["character"]["failed"] += 1
                self.results["character"]["errors"].append(f"{file_path.name}: {error}")
                
    def validate_monster_files(self):
        """Validate monster files"""
        monster_dir = self.module_path / "monsters"
        if not monster_dir.exists():
            return
            
        for file_path in monster_dir.glob("*.json"):
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                continue
                
            success, error = self.validate_file(file_path, "monster")
            self.results["monster"]["files"].append(file_path.name)
            
            if success:
                self.results["monster"]["passed"] += 1
            else:
                self.results["monster"]["failed"] += 1
                self.results["monster"]["errors"].append(f"{file_path.name}: {error}")
                
    def validate_map_files(self):
        """Validate map files"""
        map_files = list(self.module_path.glob("map_*.json"))
        
        for file_path in map_files:
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                continue
                
            success, error = self.validate_file(file_path, "map")
            self.results["map"]["files"].append(file_path.name)
            
            if success:
                self.results["map"]["passed"] += 1
            else:
                self.results["map"]["failed"] += 1
                self.results["map"]["errors"].append(f"{file_path.name}: {error}")
                
    def validate_plot_files(self):
        """Validate plot files"""
        plot_files = list(self.module_path.glob("*_plot.json"))
        
        for file_path in plot_files:
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                continue
                
            success, error = self.validate_file(file_path, "plot")
            self.results["plot"]["files"].append(file_path.name)
            
            if success:
                self.results["plot"]["passed"] += 1
            else:
                self.results["plot"]["failed"] += 1
                self.results["plot"]["errors"].append(f"{file_path.name}: {error}")
                
    def validate_party_tracker(self):
        """Validate party tracker file"""
        party_file = self.module_path / "party_tracker.json"
        
        if party_file.exists():
            success, error = self.validate_file(party_file, "party")
            self.results["party"]["files"].append("party_tracker.json")
            
            if success:
                self.results["party"]["passed"] += 1
            else:
                self.results["party"]["failed"] += 1
                self.results["party"]["errors"].append(f"party_tracker.json: {error}")
                
    def validate_module_context(self):
        """Skip validation for module_context.json as it's an internal tracking file"""
        context_file = self.module_path / "module_context.json"
        
        if context_file.exists():
            # Mark as passed since it's an internal file that doesn't need validation
            self.results["module_context"]["files"].append("module_context.json")
            self.results["module_context"]["passed"] += 1
            print("  - Skipping module_context.json (internal tracking file)")
                
    def validate_encounter_files(self):
        """Validate encounter files"""
        encounter_dir = self.module_path / "encounters"
        if not encounter_dir.exists():
            return
            
        for file_path in encounter_dir.glob("*.json"):
            if any(part in str(file_path) for part in ["_BU", ".bak", ".backup", ".tmp"]):
                continue
                
            success, error = self.validate_file(file_path, "encounter")
            self.results["encounter"]["files"].append(file_path.name)
            
            if success:
                self.results["encounter"]["passed"] += 1
            else:
                self.results["encounter"]["failed"] += 1
                self.results["encounter"]["errors"].append(f"{file_path.name}: {error}")
                
    def run_validation(self):
        """Run all validations"""
        print(f"\nValidating module: {self.module_path}")
        print("=" * 80)
        
        self.load_schemas()
        print("\nRunning validations...")
        
        # Run all validation methods
        self.validate_module_files()
        self.validate_area_files()
        self.validate_character_files()
        self.validate_monster_files()
        self.validate_map_files()
        self.validate_plot_files()
        self.validate_party_tracker()
        self.validate_module_context()
        self.validate_encounter_files()
        
    def print_report(self):
        """Print comprehensive validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        print(f"Module: {self.module_path.name}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n")
        
        # Summary statistics
        total_passed = sum(r["passed"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        total_files = total_passed + total_failed
        
        print(f"SUMMARY: {total_files} files validated")
        print(f"  ✓ Passed: {total_passed}")
        print(f"  ✗ Failed: {total_failed}")
        if total_files > 0:
            print(f"  Success Rate: {(total_passed/total_files)*100:.1f}%")
        print("\n")
        
        # Detailed results by file type
        print("DETAILED RESULTS BY FILE TYPE:")
        print("-" * 80)
        
        file_type_order = ["module", "area", "character", "monster", "map", "plot", 
                          "party", "module_context", "encounter"]
        
        for file_type in file_type_order:
            if file_type not in self.results or not self.results[file_type]["files"]:
                continue
                
            result = self.results[file_type]
            total = result["passed"] + result["failed"]
            
            print(f"\n{file_type.upper()} FILES ({total} files)")
            print(f"  Status: {'✓ ALL PASSED' if result['failed'] == 0 else '✗ FAILURES DETECTED'}")
            print(f"  Passed: {result['passed']}/{total}")
            
            if result["failed"] > 0:
                print(f"  Failed: {result['failed']}/{total}")
                print("  Errors:")
                for error in result["errors"][:5]:  # Show first 5 errors
                    print(f"    - {error}")
                if len(result["errors"]) > 5:
                    print(f"    ... and {len(result['errors']) - 5} more errors")
                    
        # Schema recommendations
        print("\n" + "-" * 80)
        print("SCHEMA RECOMMENDATIONS:")
        
        missing_schemas = []
        needs_refactoring = []
        
        # Check for missing schemas
        if "module_context" in self.results and self.results["module_context"]["failed"] > 0:
            for error in self.results["module_context"]["errors"]:
                if "No schema available" in error:
                    missing_schemas.append("module_context_schema.json")
                    
        # Check for high failure rates indicating schema issues
        for file_type, result in self.results.items():
            if result["files"] and result["failed"] > 0:
                failure_rate = result["failed"] / (result["passed"] + result["failed"])
                if failure_rate > 0.5:  # More than 50% failure rate
                    needs_refactoring.append(file_type)
                    
        if missing_schemas:
            print("\nMissing Schemas:")
            for schema in missing_schemas:
                print(f"  - {schema}")
                
        if needs_refactoring:
            print("\nSchemas Needing Review (high failure rate):")
            for file_type in needs_refactoring:
                schema_name = self.get_schema_name(file_type)
                print(f"  - {schema_name} ({file_type} files)")
                
        if not missing_schemas and not needs_refactoring:
            print("\n  ✓ All required schemas are present and functioning well")
            
        print("\n" + "=" * 80)
        
    def get_schema_name(self, file_type):
        """Get the schema filename for a file type"""
        mapping = {
            "module": "module_schema.json",
            "area": "locationfile_schema.json",
            "character": "char_schema.json",
            "monster": "mon_schema.json",
            "map": "map_schema.json",
            "plot": "plot_schema.json",
            "party": "party_schema.json",
            "encounter": "encounter_schema.json"
        }
        return mapping.get(file_type, f"{file_type}_schema.json")
        
    def save_report(self, output_file=None):
        """Save validation report to JSON file"""
        if not output_file:
            output_file = self.module_path / "validation_report.json"
            
        report = {
            "module": str(self.module_path.name),
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": sum(len(r["files"]) for r in self.results.values()),
                "total_passed": sum(r["passed"] for r in self.results.values()),
                "total_failed": sum(r["failed"] for r in self.results.values())
            },
            "results": dict(self.results)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: {output_file}")


def main():
    """Main execution function"""
    # Set paths
    module_path = "/mnt/c/dungeon_master_v1/modules/Keep_of_Doom"
    schema_dir = "/mnt/c/dungeon_master_v1"
    
    # Create validator and run
    validator = ModuleValidator(module_path, schema_dir)
    validator.run_validation()
    validator.print_report()
    validator.save_report()
    
    # Return exit code based on failures
    total_failed = sum(r["failed"] for r in validator.results.values())
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())