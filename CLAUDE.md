Always provide a plan before startign to modify code to ensure you are aligned with the user's request.
Beware fo feature creep and don't ad dnew features unless specifically asked or approved. Feature creep is the enemy of shipping software.

# Module-Centric Architecture
This system follows a **Module-Centric Design Philosophy** instead of campaign-based organization:

## Core Principles:
- **Modules as Self-Contained Adventures**: Each module represents a complete, playable adventure
- **No Campaign Dependencies**: Modules can be played independently or linked together
- **Modular Content Organization**: All content (characters, monsters, locations) stored within module directories
- **Unified Path Management**: ModulePathManager provides consistent file access patterns
- **Forward Compatibility**: System designed around modules/ directory structure

## Directory Structure:
```
modules/[module_name]/
├── areas/              # Location files (HH001.json, G001.json)
├── characters/         # Unified player/NPC storage  
├── monsters/           # Module-specific creatures
├── encounters/         # Combat encounters
├── module_plot.json    # Plot progression
├── party_tracker.json  # Party state
└── [module_name]_module.json  # Module metadata
```

## Terminology Standards:
- Use "module" not "campaign" in all new code
- Use "ModulePathManager" for file operations
- Reference "module_data" and "module_name" in function parameters
- File naming: "*_module.json" not "*_campaign.json"

This architecture supports both standalone adventures and linked module series while maintaining clean separation of concerns.

# SRD 5.2.1 Compliance
This project uses SRD content under CC BY 4.0. When coding:
- Use "5th edition" or "5e" instead of "D&D" 
- Add attribution to SRD-derived content: `"_srd_attribution": "Portions derived from SRD 5.2.1, CC BY 4.0"`
- Use generic fantasy settings only

# Tool Command Names
When using command line tools, use these specific command names:
- Use `fdfind` instead of `fd` for file searching
- Use `batcat` instead of `bat` for syntax-highlighted file viewing
- Use `rg` for ripgrep (fast text search)
- All other tools use their standard names: `jq`, `tree`, `fzf`, `black`, `flake8`, `pytest`, `mypy`

Use the Github CLI for this repo as your primary source of open and closed issues.