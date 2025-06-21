# Module Travel Investigation Plan

## Objective
Investigate why module travel isn't working - the AI only moves within the current module instead of transitioning to new modules.

## Investigation Steps

1. **Examine Module Transition Detection**
   - Look at how cross-module transitions are detected
   - Check the logic for "Cross-area transition: False" in debug logs
   - Understand within-module vs cross-module transition logic

2. **Check Module Travel Handlers**
   - Find action handlers for module travel
   - Look for specific action types related to module transitions
   - Check if there are travel or module_travel action handlers

3. **Analyze Module Context for AI**
   - How does the AI know about available modules?
   - What context is provided about other modules?
   - Check system prompts for module travel instructions

4. **Review Module Stitcher & Campaign Manager**
   - Examine module stitching functionality
   - Check how modules are linked together
   - Look at campaign management for module transitions

5. **Debug Location Transition System**
   - Trace the location transition flow
   - Find where "Cross-area transition" is determined
   - Check for bugs in transition detection

## Key Files to Examine
- Module stitcher implementation
- Campaign/module manager
- Action handlers (especially travel-related)
- Location transition logic
- System prompt generation for module context