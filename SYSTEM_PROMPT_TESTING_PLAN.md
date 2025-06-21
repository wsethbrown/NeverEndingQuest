# System Prompt Testing Plan

## Objective
Compare the performance and reliability of the new truncated system prompt (stored in claude.txt) against the existing system prompt to determine which provides better AI behavior and validation results.

## Background
The current system has been showing repetitive narrative patterns which may lead to AI training issues. A new, highly truncated system prompt has been developed and stored in claude.txt that may provide more varied and reliable outputs.

## Testing Plan Overview

### Phase 1: Preparation and Analysis
1. **Document Creation** ✅
   - Create this testing plan document for reference
   
2. **Prompt Examination**
   - Examine the new truncated prompt in claude.txt
   - Identify current system prompt location (likely system_prompt.txt)
   - Create backup of existing system prompt
   - Document key differences between prompts

3. **Test Environment Setup**
   - Ensure validation tools are working
   - Prepare test scenarios that exercise key AI behaviors
   - Set up result collection methodology

### Phase 2: Test Scenario Design
Design test scenarios that evaluate:

#### Core Functionality Tests
- **JSON Response Format**: Ensure proper JSON structure
- **Action Generation**: Verify correct action parameters
- **Time Management**: Test updateTime action reliability
- **Location Transitions**: Test transitionLocation behavior
- **Character Updates**: Test updateCharacterInfo accuracy
- **Storage Interactions**: Test storageInteraction functionality

#### Narrative Quality Tests
- **Dialogue Variety**: Test for repetitive phrases/patterns
- **Description Uniqueness**: Evaluate location/character descriptions
- **Plot Progression**: Test story coherence and advancement
- **NPC Behavior**: Evaluate NPC personality consistency

#### Reliability Tests
- **Schema Validation**: Run validator on AI outputs
- **Error Handling**: Test response to invalid inputs
- **Edge Cases**: Test boundary conditions
- **Consistency**: Multiple runs of same scenario

### Phase 3: Implementation and Testing

#### Test Execution Process
1. **Baseline Testing** (Current Prompt)
   - Run test scenarios with existing system prompt
   - Collect AI responses and validation results
   - Document any repetitive patterns or issues

2. **New Prompt Testing** (Truncated Prompt)
   - Replace system prompt with claude.txt version
   - Run identical test scenarios
   - Collect AI responses and validation results
   - Document differences in behavior

3. **Comparative Analysis**
   - Compare validation success rates
   - Analyze narrative variety and quality
   - Evaluate reliability and consistency
   - Document performance differences

### Phase 4: Data Collection and Metrics

#### Quantitative Metrics
- **Validation Success Rate**: Percentage of valid JSON responses
- **Action Accuracy**: Correct action types and parameters
- **Schema Compliance**: Adherence to response template
- **Response Time**: If measurable, AI response latency

#### Qualitative Metrics
- **Narrative Variety**: Unique phrases/descriptions count
- **Repetition Analysis**: Identify repeated patterns
- **Story Coherence**: Plot progression quality
- **Character Consistency**: NPC behavior reliability

### Phase 5: Results Analysis and Recommendations

#### Expected Outcomes
- Clear winner between prompts based on metrics
- Specific recommendations for prompt improvement
- Identification of any issues requiring fixes
- Decision on which prompt to use going forward

#### Documentation Requirements
- Detailed comparison report
- Example outputs from both prompts
- Validation results summary
- Implementation recommendations

## Test Scenarios

### Scenario 1: Basic Interaction
**Setup**: Player asks "What do I see around me?"
**Expected**: Proper JSON with narration and appropriate actions

### Scenario 2: Combat Initiation
**Setup**: Player attacks a monster
**Expected**: createEncounter action with proper parameters

### Scenario 3: Item Management
**Setup**: Player picks up an item
**Expected**: updateCharacterInfo with inventory changes

### Scenario 4: Location Movement
**Setup**: Player moves to adjacent room
**Expected**: transitionLocation with valid location ID

### Scenario 5: Storage Usage
**Setup**: Player stores items in container
**Expected**: storageInteraction with proper description

### Scenario 6: Time-Consuming Activity
**Setup**: Player takes a short rest
**Expected**: updateTime action with appropriate time estimate

### Scenario 7: Repetition Test
**Setup**: Repeat same scenario multiple times
**Expected**: Varied narrative responses, consistent actions

## Risk Mitigation
- **Backup Strategy**: Keep original system prompt as backup
- **Rollback Plan**: Quick procedure to revert if new prompt fails
- **Validation Safety**: Run validator on all test outputs
- **Documentation**: Comprehensive record of all changes

## Success Criteria
- New prompt shows equal or better validation success rate
- Reduced repetitive patterns in narrative output
- Maintained or improved action accuracy
- Overall system reliability maintained or improved

## Implementation Timeline
1. **Preparation**: 30 minutes - setup and analysis
2. **Testing**: 60 minutes - run scenarios on both prompts  
3. **Analysis**: 30 minutes - compare results and document findings
4. **Decision**: 15 minutes - choose prompt and implement

## Files Involved
- `claude.txt` - New truncated system prompt
- `system_prompt.txt` - Current system prompt (likely location)
- `validate_module_files.py` - Validation tool
- Test output files and comparison results

## Next Steps After Testing
Based on results, proceed to narrative uniqueness evaluation using the better-performing system prompt.