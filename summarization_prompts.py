#!/usr/bin/env python3
"""
Refined Prompts for AI Summarization

This module contains specialized prompts for AI-powered conversation summarization,
designed to preserve critical game information while maintaining narrative continuity.
"""

from typing import Dict, List, Any


class SummarizationPrompts:
    """Collection of refined prompts for different summarization scenarios"""
    
    # Chronicle-style narrative prompt based on ChatGPT example
    CHRONICLE_SUMMARY_PROMPT = """
Create a detailed chronicle-style summary of the player's journey from {start_location} to {end_location}.

FORMAT REQUIREMENTS:
- Use rich narrative prose with emotional beats and environmental storytelling
- Preserve specific character names, dialogue quotes, and story details
- Maintain chronological flow between locations
- Include actual discoveries, items, and plot developments
- Capture the atmosphere and tension of each location

STRUCTURE:
🧭 CHRONICLE SUMMARY — From {start_location} to {end_location}

[Opening paragraph: Key actions, dialogue, and discoveries at the origin point]

[Middle paragraphs: Journey through each intermediate location with:
- Environmental details and atmosphere
- Specific NPC interactions with actual dialogue
- Combat encounters with participants and outcomes
- Items found/used with names and significance
- Character progression and state changes
- Plot revelations and quest developments]

[Final paragraph: Arrival at destination with narrative tension and decisions faced]

[Closing line: Reflective or forward-facing conclusion]

CRITICAL PRESERVATION:
- Character names and relationships
- Specific dialogue and quotes
- Item names and their significance
- Combat participants and outcomes
- Plot developments and quest changes
- Environmental discoveries and lore

LOCATIONS VISITED:
{location_list}

ORIGINAL CONVERSATION:
{message_content}

Write in the style of an epic fantasy chronicle that captures the drama and significance of this journey segment."""

    # Prompt for multi-location journeys
    MULTI_LOCATION_SUMMARY_PROMPT = """
Create a comprehensive summary of the player's activities across multiple locations:

START: {start_location}
INTERMEDIATE: {intermediate_locations}
END: {end_location}

Preserve ALL critical information including combat statistics, NPC interactions, inventory changes, character progression, and plot developments. Ensure no loss of game-mechanical data while condensing narrative flow.

CONVERSATION SEGMENT TO SUMMARIZE:
{message_content}

CRITICAL EVENTS IDENTIFIED:
{critical_events}

Focus on:
1. Journey progression and location connections
2. Combat encounters with specific outcomes
3. Character state changes (HP, spells, items, experience)
4. NPC relationships and dialogue outcomes
5. Plot progression and quest updates
6. Environmental discoveries and their implications

Maintain D&D 5e mechanical accuracy and preserve all actionable information for future reference.
"""

    # Prompt for combat-heavy segments
    COMBAT_FOCUSED_SUMMARY_PROMPT = """
Summarize this combat-heavy segment from {start_location} to {end_location}.

COMBAT PRESERVATION REQUIREMENTS:
- Initiative order and participant actions
- Attack rolls, damage dealt, and tactical decisions
- Spell usage and resource expenditure
- Combat outcomes and character state changes
- Environmental factors affecting combat
- Loot and experience gained

ORIGINAL COMBAT SEGMENT:
{message_content}

IDENTIFIED COMBAT EVENTS:
{combat_events}

Create a detailed but concise summary that preserves all mechanical information while condensing repetitive narrative elements. Ensure future combat balance relies on accurate resource tracking.
"""

    # Prompt for NPC-heavy segments
    NPC_INTERACTION_SUMMARY_PROMPT = """
Summarize the player's social interactions from {start_location} to {end_location}.

NPC INTERACTION PRESERVATION:
- Character names and key personality traits
- Important dialogue and conversation outcomes
- Relationship changes and trust levels
- Quest information shared or received
- Trade agreements and exchanges
- Social consequences of player actions

ORIGINAL CONVERSATION SEGMENT:
{message_content}

IDENTIFIED NPC INTERACTIONS:
{npc_events}

Focus on preserving dialogue outcomes that affect future interactions, quest progression, and social standing. Maintain character voices and relationship dynamics.
"""

    # Prompt for exploration-heavy segments
    EXPLORATION_SUMMARY_PROMPT = """
Summarize the player's exploration activities from {start_location} to {end_location}.

EXPLORATION PRESERVATION REQUIREMENTS:
- Areas searched and methods used
- Hidden discoveries and secret areas found
- Traps encountered and their outcomes
- Environmental obstacles and solutions
- Map connectivity and area relationships
- Clues and lore discovered

ORIGINAL EXPLORATION SEGMENT:
{message_content}

IDENTIFIED DISCOVERIES:
{discovery_events}

Preserve all environmental knowledge that affects future navigation and decision-making. Maintain accuracy of area connections and discovered secrets.
"""

    # Prompt for mixed content segments
    COMPREHENSIVE_SUMMARY_PROMPT = """
Create a comprehensive summary of all activities from {start_location} to {end_location}.

This segment contains mixed activities including combat, exploration, NPC interactions, and character development. Preserve ALL critical information across all categories:

COMBAT: {combat_summary}
NPC INTERACTIONS: {npc_summary}
EXPLORATION: {exploration_summary}
CHARACTER CHANGES: {character_summary}
PLOT PROGRESSION: {plot_summary}

ORIGINAL CONVERSATION SEGMENT:
{message_content}

Create a well-structured summary that maintains narrative flow while preserving all mechanical and story information. Organize content logically and ensure no critical data is lost.
"""

    # Prompt for emergency compression (high compression ratio needed)
    EMERGENCY_COMPRESSION_PROMPT = """
EMERGENCY COMPRESSION NEEDED: Reduce this segment by at least 70% while preserving only the most critical information.

JOURNEY: {start_location} to {end_location}

ABSOLUTE PRESERVATION PRIORITIES:
1. Character death/revival events
2. Level advancement and major ability gains
3. Quest completion or major plot revelations
4. Permanent inventory changes (major items gained/lost)
5. Relationship changes affecting future story

ORIGINAL SEGMENT:
{message_content}

CRITICAL EVENTS ONLY:
{critical_events}

Create an ultra-compressed summary focusing ONLY on information that directly impacts future gameplay. Sacrifice narrative detail for mechanical accuracy.
"""

    @classmethod
    def get_prompt_for_scenario(cls, scenario_type: str, **kwargs) -> str:
        """
        Get the appropriate prompt template for a given scenario
        
        Args:
            scenario_type: Type of scenario (location_transition, multi_location, combat_heavy, etc.)
            **kwargs: Template variables for prompt formatting
            
        Returns:
            Formatted prompt string
        """
        prompt_mapping = {
            'location_transition': cls.LOCATION_TRANSITION_SUMMARY_PROMPT,
            'multi_location': cls.MULTI_LOCATION_SUMMARY_PROMPT,
            'combat_heavy': cls.COMBAT_FOCUSED_SUMMARY_PROMPT,
            'npc_heavy': cls.NPC_INTERACTION_SUMMARY_PROMPT,
            'exploration_heavy': cls.EXPLORATION_SUMMARY_PROMPT,
            'comprehensive': cls.COMPREHENSIVE_SUMMARY_PROMPT,
            'emergency': cls.EMERGENCY_COMPRESSION_PROMPT
        }
        
        template = prompt_mapping.get(scenario_type, cls.LOCATION_TRANSITION_SUMMARY_PROMPT)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
    
    @classmethod
    def determine_best_prompt(cls, events: List[Dict], compression_ratio: float) -> str:
        """
        Determine the best prompt type based on event analysis
        
        Args:
            events: List of identified events
            compression_ratio: Required compression ratio
            
        Returns:
            Best prompt type identifier
        """
        # Emergency compression for high ratios
        if compression_ratio > 0.7:
            return 'emergency'
        
        # Analyze event types
        event_types = [event.get('type', '') for event in events]
        combat_count = event_types.count('combat')
        npc_count = event_types.count('npc_interaction')
        exploration_count = event_types.count('discovery')
        
        total_events = len(events)
        
        if total_events == 0:
            return 'location_transition'
        
        # Determine dominant activity type
        if combat_count / total_events > 0.6:
            return 'combat_heavy'
        elif npc_count / total_events > 0.6:
            return 'npc_heavy'
        elif exploration_count / total_events > 0.6:
            return 'exploration_heavy'
        elif total_events > 10:  # Complex mixed scenario
            return 'comprehensive'
        else:
            return 'location_transition'
    
    @classmethod
    def format_events_for_prompt(cls, events: List[Dict]) -> Dict[str, str]:
        """
        Format events data for prompt templates
        
        Args:
            events: List of identified events
            
        Returns:
            Dictionary with formatted event summaries
        """
        formatted = {
            'combat_events': [],
            'npc_events': [],
            'discovery_events': [],
            'character_events': [],
            'plot_events': [],
            'critical_events': []
        }
        
        for event in events:
            event_type = event.get('type', '')
            description = event.get('description', '')
            importance = event.get('importance', 'minor')
            
            if importance == 'critical':
                formatted['critical_events'].append(description)
            
            if event_type == 'combat':
                formatted['combat_events'].append(description)
            elif event_type == 'npc_interaction':
                formatted['npc_events'].append(description)
            elif event_type == 'discovery':
                formatted['discovery_events'].append(description)
            elif event_type == 'character_state':
                formatted['character_events'].append(description)
            elif event_type == 'plot':
                formatted['plot_events'].append(description)
        
        # Convert lists to formatted strings
        return {
            'combat_summary': '; '.join(formatted['combat_events']) if formatted['combat_events'] else 'No combat encounters',
            'npc_summary': '; '.join(formatted['npc_events']) if formatted['npc_events'] else 'No NPC interactions',
            'exploration_summary': '; '.join(formatted['discovery_events']) if formatted['discovery_events'] else 'No discoveries',
            'character_summary': '; '.join(formatted['character_events']) if formatted['character_events'] else 'No character changes',
            'plot_summary': '; '.join(formatted['plot_events']) if formatted['plot_events'] else 'No plot progression',
            'critical_events': '; '.join(formatted['critical_events']) if formatted['critical_events'] else 'No critical events',
            'combat_events': formatted['combat_events'],
            'npc_events': formatted['npc_events'],
            'discovery_events': formatted['discovery_events']
        }


