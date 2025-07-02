# Plan: Debug Encounter Action Not Launching Combat Manager

## Issue
The create encounter action is not launching the combat manager but instead returning in the system prompt.

## Investigation Steps

1. **Read CLAUDE.md** - Get project context and guidelines
2. **Gather Primary Game Files** - Collect files needed for analysis:
   - action_handler.py (handles encounter actions)
   - combat_manager.py (manages combat)
   - web_interface.py (web socket handling)
   - game_interface.html (UI interface)
   - static/js/webui.js (client-side logic)
   - main.py (main game loop)
   - run_web.py (web server entry point)

3. **Analyze with Gemini** - Pass files to Gemini to understand:
   - How encounter action flows through the system
   - Why combat manager isn't being launched
   - Impact of recent auto-restart refactoring

4. **Review Refactoring Changes** - Check:
   - game_interface.html changes
   - Web UI script modifications
   - Auto-restart implementation

5. **Verify Entry Point** - Confirm run_web.py is still the correct way to start the game

## Expected Outcome
- Identify root cause of encounter action failure
- Understand impact of recent refactoring
- Provide fix for combat manager launch issue