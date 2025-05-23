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

class AIPlayer:
    """AI player that makes decisions based on test objectives"""
    
    def __init__(self, test_profile, player_name="TestHero"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.test_profile = test_profile
        self.player_name = player_name
        self.conversation_history = []
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
        
    def create_system_prompt(self):
        """Create the system prompt for the AI player"""
        current_objective = self.get_current_objective()
        
        prompt = f"""You are an AI testing a D&D game. Your role is '{self.test_profile['name']}'.

Current Test Profile: {self.test_profile['description']}

Your Current Objective: {current_objective}

Game State:
- Location: {self.game_state['location']}
- HP: {self.game_state['hp']}
- Time: {self.game_state['time']}
- Recent Events: {'; '.join(self.game_state['recent_events'][-3:])}

Testing Guidelines:
1. Make decisions that progress toward your current objective
2. If you encounter an error or unexpected response, note it and try a different approach
3. Be specific in your commands (e.g., "I search the room" not just "search")
4. Test variations of commands when appropriate
5. Document any issues or unclear responses

Constraints:
{json.dumps(self.test_profile.get('constraints', {}), indent=2)}

When responding:
- Give a single, clear action or response
- Don't explain your reasoning unless encountering an issue
- If something seems broken, say "ISSUE DETECTED: [description]" before trying alternatives
- Stay in character as an adventurer, but with testing awareness

What is your next action?"""
        
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
    
    def get_next_action(self, game_output):
        """Determine the next action based on game output and objectives"""
        # Update game state
        self.update_game_state(game_output)
        
        # Check for objective completion
        self.check_objective_completion(game_output)
        
        # Check for issues
        self.check_for_issues(game_output)
        
        # Get AI decision
        messages = [
            {"role": "system", "content": self.create_system_prompt()},
            {"role": "user", "content": f"Game Output:\n{game_output}\n\nWhat is your next action?"}
        ]
        
        # Add recent conversation context
        for msg in self.conversation_history[-4:]:
            messages.append(msg)
        
        try:
            response = self.client.chat.completions.create(
                model=DM_MINI_MODEL,
                temperature=0.7,
                messages=messages,
                max_tokens=150
            )
            
            action = response.choices[0].message.content.strip()
            
            # Log the decision
            self.log_action(game_output, action)
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": game_output})
            self.conversation_history.append({"role": "user", "content": action})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
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
    
    def check_for_issues(self, game_output):
        """Check for potential issues in game output"""
        issue_patterns = [
            (r"error|exception", "Error message detected"),
            (r"undefined|null|none.*error", "Null reference detected"),
            (r"cannot find|not found|doesn't exist", "Missing content detected"),
            (r"[{][^}]*[}]", "Raw JSON in output"),
            (r"DEBUG:|FIXME:|TODO:", "Debug message in output"),
            (r"<.*>", "HTML/XML tags in output"),
            (r"\\n|\\t", "Escaped characters in output")
        ]
        
        for pattern, issue_type in issue_patterns:
            if re.search(pattern, game_output, re.IGNORECASE):
                self.report_issue(issue_type, game_output)
    
    def report_issue(self, issue_type, context):
        """Report a detected issue"""
        issue = {
            "type": issue_type,
            "timestamp": datetime.now().isoformat(),
            "objective": self.get_current_objective(),
            "location": self.game_state['location'],
            "context": context[:500]  # Limit context length
        }
        
        self.issues_found.append(issue)
        game_logger.warning(f"Issue detected: {issue_type} at {self.game_state['location']}")
        game_event("issue_detected", {"type": issue_type, "location": self.game_state['location']})
    
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
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        game_logger.info(f"Test results saved to {filename}")
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