# ============================================================================
# CAMPAIGN_MANAGER.PY - MULTI-MODULE CAMPAIGN ORCHESTRATION
# ============================================================================
# 
# ARCHITECTURE ROLE: Campaign Layer - Module Continuity Management
# 
# This module handles campaign-level state management, module transitions,
# and inter-module continuity for extended campaigns. It implements the
# hub-and-spoke model where completed modules affect future adventures.
# 
# KEY RESPONSIBILITIES:
# - Manage campaign state across multiple modules
# - Generate and store module completion summaries
# - Track cross-module relationships and consequences
# - Handle module transitions and unlocking
# - Maintain campaign context for AI conversations
# 
# DESIGN PHILOSOPHY:
# - Minimal overhead: Only essential campaign data
# - Token-efficient: Compress completed modules to summaries
# - Continuity-focused: Track decisions that matter across modules
# - Hub-centric: Support Keep of Doom as central base
# 
# ARCHITECTURAL INTEGRATION:
# - Works with existing ModulePathManager for file operations
# - Extends conversation_utils.py with campaign context
# - Integrates with party_tracker.json for state persistence
# - Uses existing AI summarization for module compression
# 
# This module enables rich multi-module campaigns while preserving
# the self-contained nature of individual adventure modules.
# ============================================================================

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
import config
from encoding_utils import safe_json_load, safe_json_dump
from token_estimator import TokenEstimator

