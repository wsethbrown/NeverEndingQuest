# ============================================================================
# CAMPAIGN_MANAGER.PY - LOCATION-BASED HUB-AND-SPOKE CAMPAIGN ORCHESTRATION
# ============================================================================
# 
# ARCHITECTURE ROLE: Campaign Layer - Location-Based Module Continuity
# 
# This module implements a revolutionary location-based hub-and-spoke campaign
# system where module boundaries are geographic rather than narrative. Players
# seamlessly transition between modules based on location, with automatic
# context preservation and summary generation.
# 
# CORE DESIGN PHILOSOPHY - LOCATION-BASED MODULES:
# - Each geographic area network = one module (Shadowmere_Valley, Crystal_Peaks, etc.)
# - Module context automatically loads based on current location ID
# - Cross-module travel triggers automatic summarization of previous module
# - Multiple visits to same module accumulate summaries for rich context
# - No player prompts needed - transitions are organic and AI-driven
# 
# HUB-AND-SPOKE MODEL:
# - Central hub locations (Thornwick Village) accessible from multiple modules
# - Players can return to any visited module through natural travel
# - Each module retains its state and continues to evolve with new visits
# - Adventure summaries accumulate, creating living world history
# 
# KEY RESPONSIBILITIES:
# - Detect cross-module transitions via location IDs
# - Auto-generate module summaries when leaving module areas
# - Accumulate and inject relevant module summaries as conversation context
# - Maintain module visit history and state continuity
# - Support unlimited module revisiting with full context preservation
# 
# LOCATION-TO-MODULE MAPPING EXAMPLE:
# - TV001, TV002, TV003 → Thornwick_Village module (hub)
# - SM001, SM002, SM003 → Shadowmere_Valley module  
# - CP001, CP002, CP003 → Crystal_Peaks module
# - Module detection via location ID prefixes or area mappings
# 
# SUMMARY ACCUMULATION STRATEGY:
# Visit 1: Shadowmere_Valley → [Chronicle of the Cursed Marshlands]
# Visit 2: Crystal_Peaks → [Tale of the Frozen Spires] 
# Visit 3: Return to Shadowmere_Valley → [Previous chronicles + new events]
# Visit 4: Back to Crystal_Peaks → [All accumulated chronicles + latest adventure]
# 
# ARCHITECTURAL INTEGRATION:
# - Enhanced transitionLocation detection for cross-module movement
# - Automatic conversation context injection with accumulated summaries
# - Seamless integration with existing ModulePathManager architecture
# - Maintains backward compatibility with single-module adventures
# 
# This system creates a living, interconnected world where every adventure
# builds upon previous experiences while maintaining the modular architecture.
# ============================================================================

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
import config
from encoding_utils import safe_json_load, safe_json_dump
from module_path_manager import ModulePathManager

