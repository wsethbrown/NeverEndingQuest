#!/usr/bin/env python3
"""
AI Player for automated testing of DungeonMasterAI
Uses GPT-4o-mini to make intelligent decisions based on test objectives
"""

import json
import time
import re
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, DM_MINI_MODEL
from enhanced_logger import game_logger, game_event
from encoding_utils import safe_json_dump, sanitize_text
import os
from pathlib import Path

class AIPlayer:
    """AI player that makes decisions based on test objectives"""
    
    def __init__(self, test_profile, player_name="TestHero", module_path=None):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.test_profile = test_profile
        self.player_name = player_name
        self.module_path = module_path
        self.conversation_history = []  # Clean conversation history
        self.raw_output_buffer = []  # Buffer for raw game output
        self.test_log = []
        self.issues_found = []
        self.objectives_completed = []
        self.current_objective_index = 0
        self.game_state = {
            "location": "Unknown",
            "hp": "Unknown",
            "inventory": [],
            "time": "Unknown",
            "recent_events": []
        }
        
        # Load character data
        self.character_data = self._load_character_data()
        
        # Initialize LLM debug log
        self.llm_debug_file = "modules/logs/ai_player_llm_debug.log"
        self._init_llm_debug_log()
    
    def _init_llm_debug_log(self):
        """Initialize the LLM debug log file"""
        # Create empty file
        with open(self.llm_debug_file, 'w') as f:
            f.write("")
    
    def _create_character_summary(self, char):
        """Create a comprehensive character summary from JSON data"""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"NAME: {char.get('name', 'Unknown')}")
        summary_parts.append(f"LEVEL: {char.get('level', 1)} {char.get('race', 'Unknown')} {char.get('class', 'Unknown')}")
        summary_parts.append(f"BACKGROUND: {char.get('background', 'Unknown')}")
        summary_parts.append(f"ALIGNMENT: {char.get('alignment', 'Unknown')}")
        
        # Health and defenses
        summary_parts.append(f"HIT POINTS: {char.get('hitPoints', 0)}/{char.get('maxHitPoints', 0)}")
        summary_parts.append(f"ARMOR CLASS: {char.get('armorClass', 10)}")
        summary_parts.append(f"SPEED: {char.get('speed', 30)} feet")
        
        # Ability scores
        abilities = char.get('abilities', {})
        if abilities:
            summary_parts.append("ABILITY SCORES:")
            for ability, score in abilities.items():
                modifier = (score - 10) // 2
                modifier_str = f"+{modifier}" if modifier >= 0 else str(modifier)
                summary_parts.append(f"  {ability.capitalize()}: {score} ({modifier_str})")
        
        # Skills
        skills = char.get('skills', {})
        if skills:
            summary_parts.append("SKILLS:")
            for skill, bonus in skills.items():
                bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
                summary_parts.append(f"  {skill}: {bonus_str}")
        
        # Equipment/Inventory - Only show items with quantity > 0
        equipment = char.get('equipment', [])
        if equipment:
            # Filter out items with zero quantity
            available_items = [item for item in equipment if item.get('quantity', 1) > 0]
            if available_items:
                summary_parts.append("CURRENT EQUIPMENT:")
                for item in available_items[:10]:  # Show first 10 available items
                    item_name = item.get('item_name', 'Unknown item')
                    quantity = item.get('quantity', 1)
                    if quantity > 1:
                        summary_parts.append(f"  {item_name} x{quantity}")
                    else:
                        summary_parts.append(f"  {item_name}")
                if len(available_items) > 10:
                    summary_parts.append(f"  ... and {len(available_items) - 10} more items")
        
        # Spell info if applicable
        spells = char.get('spells', {})
        if spells:
            spell_slots = spells.get('spellSlots', {})
            if spell_slots:
                summary_parts.append("SPELL SLOTS:")
                for level, slots in spell_slots.items():
                    if slots.get('max', 0) > 0:
                        current = slots.get('current', 0)
                        maximum = slots.get('max', 0)
                        summary_parts.append(f"  Level {level}: {current}/{maximum}")
        
        # Special abilities
        features = char.get('features', [])
        if features:
            summary_parts.append("CLASS FEATURES:")
            for feature in features[:5]:  # Show first 5 features
                name = feature.get('name', 'Unknown feature')
                summary_parts.append(f"  {name}")
            if len(features) > 5:
                summary_parts.append(f"  ... and {len(features) - 5} more features")
        
        return "\n".join(summary_parts)
    
    def _load_character_data(self):
        """Load character data from norn.json using party_tracker module"""
        try:
            # First, get the module name from party_tracker.json
            with open("party_tracker.json", 'r', encoding='utf-8') as f:
                party_data = json.load(f)
                module_name = party_data.get("module", "Keep_of_Doom")
                
            # Construct the path to norn.json in the module folder
            char_path = Path(f"modules/{module_name}/characters/norn.json")
            
            if char_path.exists():
                with open(char_path, 'r', encoding='utf-8') as f:
                    game_logger.info(f"Loaded character data from {char_path}")
                    return json.load(f)
            else:
                game_logger.warning(f"Character file not found at {char_path}")
                
        except Exception as e:
            game_logger.error(f"Error loading character data: {str(e)}")
        
        # Return minimal default if not found
        game_logger.warning("Using default character data")
        return {
            "name": "Norn",
            "race": "Human",
            "class": "Fighter",
            "level": 4,
            "background": "Soldier",
            "alignment": "lawful good",
            "personality_traits": "Always polite and respectful",
            "ideals": "Responsibility",
            "bonds": "Fight for those who cannot fight for themselves",
            "flaws": "Hard time hiding true feelings"
        }
    
    def _log_llm_interaction(self, messages, response_text=None):
        """Log only the exact messages sent to OpenAI API - overwrites file each time"""
        with open(self.llm_debug_file, 'w') as f:
            # Write the exact API payload
            api_payload = {
                "model": DM_MINI_MODEL,
                "temperature": 0.7,
                "messages": messages
            }
            f.write(json.dumps(api_payload, indent=2))
        
    def create_system_prompt(self):
        """Create the system prompt for the AI player with complete character data"""
        current_objective = self.get_current_objective()
        char = self.character_data
        # Check if we have a speedrun profile by looking at constraints
        constraints = self.test_profile.get('constraints', {})
        profile_name = self.test_profile.get('name', '')
        
        # Determine profile type based on constraints and name
        is_speedrun = (constraints.get('focus_main_quest', False) and 
                      constraints.get('minimize_side_content', False))
        is_combat_test = 'combat' in profile_name.lower()
        
        # Create complete character summary from JSON data
        char_summary = self._create_character_summary(char)
        
        # Create base character info with full data
        base_info = f"""You are an AI tester validating a 5e game system while playing as {char['name']}, a level {char['level']} {char['race']} {char['class']}.

PRIMARY ROLE: Game System Tester
Your main purpose is to systematically test game functionality, find issues, and validate that all systems work correctly.

TESTING PROFILE: {self.test_profile.get('name', 'Custom Test')}
Description: {self.test_profile.get('description', 'Automated testing profile')}

CURRENT OBJECTIVE: {current_objective}

COMPLETE CHARACTER DATA:
{char_summary}

ONGOING CONVERSATION CONTEXT:
This is a CONTINUOUS conversation with the Dungeon Master. You have full access to all previous interactions below and should reference them when making decisions. The DM remembers everything that has happened, so you can:
- Refer to previous events, conversations, and locations visited
- Reference items you've stored, NPCs you've talked to, or actions you've taken
- Build upon previous decisions and conversations naturally
- Ask follow-up questions or revisit previous topics

IMPORTANT: Use your complete character data above to make informed decisions about what you can do, what equipment you have, and what your capabilities are. Don't ask about things you can see in your character sheet."""

        # Profile-specific prompts
        if is_speedrun:
            prompt = f"""{base_info}

CRITICAL TESTING FOCUS: QUEST DISCOVERY & TRACKING

SPEEDRUN TESTING METHODOLOGY:
1. QUEST DISCOVERY (HIGHEST PRIORITY)
   - Immediately seek out quest-giving NPCs
   - Ask every NPC about quests, missions, or tasks
   - Use keywords: "quest", "help", "task", "mission", "problem"
   - Document ALL quest information received
   - Report if quest objectives are unclear or missing

2. QUEST TRACKING
   - After receiving a quest, verify it appears in your objectives
   - Check if quest markers or hints are provided
   - Test if the game tracks quest progress
   - Verify quest completion conditions
   - Document any quest-breaking bugs

3. EFFICIENT PROGRESSION
   - Move directly between quest objectives
   - Skip optional content (note it exists but don't explore)
   - Focus on main storyline NPCs
   - Test fast travel if available
   - Minimize combat unless required for quest

4. SPEEDRUN BEHAVIORS
   - Take the most direct path to objectives
   - Skip flavor text and lore unless quest-critical
   - Avoid side quests unless they block main progression
   - Test if you can sequence-break quests
   - Try to complete objectives out of order

5. CRITICAL VALIDATION POINTS
   - Can you find the main quest?
   - Are quest objectives clearly communicated?
   - Does the game guide you to the next objective?
   - Can you complete the quest as intended?
   - Are there any softlocks or progression blockers?

ISSUE REPORTING FOCUS:
- QUEST_NOT_FOUND: Cannot discover main quest
- OBJECTIVE_UNCLEAR: Quest objectives are vague or missing
- PROGRESSION_BLOCKED: Cannot advance main quest
- SEQUENCE_BREAK: Able to skip required steps
- QUEST_TRACKING_FAIL: Game doesn't track quest progress

CONSTRAINTS:
- Minimize side content: {constraints.get('minimize_side_content', False)}
- Focus main quest: {constraints.get('focus_main_quest', False)}
- Combat required: {constraints.get('require_combat', False)}
- Complete speedrun: {constraints.get('complete_speedrun', False)}

Remember: Your goal is to speedrun the main quest while documenting any issues that would prevent a player from finding or completing it quickly."""

        elif is_combat_test:
            prompt = f"""{base_info}

COMBAT STRESS TESTING METHODOLOGY:
1. SEEK COMBAT ENCOUNTERS
   - Actively look for enemies
   - Engage every hostile creature
   - Test group combat scenarios
   - Try to trigger multiple enemies at once

2. COMBAT MECHANICS TESTING
   - Test all available attacks and abilities
   - Verify damage calculations
   - Check status effects
   - Test healing and recovery
   - Validate death and respawn mechanics

3. EDGE CASES
   - Fight with low HP
   - Test combat with no equipment
   - Try to flee from combat
   - Test environmental damage
   - Verify turn order and initiative

Remember: Focus on breaking combat mechanics and finding edge cases."""

        else:
            # Default thorough testing prompt
            prompt = f"""{base_info}

TESTING METHODOLOGY:
1. SYSTEMATIC EXPLORATION
   - Visit every accessible location
   - Try all available actions in each location
   - Test all transitions between areas
   - Document what works and what doesn't

2. INTERACTION TESTING
   - Talk to every NPC you encounter
   - Exhaust all dialogue options
   - Try different conversation approaches
   - Test both polite and confrontational responses

3. COMMAND VARIATIONS
   - Test synonyms: "examine" vs "look at" vs "inspect"
   - Try incomplete commands to test error handling
   - Attempt invalid actions to verify error messages
   - Test case sensitivity if relevant

4. ISSUE DETECTION & REPORTING
   When you encounter problems, report them clearly:
   - ISSUE DETECTED: [Type] - [Description] - [Attempted Action] - [Result]
   
   Issue Types:
   - MISSING_CONTENT: Expected content not found
   - ERROR: System errors or crashes  
   - INCONSISTENCY: Logic or continuity problems
   - UNCLEAR: Vague or confusing responses
   - TRANSITION_FAIL: Cannot move between locations
   - VALIDATION_FAIL: System rejects valid actions

5. TESTING BEHAVIORS
   - Override character personality when it conflicts with testing needs
   - If Norn would "hesitate," push forward for testing completeness
   - Try edge cases and boundary conditions
   - Attempt to break the game in controlled ways
   - Verify all game state changes

DECISION MAKING:
- When multiple options exist, choose the one that tests new functionality
- Prioritize unexplored content over roleplay consistency
- Focus on your current objective but note other issues found
- After each action, verify the game responded appropriately

RESPONSE GUIDELINES:
1. NATURAL LANGUAGE: Use normal conversational responses (aim for ~20-35 words)
2. ACTION-FOCUSED: State your action clearly, brief context is fine
3. VALID ACTIONS ONLY: Choose from these tested action types:
   - Look/examine [object/area]
   - Go/move [direction/location]
   - Talk to [character name]
   - Attack [target]
   - Use [item] or Cast [spell]
   - Take/get [item]
   - Store/retrieve items (storage system)
   - Open/close [door/container]
   - Search [area]
   - Help (when stuck)

NATURAL SPEECH GUIDELINES:
- Use conversational tone like a real player would
- Brief context or reasoning is fine ("I'll check the chest for loot")
- Avoid multi-paragraph backstories or elaborate character histories
- Don't ask meta-questions like "what would my character do"

EXAMPLE NATURAL RESPONSES: 
- "I'll go north to see what's there"
- "Let me talk to the shopkeeper about what they're selling"
- "I want to examine that chest carefully for any traps"
- "I should store some of my gear here before moving on"

ISSUE REPORTING: Only when you encounter actual bugs/errors:
"ISSUE DETECTED: [Type] - [Brief description]"

Remember: You are a TESTER, not a creative writer. Be concise, direct, and systematic."""
        
        return prompt
    
    def get_current_objective(self):
        """Get the current test objective"""
        objectives = self.test_profile.get('objectives', [])
        if self.current_objective_index < len(objectives):
            return objectives[self.current_objective_index]
        return "Explore and test general gameplay"
    
    def update_game_state(self, game_output):
        """Extract game state from DM output"""
        # Extract location
        location_match = re.search(r"Current location: ([^\.]+)", game_output)
        if location_match:
            self.game_state['location'] = location_match.group(1).strip()
        
        # Extract HP
        hp_match = re.search(r"\[HP:(\d+/\d+)\]", game_output)
        if hp_match:
            self.game_state['hp'] = hp_match.group(1)
        
        # Extract time
        time_match = re.search(r"\[(\d+:\d+:\d+)\]", game_output)
        if time_match:
            self.game_state['time'] = time_match.group(1)
        
        # Add to recent events (summarize long outputs)
        if len(game_output) > 200:
            summary = game_output[:200] + "..."
        else:
            summary = game_output
        self.game_state['recent_events'].append(summary)
        if len(self.game_state['recent_events']) > 5:
            self.game_state['recent_events'].pop(0)
    
    def filter_game_output(self, raw_output):
        """Extract only the DM's narrative content from game output"""
        # Skip empty output
        if not raw_output or not raw_output.strip():
            return None
            
        # Skip any JSON objects (equipment updates, etc.)
        if raw_output.strip().startswith('{') and raw_output.strip().endswith('}'):
            return None
            
        # Skip debug messages
        if any(prefix in raw_output for prefix in ['DEBUG:', 'VALIDATION:', 'System:', 'Schema:']):
            return None
            
        # Skip error messages that aren't relevant to gameplay
        if 'Traceback' in raw_output or 'Error:' in raw_output and 'validation' in raw_output.lower():
            return None
            
        # Skip repeated dashes or formatting lines
        if raw_output.strip() in ['---', '===', '***'] or raw_output.strip().startswith('---'):
            return None
            
        # Skip adventure history context
        if 'Adventure History Context:' in raw_output:
            return None
            
        # Skip pure time/date notes without other content
        if raw_output.strip().startswith('Dungeon Master Note:') and 'Current date and time:' in raw_output and len(raw_output.strip()) < 100:
            return None
        
        # Skip status messages
        if any(status in raw_output for status in ['[Processing', '[Validating', '[Generating']):
            return None
            
        # Skip validation failure messages
        if raw_output.strip().startswith('Validation failed'):
            return None
            
        # Skip debug info like "User messages: X" or "Assistant messages: X"
        if re.match(r'^(User|Assistant) messages: \d+$', raw_output.strip()):
            return None
        
        # Skip time advancement messages
        if 'Current Time:' in raw_output and 'Time Advanced:' in raw_output:
            return None
        
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', raw_output)
        
        # Skip player status lines (time/HP/XP display)
        if re.match(r'^\[\d+:\d+:\d+\]\[HP:\d+/\d+\]\[XP:\d+/\d+\]', cleaned):
            return None
        
        # Extract DM narrative - look for "Dungeon Master:" prefix
        dm_match = re.search(r'Dungeon Master:\s*(.+)', cleaned, re.DOTALL)
        if dm_match:
            return dm_match.group(1).strip()
        
        # If no DM prefix but contains narrative content (not just status/time)
        # Check if it's likely narrative (contains multiple words, not just timestamps)
        cleaned = cleaned.strip()
        if cleaned and not re.match(r'^\[\d+:\d+:\d+\]', cleaned) and len(cleaned.split()) > 5:
            # Skip if it looks like a player name followed by colon (like "norn:")
            if re.match(r'^[a-zA-Z]+:$', cleaned):
                return None
            return cleaned
            
        return None
    
    def get_next_action(self, game_output):
        """Determine the next action based on game output and objectives"""
        # Filter the game output
        filtered_output = self.filter_game_output(game_output)
        
        # If output was filtered out, don't process it
        if filtered_output is None:
            return None
            
        # Add to raw buffer for debugging
        self.raw_output_buffer.append(game_output)
        if len(self.raw_output_buffer) > 100:
            self.raw_output_buffer.pop(0)
        
        # Update game state
        self.update_game_state(filtered_output)
        
        # Check for objective completion
        self.check_objective_completion(filtered_output)
        
        # Check for issues
        self.check_for_issues(filtered_output)
        
        # Build messages for AI with system prompt and full conversation history
        messages = [
            {"role": "system", "content": self.create_system_prompt()}
        ]
        
        # Add complete conversation history with proper context
        # Each exchange: DM message (user) -> AI response (assistant)
        for msg in self.conversation_history:
            messages.append(msg)
            
        # Add current DM output as a user message
        messages.append({"role": "user", "content": filtered_output})
        
        # Manage message history length to prevent token overflow
        # Keep system prompt + last 20 exchanges (40 messages)
        if len(messages) > 41:  # system + 40 messages
            # Keep system prompt and last 20 exchanges
            messages = [messages[0]] + messages[-40:]
        
        # Log the exact API payload before making the call
        self._log_llm_interaction(messages, None)
        
        try:
            response = self.client.chat.completions.create(
                model=DM_MINI_MODEL,
                temperature=0.7,
                messages=messages
            )
            
            action = response.choices[0].message.content.strip()
            # Sanitize AI response to prevent encoding issues
            action = sanitize_text(action)
            
            # Validate and constrain the response
            action = self.validate_and_constrain_response(action)
            
            # Track the current action for error reporting
            self._last_action = action
            
            # Log the decision
            self.log_action(filtered_output, action)
            
            # Add to conversation history with correct roles
            # DM output is "user" (what the game told the AI)
            # AI action is "assistant" (how the AI responded)
            self.conversation_history.append({"role": "user", "content": filtered_output})
            self.conversation_history.append({"role": "assistant", "content": action})
            
            # Keep conversation history manageable (last 30 exchanges = 60 messages)
            if len(self.conversation_history) > 60:
                # Remove oldest exchanges but keep recent context
                self.conversation_history = self.conversation_history[-60:]
            
            return action
            
        except Exception as e:
            game_logger.error(f"AI Player error: {str(e)}")
            return "look around"  # Default safe action
    
    def check_objective_completion(self, game_output):
        """Check if current objective might be completed"""
        current_objective = self.get_current_objective()
        
        # Simple heuristic checks
        objective_lower = current_objective.lower()
        output_lower = game_output.lower()
        
        completion_indicators = {
            "visit": ["you arrive", "you enter", "you stand in"],
            "talk to": ["says", "replies", "tells you"],
            "gather": ["you learn", "you discover", "reveals"],
            "acquire": ["you receive", "you take", "added to inventory"],
            "fight": ["combat", "you defeat", "victory"],
            "find": ["you find", "you discover", "you see"]
        }
        
        for key, indicators in completion_indicators.items():
            if key in objective_lower:
                if any(indicator in output_lower for indicator in indicators):
                    self.mark_objective_progress(current_objective, "possible_completion")
    
    def validate_and_constrain_response(self, action):
        """Validate and constrain AI response to prevent verbosity and invalid actions"""
        
        # Valid action verbs that the game system supports
        valid_actions = [
            'look', 'examine', 'inspect', 'go', 'move', 'walk', 'run', 'travel',
            'talk', 'speak', 'ask', 'tell', 'say', 'greet',
            'attack', 'fight', 'strike', 'hit', 'defend',
            'use', 'cast', 'activate', 'consume', 'drink', 'eat',
            'take', 'get', 'pick', 'grab', 'drop', 'give',
            'store', 'retrieve', 'put', 'place',
            'open', 'close', 'unlock', 'lock',
            'search', 'find', 'seek',
            'help', 'commands', 'inventory', 'status',
            'wait', 'rest', 'sleep'
        ]
        
        # No artificial word limits - let natural language flow
        # Only remove completely invalid or problematic content
        
        # Only remove extremely problematic verbose phrases
        overly_verbose_phrases = [
            "As a seasoned adventurer with years of experience, I think",
            "Given my extensive background as a seasoned",
            "Considering all the factors and my character's motivations, I believe",
            "After careful deliberation about my character's personality and background, I decide"
        ]
        
        for phrase in overly_verbose_phrases:
            if phrase.lower() in action.lower():
                # Remove only the problematic phrase, keep the rest
                action = action.replace(phrase, "").strip()
                # Clean up any double spaces
                action = ' '.join(action.split())
                break
        
        # Remove issue reporting unless it's a real issue
        if action.startswith("ISSUE DETECTED:") and not any(keyword in action.lower() for keyword in ['error', 'bug', 'fail', 'crash', 'broken']):
            action = "look around"  # Default safe action
            
        # Only validate action if it's clearly invalid - allow natural speech patterns
        words = action.split()
        if words:
            first_word = words[0].lower()
            # Allow common natural language starters  
            natural_starters = valid_actions + ["i", "i'll", "let", "maybe", "perhaps", "i'd", "i'd", "let's"]
            
            if first_word not in natural_starters:
                # Try to find a valid action in the response
                found_action = False
                for word in words:
                    if word.lower() in valid_actions:
                        # Reconstruct starting with the action verb
                        idx = words.index(word)
                        action = ' '.join(words[idx:])
                        found_action = True
                        break
                
                if not found_action:
                    # Only default if completely invalid
                    action = "look around"
                    game_logger.warning(f"No valid action found in AI response, defaulting to: {action}")
        
        # Remove quotes if the entire action is quoted
        if action.startswith('"') and action.endswith('"'):
            action = action[1:-1]
        if action.startswith("'") and action.endswith("'"):
            action = action[1:-1]
            
        # Clean up common formatting issues
        action = action.replace('  ', ' ').strip()
        
        # Ensure it's not empty
        if not action:
            action = "look around"
            
        return action

    def check_for_issues(self, game_output):
        """Check for potential issues in game output with enhanced detection"""
        issue_patterns = [
            # Critical errors
            (r"error|exception|traceback|failed.*to", "CRITICAL_ERROR"),
            (r"validation.*failed|schema.*error", "VALIDATION_ERROR"),
            (r"file.*not.*found|directory.*not.*exist", "FILE_MISSING"),
            
            # Content issues
            (r"undefined|null.*reference|none.*error", "NULL_REFERENCE"),
            (r"cannot find|not found|doesn't exist", "MISSING_CONTENT"),
            (r"no.*response|empty.*response", "EMPTY_RESPONSE"),
            
            # System issues
            (r"[{][^}]*[}]", "RAW_JSON_OUTPUT"),
            (r"DEBUG:|FIXME:|TODO:", "DEBUG_LEAK"),
            (r"<.*>", "HTML_XML_TAGS"),
            (r"\\n|\\t", "ESCAPED_CHARS"),
            
            # Storage system issues
            (r"gold.*coin.*not.*found|item.*not.*in.*inventory", "STORAGE_INVENTORY_MISMATCH"),
            (r"storage.*operation.*failed", "STORAGE_OPERATION_FAILED"),
            
            # Combat issues
            (r"combat.*error|turn.*order.*failed", "COMBAT_ERROR"),
            (r"damage.*calculation.*error", "DAMAGE_CALCULATION_ERROR")
        ]
        
        for pattern, issue_type in issue_patterns:
            match = re.search(pattern, game_output, re.IGNORECASE)
            if match:
                # Extract the specific error context
                error_context = self._extract_error_context(game_output, match)
                self.report_issue(issue_type, game_output, error_context)
    
    def _extract_error_context(self, game_output, match):
        """Extract specific error context around the matched pattern"""
        start = max(0, match.start() - 100)
        end = min(len(game_output), match.end() + 100)
        context = game_output[start:end].strip()
        
        # Try to get the specific error line
        lines = game_output.split('\n')
        for i, line in enumerate(lines):
            if match.group(0).lower() in line.lower():
                # Get surrounding lines for context
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                return '\n'.join(lines[context_start:context_end])
        
        return context
    
    def report_issue(self, issue_type, full_context, error_context=None):
        """Report a detected issue with enhanced details"""
        # Get current action for better context
        current_action = getattr(self, '_last_action', 'Unknown action')
        
        issue = {
            "type": issue_type,
            "timestamp": datetime.now().isoformat(),
            "objective": self.get_current_objective(),
            "location": self.game_state.get('location', 'Unknown'),
            "current_action": current_action,
            "error_context": error_context[:300] if error_context else None,
            "full_context": full_context[:500],  # Limit full context length
            "action_count": getattr(self, 'actions_taken', 0)
        }
        
        self.issues_found.append(issue)
        
        # Enhanced logging with more details
        location = self.game_state.get('location', 'Unknown')
        game_logger.warning(f"ISSUE DETECTED [{issue_type}] at {location} during '{current_action}'")
        if error_context:
            game_logger.warning(f"Error context: {error_context[:150]}...")
        
        game_event("issue_detected", {
            "type": issue_type, 
            "location": location,
            "action": current_action
        })
    
    def mark_objective_progress(self, objective, status):
        """Mark progress on an objective"""
        self.objectives_completed.append({
            "objective": objective,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "location": self.game_state['location']
        })
        
        game_event("objective_progress", {
            "objective": objective[:50] + "...",
            "status": status
        })
    
    def log_action(self, game_output, action):
        """Log the interaction for analysis"""
        self.test_log.append({
            "timestamp": datetime.now().isoformat(),
            "game_output": game_output,
            "ai_action": action,
            "current_objective": self.get_current_objective(),
            "game_state": self.game_state.copy()
        })
    
    def advance_objective(self):
        """Move to the next objective"""
        self.current_objective_index += 1
        if self.current_objective_index < len(self.test_profile.get('objectives', [])):
            new_objective = self.get_current_objective()
            game_logger.info(f"Advanced to objective: {new_objective}")
            game_event("objective_change", {"new_objective": new_objective[:50] + "..."})
    
    def generate_test_report(self):
        """Generate a report of the test session"""
        report = {
            "test_profile": self.test_profile['name'],
            "player_name": self.player_name,
            "start_time": self.test_log[0]['timestamp'] if self.test_log else "N/A",
            "end_time": datetime.now().isoformat(),
            "total_actions": len(self.test_log),
            "objectives_attempted": self.current_objective_index + 1,
            "objectives_completed": len([o for o in self.objectives_completed if o['status'] == 'completed']),
            "issues_found": len(self.issues_found),
            "issues_detail": self.issues_found,
            "objectives_progress": self.objectives_completed,
            "sample_interactions": self.test_log[-10:] if len(self.test_log) > 10 else self.test_log
        }
        
        return report
    
    def save_test_results(self, filename=None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{self.test_profile['name'].replace(' ', '_')}_{timestamp}.json"
        
        report = self.generate_test_report()
        
        safe_json_dump(report, filename)
        
        game_logger.info(f"Test results saved to {filename}")
        game_logger.info(f"LLM debug log available at: {self.llm_debug_file}")
        
        # Add note about debug log to report
        report['llm_debug_log'] = self.llm_debug_file
        
        return filename

class AIPlayerPersonality:
    """Different personality types for more varied testing"""
    
    CAUTIOUS = {
        "name": "Cautious Explorer",
        "traits": ["always searches for traps", "asks about dangers", "saves frequently"],
        "action_modifiers": ["carefully", "cautiously", "slowly"]
    }
    
    AGGRESSIVE = {
        "name": "Aggressive Warrior", 
        "traits": ["attacks first", "breaks doors", "rushes into danger"],
        "action_modifiers": ["forcefully", "quickly", "aggressively"]
    }
    
    CURIOUS = {
        "name": "Curious Scholar",
        "traits": ["examines everything", "asks many questions", "reads all text"],
        "action_modifiers": ["thoroughly", "carefully examine", "study"]
    }
    
    SPEEDRUNNER = {
        "name": "Speedrunner",
        "traits": ["skips optional content", "takes shortcuts", "minimal interaction"],
        "action_modifiers": ["quickly", "directly", "immediately"]
    }