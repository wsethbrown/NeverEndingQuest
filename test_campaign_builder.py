#!/usr/bin/env python3
"""
Test the campaign builder with context validation
"""

from campaign_builder import CampaignBuilder, BuilderConfig
from datetime import datetime

def test_campaign_builder():
    """Test campaign generation with predefined inputs"""
    
    # Configure test campaign
    config = BuilderConfig(
        campaign_name="Test_Validation",
        num_areas=2,
        locations_per_area=5,
        output_directory=f"./campaigns/Test_Validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Build campaign
    builder = CampaignBuilder(config)
    builder.build_campaign("A cursed castle where an ancient evil awakens")
    
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
    test_campaign_builder()