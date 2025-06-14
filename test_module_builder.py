#!/usr/bin/env python3
"""
Test the module builder with context validation
"""

from module_builder import ModuleBuilder, BuilderConfig
from datetime import datetime

def test_module_builder():
    """Test module generation with predefined inputs"""
    
    # Configure test module
    config = BuilderConfig(
        module_name="Test_Validation",
        num_areas=2,
        locations_per_area=5,
        output_directory=f"./modules/Test_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Build module
    builder = ModuleBuilder(config)
    builder.build_module("A cursed castle where an ancient evil awakens")
    
    print("\n=== Test Results ===")
    print(f"Output directory: {config.output_directory}")
    
    # Check validation results
    if builder.context.validation_issues:
        print(f"\nValidation issues found: {len(builder.context.validation_issues)}")
        for issue in builder.context.validation_issues:
            print(f"  - {issue}")
    else:
        print("\nAll validation checks passed!")
    
    print(f"\nGenerated:")
    print(f"  - Areas: {len(builder.context.areas)}")
    print(f"  - Locations: {len(builder.context.locations)}")
    print(f"  - NPCs: {len(builder.context.npcs)}")
    print(f"  - Plot points: {len(builder.context.plot_scopes)}")

if __name__ == "__main__":
    test_module_builder()