class PromptOptimizer:
    """Optimize prompts based on model performance and feedback"""
    
    def __init__(self):
        self.performance_history = []
        self.optimization_rules = {}
    
    def track_prompt_performance(self, prompt_type: str, original_tokens: int, 
                                summary_tokens: int, quality_score: float, 
                                information_preserved: float):
        """Track performance metrics for prompt optimization"""
        performance_data = {
            'prompt_type': prompt_type,
            'original_tokens': original_tokens,
            'summary_tokens': summary_tokens,
            'compression_ratio': (original_tokens - summary_tokens) / original_tokens,
            'quality_score': quality_score,
            'information_preserved': information_preserved,
            'efficiency': information_preserved / (summary_tokens / original_tokens) if original_tokens > 0 else 0
        }
        
        self.performance_history.append(performance_data)
    
    def get_optimization_suggestions(self, prompt_type: str) -> List[str]:
        """Get suggestions for improving prompt performance"""
        relevant_performance = [
            p for p in self.performance_history 
            if p['prompt_type'] == prompt_type
        ]
        
        if not relevant_performance:
            return ["No performance data available for this prompt type"]
        
        avg_compression = sum(p['compression_ratio'] for p in relevant_performance) / len(relevant_performance)
        avg_quality = sum(p['quality_score'] for p in relevant_performance) / len(relevant_performance)
        avg_preservation = sum(p['information_preserved'] for p in relevant_performance) / len(relevant_performance)
        
        suggestions = []
        
        if avg_compression < 0.3:
            suggestions.append("Consider more aggressive compression instructions")
        if avg_quality < 0.7:
            suggestions.append("Add more specific quality requirements to prompt")
        if avg_preservation < 0.8:
            suggestions.append("Emphasize information preservation more strongly")
        
        return suggestions if suggestions else ["Prompt performance is satisfactory"]