class CampaignManager:
    """Manages campaign state and inter-module continuity"""
    
    def __init__(self):
        """Initialize campaign manager"""
        self.campaign_file = "modules/campaign.json"
        self.summaries_dir = "modules/campaign_summaries"
        self.token_estimator = TokenEstimator()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Ensure directories exist
        os.makedirs(self.summaries_dir, exist_ok=True)
        
        # Load or create campaign state
        self.campaign_data = self._load_campaign_data()
    
    def _load_campaign_data(self) -> Dict[str, Any]:
        """Load campaign data or create default"""
        if os.path.exists(self.campaign_file):
            return safe_json_load(self.campaign_file)
        else:
            # Create default campaign
            default_campaign = {
                "campaignName": "Chronicles of the Haunted Realm",
                "currentModule": None,
                "hubModule": None,
                "completedModules": [],
                "availableModules": ["Village", "Keep_of_Doom"],
                "worldState": {
                    "keepOwnership": False,
                    "majorDecisions": [],
                    "crossModuleRelationships": {},
                    "unlockedAreas": [],
                    "hubEstablished": False
                },
                "lastUpdated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            safe_json_dump(default_campaign, self.campaign_file)
            return default_campaign
    
    def get_campaign_context(self, max_tokens: int = 5000) -> str:
        """Get campaign context for AI conversations"""
        context_parts = []
        
        # Campaign overview
        context_parts.append(f"CAMPAIGN: {self.campaign_data['campaignName']}")
        context_parts.append(f"Current Module: {self.campaign_data['currentModule']}")
        
        # Hubs
        if self.campaign_data['hubs']:
            context_parts.append("\nESTABLISHED HUBS:")
            for hub_name, hub_data in self.campaign_data['hubs'].items():
                context_parts.append(f"- {hub_name}: {hub_data}")
        
        # Completed modules summary
        if self.campaign_data['completedModules']:
            context_parts.append("\nPREVIOUS ADVENTURES:")
            for module in self.campaign_data['completedModules']:
                summary = self._load_module_summary(module)
                if summary:
                    context_parts.append(f"\n{module}: {summary.get('summary', 'No summary available')}")
        
        # Relationships
        if self.campaign_data['relationships']:
            context_parts.append("\nKEY RELATIONSHIPS:")
            for name, status in self.campaign_data['relationships'].items():
                context_parts.append(f"- {name}: {status}")
        
        # Artifacts
        if self.campaign_data['artifacts']:
            context_parts.append("\nIMPORTANT ARTIFACTS:")
            for artifact, data in self.campaign_data['artifacts'].items():
                context_parts.append(f"- {artifact}: {data}")
        
        # World State
        if self.campaign_data['worldState']:
            context_parts.append("\nWORLD STATE:")
            for key, value in self.campaign_data['worldState'].items():
                context_parts.append(f"- {key}: {value}")
        
        # Build context string
        context = "\n".join(context_parts)
        
        # Ensure we stay within token budget
        tokens = self.token_estimator.estimate_tokens_from_text(context)
        if tokens > max_tokens:
            # Truncate if necessary (shouldn't happen with proper summary generation)
            context = self._truncate_to_tokens(context, max_tokens)
        
        return context
    
    def _load_module_summary(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Load a module summary if it exists"""
        summary_file = os.path.join(self.summaries_dir, f"{module_name}_summary.json")
        if os.path.exists(summary_file):
            return safe_json_load(summary_file)
        return None
    
    def check_module_completion(self, party_tracker_data: Dict[str, Any]) -> bool:
        """Check if current module is complete based on quest status"""
        # Simple heuristic: All major quests completed or main plot stage reached
        active_quests = party_tracker_data.get('activeQuests', [])
        
        # Check for resolution quest (typically the final quest)
        for quest in active_quests:
            if 'resolution' in quest.get('title', '').lower() and quest.get('status') == 'completed':
                return True
        
        # Alternative: Check if all major quests are completed
        major_quest_statuses = [q['status'] for q in active_quests if 'SQ' not in q.get('id', '')]
        if major_quest_statuses and all(status == 'completed' for status in major_quest_statuses):
            return True
        
        return False
    
    def complete_module(self, module_name: str, party_tracker_data: Dict[str, Any], 
                       conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete a module and generate its summary"""
        print(f"Completing module: {module_name}")
        
        # Generate module summary
        summary = self._generate_module_summary(module_name, party_tracker_data, conversation_history)
        
        # Save summary
        summary_file = os.path.join(self.summaries_dir, f"{module_name}_summary.json")
        safe_json_dump(summary, summary_file)
        
        # Update campaign state
        if module_name not in self.campaign_data['completedModules']:
            self.campaign_data['completedModules'].append(module_name)
        
        # Import exported data from module
        self._handle_module_completion_export(module_name, summary)
        
        # Update available modules based on completion
        self._update_available_modules(module_name, summary)
        
        # Save campaign state
        self.campaign_data['lastUpdated'] = datetime.now().isoformat()
        safe_json_dump(self.campaign_data, self.campaign_file)
        
        return summary
    
    def _generate_module_summary(self, module_name: str, party_tracker_data: Dict[str, Any],
                                conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI-powered module summary"""
        # Extract key information from party tracker
        party_npcs = party_tracker_data.get('partyNPCs', [])
        active_quests = party_tracker_data.get('activeQuests', [])
        
        # Build prompt for AI
        system_prompt = """You are a campaign chronicler summarizing a completed adventure module. 
        Create a concise but comprehensive summary (500-1000 tokens) that captures:
        1. The main story arc and how it was resolved
        2. Key decisions made by the party
        3. Important NPCs and their fates
        4. Consequences that will affect future modules
        5. Items, allies, or abilities gained"""
        
        user_prompt = f"""Summarize the completed module '{module_name}' based on this information:
        
        Party NPCs: {json.dumps(party_npcs, indent=2)}
        Quest Status: {json.dumps(active_quests, indent=2)}
        
        Focus on story outcomes and decisions that will matter in future adventures.
        Keep the summary under 1000 tokens."""
        
        try:
            response = self.client.chat.completions.create(
                model=config.DM_SUMMARY_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            summary_text = response.choices[0].message.content
            
            # Have AI also extract exportable data
            export_prompt = f"""From this module summary, extract key data to export to the campaign:
            
            Summary: {summary_text}
            
            Extract:
            1. Relationships formed (NPCs met, befriended, made enemies)
            2. Artifacts or important items acquired
            3. Locations that could become hubs (owned property, bases)
            4. World state changes (political shifts, curses lifted, etc)
            5. Modules that should be unlocked next
            
            Format as JSON with keys: relationships, artifacts, hubs, worldState, unlockedModules"""
            
            try:
                export_response = self.client.chat.completions.create(
                    model=config.DM_SUMMARY_MODEL,
                    messages=[
                        {"role": "system", "content": "Extract campaign-relevant data from module completion summary. Be concise and factual."},
                        {"role": "user", "content": export_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                exported_data = json.loads(export_response.choices[0].message.content)
            except:
                exported_data = self._process_module_summary_for_export(summary_text, party_tracker_data)
            
            return {
                "moduleName": module_name,
                "completionDate": datetime.now().isoformat(),
                "summary": summary_text,
                "exportedData": exported_data
            }
            
        except Exception as e:
            print(f"Error generating module summary: {e}")
            # Fallback summary
            return {
                "moduleName": module_name,
                "completionDate": datetime.now().isoformat(),
                "summary": f"Module {module_name} was completed successfully.",
                "keyDecisions": [],
                "consequences": {},
                "unlockedModules": [],
                "importantNPCs": {}
            }
    
    def _handle_module_completion_export(self, module_name: str, summary: Dict[str, Any]):
        """Handle exporting data from completed module to campaign state"""
        exported_data = summary.get('exportedData', {})
        
        # Import relationships
        for entity, status in exported_data.get('relationships', {}).items():
            self.campaign_data['relationships'][entity] = status
        
        # Import artifacts
        for artifact, data in exported_data.get('artifacts', {}).items():
            self.campaign_data['artifacts'][artifact] = data
        
        # Import hubs
        for hub, data in exported_data.get('hubs', {}).items():
            self.campaign_data['hubs'][hub] = data
        
        # Import world state changes
        for key, value in exported_data.get('worldState', {}).items():
            self.campaign_data['worldState'][key] = value
    
    def _update_available_modules(self, completed_module: str, summary: Dict[str, Any]):
        """Update available modules based on completion"""
        # Remove completed module
        if completed_module in self.campaign_data['availableModules']:
            self.campaign_data['availableModules'].remove(completed_module)
        
        # Add newly unlocked modules
        unlocked = summary.get('unlockedModules', [])
        for module in unlocked:
            if module not in self.campaign_data['availableModules']:
                self.campaign_data['availableModules'].append(module)
    
    def _process_module_summary_for_export(self, summary_text: str, party_tracker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Let AI extract exportable data from module completion"""
        # This method would use AI to extract key data agnostically
        # For now, return empty export data - would be filled by AI analysis
        return {
            "relationships": {},
            "artifacts": {},
            "hubs": {},
            "worldState": {},
            "unlockedModules": []
        }
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        # Simple truncation - in production would use proper tokenizer
        tokens = self.token_estimator.estimate_tokens_from_text(text)
        if tokens <= max_tokens:
            return text
        
        # Rough estimate: 4 chars per token
        char_limit = max_tokens * 4
        return text[:char_limit] + "..."
    
    def transition_module(self, from_module: str, to_module: str):
        """Handle transition between modules"""
        print(f"Transitioning from {from_module} to {to_module}")
        
        # Update current module
        self.campaign_data['currentModule'] = to_module
        
        # Save state
        self.campaign_data['lastUpdated'] = datetime.now().isoformat()
        safe_json_dump(self.campaign_data, self.campaign_file)
    
    def can_start_module(self, module_name: str) -> bool:
        """Check if a module can be started"""
        # Simple check - is it in available modules?
        return module_name in self.campaign_data.get('availableModules', [])


# Utility functions for integration
def get_campaign_manager():
    """Get or create campaign manager instance"""
    return CampaignManager()

def inject_campaign_context(conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Inject campaign context into conversation history"""
    manager = get_campaign_manager()
    context = manager.get_campaign_context()
    
    # Find or create campaign context message
    campaign_msg_index = None
    for i, msg in enumerate(conversation_history):
        if msg.get('role') == 'system' and 'CAMPAIGN:' in msg.get('content', ''):
            campaign_msg_index = i
            break
    
    campaign_message = {
        "role": "system",
        "content": f"=== CAMPAIGN CONTEXT ===\n{context}"
    }
    
    if campaign_msg_index is not None:
        # Update existing
        conversation_history[campaign_msg_index] = campaign_message
    else:
        # Insert after first system message
        conversation_history.insert(1, campaign_message)
    
    return conversation_history