# System Prompt Test Scenarios

## Prompt Comparison Overview
- **Current Prompt**: 1,159 lines, 65,823 characters (system_prompt.txt)
- **New Truncated Prompt**: 117 lines, 5,429 characters (claude.txt)
- **Size Reduction**: ~92% smaller (12x reduction)

## Key Differences Analysis

### Current Prompt Characteristics
- Extremely detailed with extensive examples
- Multiple sections covering every possible scenario
- Heavy emphasis on specific formatting rules
- Extensive action parameter documentation
- Many redundant explanations and examples

### New Truncated Prompt Characteristics
- Concise, focused on essential rules only
- JSON structure clearly defined with template
- Core rules organized by functional area
- Reference tables for class-specific mechanics
- Single example for storage interaction

## Test Scenarios

### Test 1: Basic JSON Structure
**Objective**: Verify both prompts produce valid JSON responses
**Input**: "What do I see around me?"
**Expected**: Valid JSON with narration field and appropriate actions
**Validation**: JSON schema compliance, structure correctness

### Test 2: Multiple Actions
**Objective**: Test handling of scenarios requiring multiple actions
**Input**: "I take a short rest and then move to the next room"
**Expected**: JSON with updateTime, updateCharacterInfo, and transitionLocation actions
**Validation**: All required actions present, proper sequencing

### Test 3: Combat Initiation
**Objective**: Test combat encounter creation
**Input**: "I attack the goblin with my sword"
**Expected**: createEncounter action with proper parameters, no narration in that action
**Validation**: Action structure, parameter completeness

### Test 4: Inventory Management
**Objective**: Test character update functionality
**Input**: "I pick up the gold coins and healing potion"
**Expected**: updateCharacterInfo with inventory additions
**Validation**: Proper inventory tracking, item descriptions

### Test 5: Storage Interaction
**Objective**: Test new storage system functionality
**Input**: "I store my extra arrows in the chest"
**Expected**: storageInteraction with natural language description
**Validation**: Action parameters, description quality

### Test 6: Time Management
**Objective**: Test time tracking reliability
**Input**: "I carefully examine the room for traps"
**Expected**: updateTime action with appropriate time estimate
**Validation**: Realistic time estimates, action inclusion

### Test 7: Location Transition
**Objective**: Test movement between locations
**Input**: "I go through the door to the north"
**Expected**: transitionLocation with valid location ID
**Validation**: Proper location ID usage, no invented IDs

### Test 8: Repetition Test A
**Objective**: Test for repetitive patterns (Run 1)
**Input**: "Describe the tavern"
**Expected**: Unique narrative description
**Validation**: Baseline description for comparison

### Test 9: Repetition Test B
**Objective**: Test for repetitive patterns (Run 2)
**Input**: "Describe the tavern" (same as Test 8)
**Expected**: Different narrative description with similar content
**Validation**: Compare against Test 8 for repetitive phrases

### Test 10: Complex Scenario
**Objective**: Test handling of complex multi-step interactions
**Input**: "I ask the innkeeper about rumors while ordering food and ale"
**Expected**: Rich dialogue, NPC interaction, possible updateCharacterInfo for purchases
**Validation**: Story coherence, action appropriateness

## Validation Criteria

### Quantitative Metrics
1. **JSON Validity**: Pass/Fail for each response
2. **Action Accuracy**: Correct action types used
3. **Parameter Completeness**: Required parameters present
4. **Schema Compliance**: Matches expected response template

### Qualitative Metrics
1. **Narrative Quality**: Descriptiveness and immersion
2. **Repetition Analysis**: Unique phrases vs repeated patterns
3. **Story Coherence**: Logical flow and consistency
4. **NPC Characterization**: Distinct personality voices

## Testing Protocol

### Phase A: Current Prompt Testing
1. Run all 10 test scenarios with current system_prompt.txt
2. Collect all AI responses
3. Run validation checks on responses
4. Document any issues or repetitive patterns

### Phase B: New Prompt Testing
1. Replace system_prompt.txt with content from claude.txt
2. Run identical 10 test scenarios
3. Collect all AI responses
4. Run validation checks on responses
5. Document differences in behavior

### Phase C: Comparative Analysis
1. Compare JSON validity rates
2. Analyze action accuracy differences
3. Evaluate narrative variety and quality
4. Identify repetitive patterns in each set
5. Assess overall reliability

## Expected Outcomes

### Hypothesis: New Truncated Prompt Will...
- Maintain JSON structure compliance
- Reduce repetitive narrative patterns
- Provide more varied responses
- Maintain core functionality
- Potentially improve response creativity

### Risk Areas to Monitor
- Loss of specific rule adherence
- Missing critical action types
- Reduced parameter accuracy
- Degraded story quality

## Implementation Notes
- Save all test responses for analysis
- Use consistent testing environment
- Document exact timing of tests
- Preserve original system prompt as backup
- Plan for quick rollback if needed

## Success Criteria
- New prompt achieves ≥95% JSON validity
- Reduced repetitive phrases by ≥30%
- Maintains all critical action types
- No significant degradation in story quality
- Overall system reliability maintained or improved