Always provide a plan before startign to modify code to ensure you are aligned with the user's request.
Beware of feature creep and don't ad dnew features unless specifically asked or approved. Feature creep is the enemy of shipping software.

Don't add emojis or special characters anywhere in the game code.

When planning, always add creating a plan md file in case you get disconnected to the first step of the plan

# Unicode and Special Characters - CRITICAL WARNING
## NEVER USE UNICODE CHARACTERS IN ANY PYTHON CODE
Windows console (cp1252) cannot display Unicode characters and will cause UnicodeEncodeError crashes that break the entire game. This is a CRITICAL requirement.

### BANNED CHARACTERS (NEVER USE THESE):
- ✓ ✗ ✔ ✘ ❌ ✅ (checkmarks/crosses) 
- → ← ↑ ↓ ➜ ⇒ (arrows)
- ● ○ ◆ ◇ ■ □ • ▪ (bullets/shapes)
- 📊 📈 📉 🎉 ⚠️ 🔧 💡 (emojis)
- « » „ " " ' ' (fancy quotes)
- — – (em/en dashes)
- … (ellipsis)
- ANY other non-ASCII character

### REQUIRED ASCII REPLACEMENTS:
- Use [OK] or [PASS] instead of ✓ ✅
- Use [ERROR] or [FAIL] instead of ✗ ❌  
- Use -> or => instead of → ➜
- Use * or - instead of ● •
- Use standard quotes " and ' only
- Use -- instead of — or –
- Use ... instead of …
- Use [WARNING] instead of ⚠️
- Use [INFO] instead of 💡
- Use regular text descriptions instead of ANY emoji

### WHERE THIS APPLIES:
- ALL print() statements
- ALL logging statements (logger.info, logger.debug, etc.)
- ALL string literals that might be displayed
- Test output and debug messages
- Comments can use Unicode but code CANNOT

### EXAMPLES:
```python
# BAD - WILL CRASH:
print("✅ Test passed!")
logger.info("→ Processing file")
print("🎉 Success!")

# GOOD - SAFE:
print("[OK] Test passed!")
logger.info("-> Processing file")
print("Success!")
```

This is not optional - Unicode characters WILL cause the game to crash with encoding errors.

# Schema Validation
Use `python validate_module_files.py` to check schema compatibility after making changes to JSON files or schemas. This ensures all game files remain compatible with their schemas and prevents runtime errors. Aim for 100% validation pass rate.

# Module-Centric Architecture
This system follows a **Module-Centric Design Philosophy** with advanced conversation timeline management:

## Core Principles:
- **Modules as Self-Contained Adventures**: Each module represents a complete, playable adventure
- **Seamless Module Transitions**: Intelligent conversation segmentation preserving chronological adventure history
- **Unified Conversation Timeline**: Hub-and-spoke model maintaining adventure sequence across all modules
- **AI-Powered Context Compression**: Full adventure summaries generated from actual gameplay conversations
- **Smart Boundary Detection**: Two-condition logic for optimal conversation segmentation between modules
- **Automatic Archiving**: Campaign summaries and conversations stored sequentially in dedicated folders
- **Unified Path Management**: ModulePathManager provides consistent file access patterns
- **Forward Compatibility**: System designed around modules/ directory structure with timeline preservation

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

# Module Transition System
Advanced conversation timeline management preserving chronological adventure history across modules:

## Transition Processing Architecture:
- **Immediate Detection**: Module transitions detected in `action_handler.py` when `updatePartyTracker` changes module
- **Marker Insertion**: "Module transition: [from] to [to]" marker inserted immediately at point of module change
- **Post-Processing**: `check_and_process_module_transitions()` in `main.py` handles conversation compression
- **AI Summary Integration**: Loads complete AI-generated summaries from `modules/campaign_summaries/` folder

## Two-Condition Boundary Detection:
1. **Previous Module Transition Exists**: Compress conversation between the two module transitions
2. **No Previous Module Transition**: Compress from after last system message to current transition

## Conversation Segmentation Format:
```json
[
  {main system message},
  {"role": "user", "content": "Module summary: === MODULE SUMMARY ===\n\n[Module_Name]:\n------------------------------\n[Full AI-generated summary]"},
  {"role": "user", "content": "Module transition: [from_module] to [to_module]"},
  {new module conversation...}
]
```

## File Structure Integration:
- **Campaign Archives**: `modules/campaign_archives/[Module_Name]_conversation_[sequence].json`
- **Campaign Summaries**: `modules/campaign_summaries/[Module_Name]_summary_[sequence].json`
- **Sequential Numbering**: Automatic sequence tracking for chronological adventure timeline

This system ensures seamless module transitions while preserving complete adventure context and enabling the hub-and-spoke campaign model.

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