def main():
    """Test prompt formatting and optimization"""
    print("Summarization Prompts Test")
    print("=" * 50)
    
    # Test event formatting
    test_events = [
        {'type': 'combat', 'description': 'Defeated orc warrior', 'importance': 'important'},
        {'type': 'npc_interaction', 'description': 'Spoke with village elder', 'importance': 'critical'},
        {'type': 'discovery', 'description': 'Found hidden treasure chest', 'importance': 'important'}
    ]
    
    formatted_events = SummarizationPrompts.format_events_for_prompt(test_events)
    print("Formatted events:")
    for key, value in formatted_events.items():
        print(f"  {key}: {value}")
    
    # Test prompt selection
    best_prompt = SummarizationPrompts.determine_best_prompt(test_events, 0.4)
    print(f"\nBest prompt type: {best_prompt}")
    
    # Test prompt generation
    try:
        prompt = SummarizationPrompts.get_prompt_for_scenario(
            'location_transition',
            start_location="Cave Entrance",
            end_location="Underground Chamber",
            intermediate_locations="Narrow Tunnel",
            location_details="Dark passage with dripping water",
            message_content="Test conversation content"
        )
        print(f"\nGenerated prompt length: {len(prompt)} characters")
        print("Prompt generation successful!")
    except Exception as e:
        print(f"Prompt generation failed: {e}")


if __name__ == "__main__":
    main()