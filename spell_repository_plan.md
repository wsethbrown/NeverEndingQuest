# Spell Repository Creation Plan

## Project Overview
Creating a comprehensive spell repository with full descriptions and metadata by extracting spell names from `leveling_info.txt` and using ChatGPT Mini API to populate detailed information for each spell.

## Progress Tracking

### Phase 1: Data Extraction & Setup
- [ ] Create plan document (spell_repository_plan.md)
- [ ] Extract unique spells from leveling_info.txt
- [ ] Create build_spell_repository.py script
- [ ] Initialize spell_repository.json with base structure

### Phase 2: Automated Population
- [ ] Implement batch processing system
- [ ] Set up API integration with GPT-4.1-mini
- [ ] Add progressive saving after each spell
- [ ] Implement error handling and retry logic
- [ ] Add progress tracking and logging

### Phase 3: Quality Assurance
- [ ] Validate all spells have complete data
- [ ] Check format consistency
- [ ] Verify SRD compliance and attribution
- [ ] Detect and resolve duplicates

## Spell Extraction Status

### Class Lists to Process:
- [ ] Bard Spells (Cantrips + 1st-5th level)
- [ ] Cleric Spells (Cantrips + 1st-5th level)
- [ ] Druid Spells (2nd-5th level - partial in file)
- [ ] Paladin Spells (1st-5th level)
- [ ] Ranger Spells (1st-5th level)
- [ ] Sorcerer Spells (Cantrips + 1st-5th level)
- [ ] Warlock Spells (Cantrips + 1st-5th level)
- [ ] Wizard Spells (Cantrips + 1st-5th level)

### Estimated Totals:
- **Cantrips**: ~15-20 unique spells
- **1st Level**: ~50-60 unique spells
- **2nd Level**: ~40-50 unique spells
- **3rd Level**: ~30-40 unique spells
- **4th Level**: ~20-30 unique spells
- **5th Level**: ~20-30 unique spells
- **Total Estimated**: ~200-250 unique spells

## API Usage Plan

### Model Configuration:
- **Model**: gpt-4.1-mini-2025-04-14 (from config.py)
- **Batch Size**: 5-10 spells per API call for efficiency
- **Rate Limiting**: Implement delays between batches if needed
- **Error Handling**: Retry failed requests up to 3 times

### Cost Estimation:
- Mini model is cost-effective for this bulk processing
- Estimated token usage: ~500-1000 tokens per spell
- Total estimated cost: $5-15 for complete repository

## Data Structure Design

```json
{
  "spell_name_key": {
    "name": "Actual Spell Name",
    "level": 0-9,
    "school": "Evocation|Divination|etc",
    "casting_time": "1 action|1 bonus action|etc",
    "range": "Self|Touch|30 feet|etc",
    "components": {
      "verbal": true/false,
      "somatic": true/false,
      "material": true/false,
      "materials": "specific components if any"
    },
    "duration": "Instantaneous|Concentration, up to 1 minute|etc",
    "description": "Full spell description text",
    "higher_levels": "Scaling at higher levels (if applicable)",
    "classes": ["Bard", "Cleric", "etc"],
    "ritual": true/false,
    "concentration": true/false,
    "_srd_attribution": "Portions derived from SRD 5.2.1, CC BY 4.0"
  }
}
```

## File Outputs

1. **spell_repository.json** - Complete spell database
2. **build_spell_repository.py** - Processing script
3. **spell_extraction_log.txt** - Processing log
4. **spell_repository_backup.json** - Backup copy

## Safety Measures

- Save after each successful spell lookup
- Create backup before major processing steps
- Log all API calls and responses
- Resume capability if interrupted
- Validate JSON structure continuously

## Usage After Completion

The completed repository will be used as a lookup system:

```python
import json

# Load spell repository
with open('spell_repository.json', 'r') as f:
    spells = json.load(f)

# Look up a spell
fireball = spells.get('fireball', {})
print(f"Description: {fireball.get('description', 'Not found')}")
```

## Timeline

- **Setup**: 30 minutes
- **Processing**: 2-3 hours (API dependent)
- **Validation**: 30 minutes
- **Total**: 3-4 hours

---

*Started: 2025-06-28*
*Status: In Progress*