# Cumulative Adventure Summary Design

## Current System Flow:
1. Player leaves location → adv_summary.py runs
2. Creates detailed summary → saves to journal.json
3. Also saves to location's adventureSummary field
4. Conversation history uses separate 9-message summarization

## Proposed New System:

### 1. Remove the 9-message summarization entirely
- Delete `summarize_conversation()` and `needs_summarization()` from main.py
- No more incremental compression during gameplay

### 2. Build Cumulative Adventure Summary
When leaving a location:
```python
# In adv_summary.py or new function
def build_cumulative_summary():
    # Load journal.json
    journal_entries = load_json_file("journal.json")
    
    # Build cumulative narrative from all entries
    cumulative_summary = "Adventure Summary:\n\n"
    
    for entry in journal_entries:
        # Add each location's summary with context
        cumulative_summary += f"[{entry['date']} - {entry['time']} - {entry['location']}]\n"
        cumulative_summary += entry['summary'] + "\n\n"
    
    return cumulative_summary
```

### 3. Insert as Single User Message
After each location transition:
```python
# Replace old summarization with:
conversation_history = [
    {"role": "system", "content": main_system_prompt},
    {"role": "user", "content": build_cumulative_summary()},
    # ... recent messages from current location only
]
```

### 4. Trim Old Messages on Transition
When leaving a location:
- Keep only system prompts
- Keep the cumulative summary
- Keep only messages from the NEW location
- This provides a clean reset at each location

## Enhanced Summary Prompt Recommendations:

```python
summary_prompt = """You are a master chronicler documenting an epic adventure. Create a detailed narrative summary of all events that occurred at '{location_name}'.

ESSENTIAL ELEMENTS TO CAPTURE:
1. **Key NPCs Met**: Names, roles, attitudes, and information they provided
2. **Items/Objects**: Any items given, found, purchased, or lost (especially keys, maps, clues)
3. **Information Learned**: Plot revelations, directions, warnings, secrets discovered
4. **Skill Checks**: What was attempted, the type of check, success/failure, and consequences
5. **Combat/Encounters**: Enemies faced, tactics used, outcomes, casualties
6. **Environmental Details**: Traps triggered/avoided, secret passages found, notable features
7. **Quest Progress**: Objectives completed, new objectives received, plot advancement
8. **Party Changes**: Level ups, injuries, equipment changes, party composition changes
9. **Relationships**: How NPC attitudes changed, alliances formed, enemies made
10. **Time Progression**: How long events took, time of day changes

CRITICAL ITEMS TO ALWAYS MENTION:
- Keys, maps, or items that unlock new areas
- Plot-critical information or revelations
- Quest items or MacGuffins
- Promises made or received
- Warnings about future dangers

Write as a flowing narrative in past tense, as if recounting the adventure to another party. Be comprehensive but engaging."""
```

## Benefits Over Current System:

1. **Token Efficiency**: One well-structured summary vs multiple compressed fragments
2. **Narrative Quality**: Maintains the high quality of journal entries
3. **Complete Context**: Nothing gets lost through repeated summarization
4. **Clear Transitions**: Each location change provides a natural boundary
5. **Easy Debugging**: Can easily see/edit the cumulative summary

## Additional Recommendations:

1. **Add Chapter Markers**: 
   ```
   === Chapter 1: Harrow's Hollow ===
   [summaries of all Harrow's Hollow locations]
   
   === Chapter 2: The Gloamwood ===
   [summaries of forest locations]
   ```

2. **Include Transition Context**:
   - Why the party left each location
   - Where they were heading and why
   - Current active objectives

3. **Smart Truncation** (if needed for very long campaigns):
   - Keep last N chapters in full detail
   - Older chapters get a high-level summary
   - Always keep critical plot points

4. **Session Markers**:
   - Add "=== Session Break ===" when exitGame is used
   - Helps AI understand time gaps

Would you like me to help implement this new system?