# Character Name Normalization Investigation Report

## Current Behavior Analysis

### Normalization Function Testing with "K'Nolls"
**Test Results:**
- Input: "K'Nolls" → Output: "k_nolls"
- Input: "Mac'Davier" → Output: "mac_davier"
- Input: "O'Brien" → Output: "o_brien"
- Input: "Jean-Claude" → Output: "jean_claude"
- Input: "Mary Sue" → Output: "mary_sue"
- Input: "Sir Galahad the Bold" → Output: "sir_galahad_the_bold"

**Current Normalization Logic (from update_character_info.py):**
1. Convert to lowercase
2. Replace spaces with underscores
3. Replace apostrophes with underscores
4. Replace any non-alphanumeric characters with underscores
5. Remove multiple consecutive underscores
6. Remove leading/trailing underscores

### Character File Structure Analysis

**Schema Fields (char_schema.json):**
- `name` field exists but used for both display and file naming
- No separate field for original/display names currently exists
- Character data structure is unified for players and NPCs

**Current Character Data Example:**
```json
{
  "character_role": "player",
  "name": "Eirik Hearthwise",
  "type": "player",
  // ... other fields
}
```

**File Naming Pattern:**
- Character files are stored as: `{normalized_name}.json`
- Example: "Eirik Hearthwise" → `eirik_hearthwise.json`

### How Names Are Used in Game/AI Systems

**Key Usage Points:**
1. **File Operations**: Normalized names used for file paths and lookups
2. **AI Interactions**: Display names passed to AI for roleplay and conversation
3. **Game Logic**: Character data uses original display names in `name` field
4. **User Interface**: Original names shown to players

## Recommendations

### Option 1: Add Display Name Field (Recommended)

**Implementation:**
1. Add new schema field: `display_name` 
2. Keep existing `name` field for backward compatibility
3. Update normalization workflow to preserve original names

**Schema Changes:**
```json
{
  "display_name": {
    "type": "string",
    "description": "Original character name as entered by user"
  },
  "name": {
    "type": "string", 
    "description": "Normalized name for file operations (backward compatibility)"
  }
}
```

**Benefits:**
- Preserves original character names with apostrophes, spaces, etc.
- Maintains file system compatibility
- Backward compatible with existing characters
- Clear separation of concerns

**Implementation Steps:**
1. Update `char_schema.json` to add `display_name` field
2. Modify `normalize_character_name()` to return both normalized and display names
3. Update character creation/update functions to populate both fields
4. Update AI prompt generation to use `display_name` for roleplay
5. Create migration script for existing characters

### Option 2: Improved Normalization (Alternative)

**Implementation:**
- Enhance normalization to preserve some special characters in filenames
- Use URL encoding or other safe encoding schemes
- Keep original names in `name` field

**Challenges:**
- File system compatibility issues across platforms
- More complex file operations
- Potential encoding problems

### Option 3: Metadata-Based Approach (Complex)

**Implementation:**
- Store mapping between normalized and display names
- Use separate metadata file or registry
- Keep current file naming scheme

**Challenges:**
- Additional complexity
- Risk of metadata/file sync issues
- More maintenance overhead

## Implementation Plan for Recommended Option

### Phase 1: Schema and Core Changes
1. Update character schema to include `display_name` field
2. Modify character creation functions
3. Update character info update functions

### Phase 2: Migration and Compatibility
1. Create migration script for existing characters
2. Update all character loading/saving operations
3. Ensure backward compatibility

### Phase 3: UI and AI Integration
1. Update AI prompts to use display names
2. Modify user interfaces to show original names
3. Update character listing and selection

### Phase 4: Testing and Validation
1. Test with special character names
2. Validate file operations still work
3. Ensure AI interactions use proper names

## Conclusion

The current normalization system works well for file system compatibility but loses important character name authenticity. Adding a `display_name` field is the cleanest solution that preserves user intent while maintaining system functionality. This approach allows "K'Nolls" to be stored as "K'Nolls" in the display field while using "k_nolls.json" for the filename.