class CampaignManager:
    """Manages campaign state and inter-module continuity"""
    
    def __init__(self):
        """Initialize campaign manager"""
        self.campaign_file = "modules/campaign.json"
        self.summaries_dir = "modules/campaign_summaries"
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Ensure directories exist
        os.makedirs(self.summaries_dir, exist_ok=True)
        self.archives_dir = "modules/campaign_archives"
        os.makedirs(self.archives_dir, exist_ok=True)
        
        # Load or create campaign state
        self.campaign_data = self._load_campaign_data()
        
        # Scan for new modules on startup (delayed import to avoid circular imports)
        self._scan_for_new_modules()
    
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
    
    def _scan_for_new_modules(self):
        """Scan for new modules using module stitcher and update available modules"""
        try:
            # Delayed import to avoid circular imports
            from module_stitcher import get_module_stitcher
            
            # Get module stitcher and scan for new modules
            stitcher = get_module_stitcher()
            newly_integrated = stitcher.scan_and_integrate_new_modules()
            
            if newly_integrated:
                # Update available modules in campaign data
                current_available = set(self.campaign_data.get('availableModules', []))
                current_available.update(newly_integrated)
                self.campaign_data['availableModules'] = list(current_available)
                
                # Save updated campaign data
                self.campaign_data['lastUpdated'] = datetime.now().isoformat()
                safe_json_dump(self.campaign_data, self.campaign_file)
                
                print(f"Campaign Manager: Integrated {len(newly_integrated)} new modules: {', '.join(newly_integrated)}")
            
        except Exception as e:
            print(f"Warning: Failed to scan for new modules: {e}")
    
    def get_campaign_context(self) -> str:
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
        return context
    
    def _load_module_summaries(self, module_name: str) -> List[Dict[str, Any]]:
        """Load ALL module summaries for a given module (supports multiple visits)"""
        import glob
        
        summaries = []
        pattern = os.path.join(self.summaries_dir, f"{module_name}_summary_*.json")
        summary_files = glob.glob(pattern)
        
        # Sort by sequence number
        summary_files.sort(key=lambda x: self._extract_sequence_number(x))
        
        for summary_file in summary_files:
            try:
                summary = safe_json_load(summary_file)
                if summary:
                    summaries.append(summary)
            except Exception as e:
                print(f"Warning: Failed to load summary {summary_file}: {e}")
        
        return summaries
    
    def _extract_sequence_number(self, file_path: str) -> int:
        """Extract sequence number from filename"""
        import re
        filename = os.path.basename(file_path)
        match = re.search(r'_(\d+)\.json$', filename)
        return int(match.group(1)) if match else 0
    
    def check_module_completion(self, module_name: str) -> bool:
        """Check if module is complete based on module_plot.json"""
        try:
            # Get module plot file
            path_manager = ModulePathManager(module_name)
            plot_file = os.path.join(path_manager.module_dir, "module_plot.json")
            
            if not os.path.exists(plot_file):
                print(f"No module_plot.json found for {module_name}")
                return False
            
            plot_data = safe_json_load(plot_file)
            plot_points = plot_data.get('plotPoints', [])
            
            if not plot_points:
                return False
            
            # Find the final plot point (one with empty nextPoints)
            final_plot_point = None
            for point in plot_points:
                if not point.get('nextPoints', []):
                    final_plot_point = point
                    break
            
            if final_plot_point:
                return final_plot_point.get('status') == 'completed'
            
            # Fallback: Check if all plot points are completed
            return all(point.get('status') == 'completed' for point in plot_points)
            
        except Exception as e:
            print(f"Error checking module completion for {module_name}: {e}")
            return False
    
    def sync_party_tracker_with_plot(self, module_name: str) -> bool:
        """Sync party_tracker.json quest statuses with module_plot.json"""
        try:
            # Load module plot data
            path_manager = ModulePathManager(module_name)
            plot_file = os.path.join(path_manager.module_dir, "module_plot.json")
            party_file = "party_tracker.json"
            
            if not os.path.exists(plot_file):
                print(f"No module_plot.json found for {module_name}")
                return False
            
            plot_data = safe_json_load(plot_file)
            party_data = safe_json_load(party_file)
            
            # Create a mapping of quest IDs to their plot statuses
            quest_statuses = {}
            
            # Get statuses from main plot points
            for point in plot_data.get('plotPoints', []):
                quest_id = point.get('id')
                status = point.get('status')
                if quest_id and status:
                    quest_statuses[quest_id] = status
                
                # Also get side quest statuses
                for side_quest in point.get('sideQuests', []):
                    sq_id = side_quest.get('id')
                    sq_status = side_quest.get('status')
                    if sq_id and sq_status:
                        quest_statuses[sq_id] = sq_status
            
            # Update party tracker quests
            updated = False
            for quest in party_data.get('activeQuests', []):
                quest_id = quest.get('id')
                if quest_id in quest_statuses:
                    new_status = quest_statuses[quest_id]
                    if quest.get('status') != new_status:
                        print(f"Syncing {quest_id}: {quest.get('status')} -> {new_status}")
                        quest['status'] = new_status
                        updated = True
            
            # Save updated party tracker if changes were made
            if updated:
                safe_json_dump(party_data, party_file)
                print(f"Party tracker synced with module plot for {module_name}")
            
            return updated
            
        except Exception as e:
            print(f"Error syncing party tracker with plot for {module_name}: {e}")
            return False
    
    def complete_module(self, module_name: str, party_tracker_data: Dict[str, Any], 
                       conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete a module and generate its summary"""
        print(f"Completing module: {module_name}")
        
        # Generate module summary
        summary = self._generate_module_summary(module_name, party_tracker_data, conversation_history)
        
        # Save summary with sequential numbering
        sequence_num = self._get_next_sequence_number(self.summaries_dir, f"{module_name}_summary", ".json")
        summary_file = os.path.join(self.summaries_dir, f"{module_name}_summary_{sequence_num:03d}.json")
        
        # Add sequence number to summary data
        summary["sequenceNumber"] = sequence_num
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
        # Archive full conversation history before summarization
        self._archive_conversation_history(module_name, conversation_history)
        
        # Load module plot data for structured information
        plot_data = self._load_module_plot_data(module_name)
        
        # Extract key information from party tracker
        party_npcs = party_tracker_data.get('partyNPCs', [])
        active_quests = party_tracker_data.get('activeQuests', [])
        
        # Build enhanced prompt for AI using plot data and conversation history
        system_prompt = """You are a chronicler and narrative designer for a fantasy TTRPG setting. Your job is to synthesize a full-length adventure arc into a single, elegant, elevated prose summary, based on structured location summaries and plot notes provided to you. Your writing should sound like a campaign journal, codex scroll, or in-world historical chronicle.

You MUST:
1. Work in past tense, third person, using immersive and elevated fantasy prose.
2. Combine multiple location summaries, character actions, player interactions, and module-level plot points into a **single narrative**.
3. Maintain **chronological flow**, but do not structure it like a bullet-pointed travel log.
4. Highlight:
   - The main story arc and how it resolved
   - Key player actions, sacrifices, and moments of bravery or failure
   - Consequences of rituals, combat, negotiations, and discoveries
   - Character relationships: loyalty, bonding, disagreements, confessions, moments of vulnerability or humor
   - Romantic developments or emotional subplots if present
   - NPCs who changed because of the party's actions (e.g. gained hope, suffered loss, forged bonds)
   - Side quests and how they connected (if relevant)
   - Emotional turning points and events that would form lasting memories for PCs or NPCs
   - Items of symbolic or magical value, and their narrative weight
   - Thematic closure: what changed, who grew, what lingers unresolved
5. Avoid game mechanics (no mention of rolls, stats, XP, or abilities).
6. Do NOT list locations like a log. Weave them naturally into the story.
7. Focus on **emotional stakes and character consequence**, not raw action alone.

Your final output should be a self-contained summary of the complete adventure arc — fitting for a codex, character-facing epilogue, or in-world retelling of their legend."""
        
        # Prepare plot data summary
        plot_summary = ""
        if plot_data:
            plot_summary = f"Plot Structure: {json.dumps(plot_data.get('plotPoints', []), indent=2)}"
        
        # Filter out system messages from conversation history and include everything else
        filtered_conversation = []
        if conversation_history:
            for message in conversation_history:
                if message.get('role') != 'system':
                    filtered_conversation.append(message)
        
        conversation_data = f"Complete Conversation History: {json.dumps(filtered_conversation, indent=2)}"
        
        user_prompt = f"""Please generate a complete narrative summary of this adventure arc using the location summaries and plot file provided below:

STRUCTURED PLOT DATA:
{plot_summary}

PARTY STATUS:
Party NPCs: {json.dumps(party_npcs, indent=2)}
Quest Status: {json.dumps(active_quests, indent=2)}

CONVERSATION CONTEXT:
{conversation_data}

Focus on story outcomes, character development, and decisions that will matter in future adventures."""
        
        try:
            response = self.client.chat.completions.create(
                model=config.DM_SUMMARIZATION_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
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
    
    def _archive_conversation_history(self, module_name: str, conversation_history: List[Dict[str, Any]]):
        """Archive the full conversation history for a module before summarization"""
        try:
            # Find next available sequence number
            sequence_num = self._get_next_sequence_number(self.archives_dir, f"{module_name}_conversation", ".json")
            archive_file = os.path.join(self.archives_dir, f"{module_name}_conversation_{sequence_num:03d}.json")
            
            archive_data = {
                "moduleName": module_name,
                "sequenceNumber": sequence_num,
                "archiveDate": datetime.now().isoformat(),
                "conversationHistory": conversation_history,
                "totalMessages": len(conversation_history)
            }
            safe_json_dump(archive_data, archive_file)
            print(f"Archived {len(conversation_history)} conversation messages for {module_name} (sequence {sequence_num:03d})")
        except Exception as e:
            print(f"Warning: Failed to archive conversation history for {module_name}: {e}")
    
    def _load_module_plot_data(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Load module plot data for structured information"""
        try:
            path_manager = ModulePathManager(module_name)
            plot_file = os.path.join(path_manager.module_dir, "module_plot.json")
            
            if os.path.exists(plot_file):
                return safe_json_load(plot_file)
            else:
                print(f"No module_plot.json found for {module_name}")
                return None
        except Exception as e:
            print(f"Error loading plot data for {module_name}: {e}")
            return None
    
    def _get_next_sequence_number(self, directory: str, base_filename: str, extension: str) -> int:
        """Find the next available sequence number for a file series"""
        import glob
        import re
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Find all existing files with the pattern
        pattern = os.path.join(directory, f"{base_filename}_*.{extension.lstrip('.')}")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return 1
        
        # Extract sequence numbers from existing files
        sequence_numbers = []
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            # Match pattern: base_filename_XXX.extension
            match = re.search(rf"{re.escape(base_filename)}_(\d+)\.{re.escape(extension.lstrip('.'))}", filename)
            if match:
                sequence_numbers.append(int(match.group(1)))
        
        # Return next available number
        return max(sequence_numbers) + 1 if sequence_numbers else 1
    
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
    
    def get_module_from_location(self, location_id: str) -> str:
        """Determine module name from location ID - FULLY AGNOSTIC"""
        if not location_id:
            return None
            
        # Use existing ModulePathManager to scan all modules
        modules_dir = "modules"
        if not os.path.exists(modules_dir):
            return None
            
        for module_name in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module_name)
            if os.path.isdir(module_path) and not module_name.startswith('.'):
                try:
                    path_manager = ModulePathManager(module_name)
                    # Check if location exists in this module
                    if self._location_exists_in_module(location_id, path_manager):
                        return module_name
                except:
                    continue
        
        return None
    
    def _location_exists_in_module(self, location_id: str, path_manager: ModulePathManager) -> bool:
        """Check if location ID exists in the given module"""
        import glob
        
        # Scan all area files in the module
        module_dir = path_manager.module_dir
        if not os.path.exists(module_dir):
            return False
            
        for area_file in glob.glob(f"{module_dir}/*.json"):
            # Skip module metadata and plot files
            filename = os.path.basename(area_file)
            if (filename.endswith("_module.json") or 
                filename.endswith("_plot.json") or 
                filename.startswith("module_") or
                filename.startswith("party_")):
                continue
                
            try:
                area_data = safe_json_load(area_file)
                if area_data and "locations" in area_data:
                    locations = area_data["locations"]
                    
                    # Handle both dict and list formats
                    if isinstance(locations, dict):
                        if location_id in locations:
                            return True
                    elif isinstance(locations, list):
                        for location in locations:
                            if isinstance(location, dict) and location.get("locationId") == location_id:
                                return True
            except:
                continue
        return False
    
    def detect_module_transition(self, from_location: str, to_location: str) -> tuple:
        """Detect if transition crosses module boundaries"""
        from_module = self.get_module_from_location(from_location)
        to_module = self.get_module_from_location(to_location)
        
        # Return (is_transition, from_module, to_module)
        if from_module and to_module and from_module != to_module:
            return (True, from_module, to_module)
        return (False, from_module, to_module)
    
    def handle_cross_module_transition(self, from_module: str, to_module: str, 
                                     party_tracker_data: Dict[str, Any], 
                                     conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle automatic summarization when crossing module boundaries"""
        print(f"\nDEBUG: Cross-module transition detected: {from_module} -> {to_module}")
        
        # Auto-summarize the module being left
        if from_module and from_module not in self.campaign_data.get('completedModules', []):
            print(f"DEBUG: Auto-generating summary for {from_module}...")
            
            summary = self._generate_module_summary(from_module, party_tracker_data, conversation_history)
            
            # Save summary with sequential numbering
            sequence_num = self._get_next_sequence_number(self.summaries_dir, f"{from_module}_summary", ".json")
            summary_file = os.path.join(self.summaries_dir, f"{from_module}_summary_{sequence_num:03d}.json")
            
            # Add sequence number to summary data
            summary["sequenceNumber"] = sequence_num
            safe_json_dump(summary, summary_file)
            
            # Update campaign state
            if from_module not in self.campaign_data['completedModules']:
                self.campaign_data['completedModules'].append(from_module)
            
            # Handle module completion export
            self._handle_module_completion_export(from_module, summary)
            
            # Save campaign state
            self.campaign_data['lastUpdated'] = datetime.now().isoformat()
            safe_json_dump(self.campaign_data, self.campaign_file)
            
            print(f"DEBUG: {from_module} summarized and archived")
            return summary
        
        return None
    
    def get_accumulated_summaries_context(self, current_module: str) -> str:
        """Get all relevant module summaries for current module context"""
        context_parts = []
        
        # Add campaign overview
        context_parts.append(f"CAMPAIGN: {self.campaign_data['campaignName']}")
        context_parts.append(f"Current Module: {current_module}")
        
        # Add all completed module summaries (multiple visits per module)
        if self.campaign_data['completedModules']:
            context_parts.append("\\nPREVIOUS ADVENTURES:")
            for module in self.campaign_data['completedModules']:
                summaries = self._load_module_summaries(module)
                if summaries:
                    context_parts.append(f"\\n=== CHRONICLES OF {module.upper()} ===")
                    for i, summary in enumerate(summaries):
                        visit_num = i + 1
                        seq_num = summary.get('sequenceNumber', visit_num)
                        context_parts.append(f"\\n--- Visit {visit_num} (Chronicle {seq_num:03d}) ---")
                        context_parts.append(summary.get('summary', 'No summary available'))
        
        # Add current world state
        if self.campaign_data.get('worldState'):
            context_parts.append("\\nWORLD STATE:")
            for key, value in self.campaign_data['worldState'].items():
                context_parts.append(f"- {key}: {value}")
        
        return "\\n".join(context_parts)


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