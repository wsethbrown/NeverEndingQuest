#!/usr/bin/env python3
"""
Create a complete Mythic Bastionland module demonstrating:
1. Realm generation (12x12 hex map with Holdings, Myths, Landmarks)
2. Sites generation (7-point hex method for detailed exploration)
3. Integration of both systems in a playable module
"""

import json
import os
from utils.realm_generator import RealmGenerator
from utils.sites_generator import SiteGenerator
from utils.enhanced_logger import set_script_name, info, debug
from utils.file_operations import safe_write_json

# Set script name for logging
set_script_name("mythic_module_creator")

def create_mythic_bastionland_module():
    """Create a complete Mythic Bastionland module with Realm and Sites"""
    
    module_name = "The Shattered Crown"
    info(f"Creating Mythic Bastionland module: {module_name}")
    
    # Create module directory structure
    module_dir = f"modules/{module_name}"
    os.makedirs(module_dir, exist_ok=True)
    os.makedirs(f"{module_dir}/sites", exist_ok=True)
    
    # Step 1: Generate the Realm (12x12 hex map)
    realm_gen = RealmGenerator(size=12)
    realm_data = realm_gen.generate_realm("The Broken Lands", coastal=True)
    
    # Save realm data
    safe_write_json(realm_data, f"{module_dir}/realm_map.json")
    info(f"Generated realm with {len(realm_data['holdings'])} Holdings and {len(realm_data['myths'])} Myths")
    
    # Step 2: Create Sites for significant Holdings
    site_gen = SiteGenerator()
    sites_created = []
    
    # Create a Site for the Seat of Power (major castle/fortress)
    if realm_data['seat_of_power']:
        seat_site = site_gen.generate_site("The Throne of Echoes", "fortress")
        site_filename = "site_001_throne_of_echoes.json"
        safe_write_json(seat_site, f"{module_dir}/sites/{site_filename}")
        sites_created.append({
            "name": "The Throne of Echoes",
            "filename": site_filename,
            "location": realm_data['seat_of_power'],
            "type": "seat_of_power"
        })
        info("Created Site for Seat of Power: The Throne of Echoes")
    
    # Create Sites for 2-3 other significant Holdings
    holdings_with_sites = []
    for i, holding in enumerate(realm_data['holdings'][:3]):  # First 3 holdings
        if holding['type'] in ['castle', 'fortress', 'tower']:
            site_gen = SiteGenerator()  # Reset for each site
            holding_name = f"The {holding['type'].title()} of Whispers"
            site_data = site_gen.generate_site(holding_name, holding['type'])
            site_filename = f"site_{i+2:03d}_{holding['type']}_whispers.json"
            safe_write_json(site_data, f"{module_dir}/sites/{site_filename}")
            
            holdings_with_sites.append({
                "name": holding_name,
                "filename": site_filename,
                "location": {"x": holding['x'], "y": holding['y']},
                "type": holding['type']
            })
            info(f"Created Site for {holding['type']}: {holding_name}")
    
    sites_created.extend(holdings_with_sites)
    
    # Create Sites for 1-2 significant Myths
    myth_sites = []
    for i, myth in enumerate(realm_data['myths'][:2]):  # First 2 myths
        site_gen = SiteGenerator()  # Reset for each site
        myth_site_name = f"The Ruins of {myth['name']}"
        site_data = site_gen.generate_site(myth_site_name, "tomb")
        site_filename = f"site_myth_{i+1:03d}_{myth['name'].lower().replace(' ', '_')}.json"
        safe_write_json(site_data, f"{module_dir}/sites/{site_filename}")
        
        myth_sites.append({
            "name": myth_site_name,
            "filename": site_filename,
            "location": {"x": myth['x'], "y": myth['y']},
            "type": "myth",
            "myth_name": myth['name']
        })
        info(f"Created Site for Myth: {myth_site_name}")
    
    sites_created.extend(myth_sites)
    
    # Step 3: Create module metadata
    module_metadata = {
        "moduleName": module_name,
        "moduleDescription": "A Mythic Bastionland realm where ancient powers stir beneath a shattered crown, and Knights must navigate both political intrigue and mystical dangers.",
        "moduleMetadata": {
            "author": "NeverEndingQuest AI",
            "version": "1.0.0",
            "gloryRange": {
                "min": 0,
                "max": 5
            },
            "estimatedPlayTime": "4-8 sessions",
            "moduleType": "realm_exploration",
            "_srd_attribution": "Portions derived from SRD 5.2.1, CC BY 4.0"
        },
        "realm": {
            "name": realm_data['name'],
            "size": realm_data['size'],
            "coastal": realm_data['coastal'],
            "total_hexes": realm_data['metadata']['total_hexes'],
            "holdings_count": realm_data['metadata']['holdings_count'],
            "myths_count": realm_data['metadata']['myths_count'],
            "landmarks_count": realm_data['metadata']['landmarks_count']
        },
        "sites": {
            "total_sites": len(sites_created),
            "sites_list": sites_created
        },
        "systemInfo": {
            "realm_generation": "12x12 hex map with Holdings, Myths, and Landmarks",
            "sites_generation": "7-point hex method for detailed exploration",
            "integration": "Sites linked to significant realm locations"
        }
    }
    
    # Save module metadata
    safe_write_json(module_metadata, f"{module_dir}/{module_name.replace(' ', '_')}_module.json")
    
    # Step 4: Create a simple plot structure
    plot_data = {
        "plotTitle": "The Crown's Last Echo",
        "mainObjective": "Discover the fate of the ancient rulers and decide whether to restore or bury their legacy forever.",
        "plotPoints": [
            {
                "id": "PP001",
                "title": "Arrival in the Broken Lands",
                "description": "Knights enter the realm and learn of the shattered crown's legend from local Holdings.",
                "location_type": "realm_exploration",
                "status": "not_started"
            },
            {
                "id": "PP002", 
                "title": "The Seat of Power",
                "description": "Explore the Throne of Echoes and uncover the first pieces of the ancient mystery.",
                "location_type": "site",
                "site_reference": "site_001_throne_of_echoes.json",
                "status": "not_started"
            },
            {
                "id": "PP003",
                "title": "Myths and Legends",
                "description": "Investigate the Myth sites to understand the true nature of the realm's past.",
                "location_type": "site",
                "site_reference": "multiple_myth_sites",
                "status": "not_started"
            },
            {
                "id": "PP004",
                "title": "The Crown's Choice",
                "description": "Make the final decision about the realm's future based on discoveries made.",
                "location_type": "realm_conclusion",
                "status": "not_started"
            }
        ]
    }
    
    # Save plot data
    safe_write_json(plot_data, f"{module_dir}/module_plot.json")
    
    # Step 5: Create summary report
    summary = {
        "module_creation_complete": True,
        "module_name": module_name,
        "files_created": [
            f"{module_name.replace(' ', '_')}_module.json",
            "realm_map.json",
            "module_plot.json",
            f"sites/ directory with {len(sites_created)} Site files"
        ],
        "system_integration": {
            "realm_system": "✓ 12x12 hex map with proper Holdings, Myths, and Landmarks",
            "sites_system": "✓ 7-point hex method with 3 circles, 2 triangles, 1 diamond",
            "plot_integration": "✓ Sites linked to realm locations in plot progression"
        },
        "ready_for_play": True,
        "next_steps": [
            "Load module in NeverEndingQuest",
            "Begin with realm exploration",
            "Use Sites for detailed location exploration",
            "Follow plot progression through connected locations"
        ]
    }
    
    safe_write_json(summary, f"{module_dir}/module_creation_summary.json")
    
    print(f"\n🎉 Mythic Bastionland Module Created Successfully!")
    print(f"📁 Module: {module_name}")
    print(f"🗺️  Realm: {realm_data['name']} ({realm_data['size']}x{realm_data['size']} hexes)")
    print(f"🏰 Holdings: {len(realm_data['holdings'])}")
    print(f"📜 Myths: {len(realm_data['myths'])}")
    print(f"🏛️  Landmarks: {len(realm_data['landmarks'])}")
    print(f"🎯 Sites: {len(sites_created)} detailed exploration areas")
    print(f"📋 Plot Points: {len(plot_data['plotPoints'])}")
    print(f"\n✅ Module ready for play in: modules/{module_name}/")
    
    return module_dir

if __name__ == "__main__":
    create_mythic_bastionland_module()