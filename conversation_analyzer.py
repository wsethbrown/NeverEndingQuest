#!/usr/bin/env python3
"""
Conversation History Analysis System

This module analyzes conversation history to identify token usage patterns,
location transitions, and compression opportunities for intelligent truncation.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class ConversationAnalyzer:
    """Analyzes conversation structure and calculates compression requirements"""
    
    def __init__(self, conversation_file_path: str):
        """Initialize analyzer with conversation history file path"""
        self.conversation_file_path = Path(conversation_file_path)
        self.conversation_data = None
        self.location_transitions = []
        self.compression_segments = []
        self.analysis_results = {}
        
    def load_conversation(self) -> bool:
        """Load conversation history from JSON file"""
        try:
            if not self.conversation_file_path.exists():
                print(f"Conversation file not found: {self.conversation_file_path}")
                return False
                
            with open(self.conversation_file_path, 'r', encoding='utf-8') as f:
                self.conversation_data = json.load(f)
                
            print(f"Loaded conversation with {len(self.conversation_data)} messages")
            return True
            
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens using word count approximation
        Rule of thumb: 1 token ≈ 0.75 words
        """
        if not text:
            return 0
            
        # Count words (split by whitespace)
        word_count = len(text.split())
        
        # Apply token estimation ratio
        estimated_tokens = int(word_count / 0.75)
        
        return estimated_tokens
    
    def estimate_json_tokens(self, json_data) -> int:
        """Estimate tokens from JSON data including structural overhead"""
        json_string = json.dumps(json_data, separators=(',', ':'))
        return self.estimate_tokens(json_string)
    
    def find_location_transitions(self) -> List[Dict]:
        """
        Scan conversation for location change indicators
        Returns list of transition points with message indices
        """
        if not self.conversation_data:
            return []
            
        transitions = []
        current_location = None
        current_location_id = None
        
        for i, message in enumerate(self.conversation_data):
            # Skip system messages but examine all user and assistant messages
            if message.get('role') == 'system':
                continue
                
            # Look for location updates in tool calls
            for tool_call in message.get('tool_calls', []):
                if tool_call.get('function', {}).get('name') == 'Read':
                    # Check if this is reading party_tracker.json
                    args = tool_call.get('function', {}).get('arguments', {})
                    if 'party_tracker.json' in str(args):
                        # This might indicate a location change - check the result
                        continue
                        
            # Look for location information in message content and tool results
            content = message.get('content', '')
            
            # Also check tool call results that might contain party tracker info
            tool_results = []
            if 'tool_calls' in message:
                for tool_call in message.get('tool_calls', []):
                    result = tool_call.get('result', '')
                    if result and ('party_tracker' in str(result) or 'currentLocation' in str(result)):
                        tool_results.append(result)
            
            # Look for the specific location transition format used in this conversation
            # Pattern: "Location transition: [From Location] ([ID]) to [To Location] ([ID])"
            if message.get('role') == 'user':
                location_transition_match = re.search(
                    r'Location transition:\s*([^(]+)\s*\(([^)]+)\)\s*to\s*([^(]+)\s*\(([^)]+)\)',
                    content
                )
                
                if location_transition_match:
                    from_location = location_transition_match.group(1).strip()
                    from_location_id = location_transition_match.group(2).strip()
                    to_location = location_transition_match.group(3).strip()
                    to_location_id = location_transition_match.group(4).strip()
                    
                    transition = {
                        'message_index': i,
                        'from_location': from_location,
                        'from_location_id': from_location_id,
                        'to_location': to_location,
                        'to_location_id': to_location_id,
                        'timestamp': message.get('timestamp', ''),
                        'message_count_since_last': 0  # Will be calculated later
                    }
                    
                    transitions.append(transition)
                    current_location = to_location
                    current_location_id = to_location_id
                    continue
            
            # Also look for other location patterns in assistant messages
            search_text = content + ' ' + ' '.join(tool_results)
            location_patterns = [
                r'currentLocation["\']?\s*:\s*["\']([^"\']+)["\']',
                r'currentLocationId["\']?\s*:\s*["\']([^"\']+)["\']',
                r'current.?location["\']?\s*:\s*["\']([^"\']+)["\']',
                r'location.*:\s*["\']([^"\']+)["\']',
                r'"currentLocation"\s*:\s*"([^"]+)"',
                r'"currentLocationId"\s*:\s*"([^"]+)"',
                r'transitionLocation.*newLocation.*["\']([^"\']+)["\']'
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                if matches:
                    new_location = matches[0]
                    
                    # Check for location ID pattern
                    location_id_match = re.search(r'currentLocationId["\']?\s*:\s*["\']([^"\']+)["\']', search_text, re.IGNORECASE)
                    new_location_id = location_id_match.group(1) if location_id_match else None
                    
                    # If this is a new location, record the transition
                    if (new_location != current_location or 
                        (new_location_id and new_location_id != current_location_id)):
                        
                        transition = {
                            'message_index': i,
                            'from_location': current_location,
                            'from_location_id': current_location_id,
                            'to_location': new_location,
                            'to_location_id': new_location_id,
                            'timestamp': message.get('timestamp', ''),
                            'message_count_since_last': 0  # Will be calculated later
                        }
                        
                        transitions.append(transition)
                        current_location = new_location
                        current_location_id = new_location_id
                        break
        
        # Calculate message counts between transitions
        for i, transition in enumerate(transitions):
            if i > 0:
                transition['message_count_since_last'] = (
                    transition['message_index'] - transitions[i-1]['message_index']
                )
        
        self.location_transitions = transitions
        return transitions
    
    def calculate_compression_needed(self, target_tokens: int = 10000) -> Dict:
        """Calculate required compression ratio and statistics"""
        if not self.conversation_data:
            return {}
            
        # Separate system vs conversation messages
        system_messages = [msg for msg in self.conversation_data if msg.get('role') == 'system']
        conversation_messages = [msg for msg in self.conversation_data if msg.get('role') != 'system']
        
        # Calculate token counts separately
        total_tokens = self.estimate_json_tokens(self.conversation_data)
        system_tokens = self.estimate_json_tokens(system_messages)
        conversation_tokens = self.estimate_json_tokens(conversation_messages)
        
        # Calculate compression requirements (we can only compress conversation, not system)
        compressible_tokens = conversation_tokens
        if compressible_tokens > target_tokens:
            compression_ratio = (compressible_tokens - target_tokens) / compressible_tokens
            tokens_to_remove = compressible_tokens - target_tokens
        else:
            compression_ratio = 0
            tokens_to_remove = 0
        
        compression_stats = {
            'total_tokens': total_tokens,
            'system_tokens': system_tokens,
            'conversation_tokens': conversation_tokens,
            'compressible_tokens': compressible_tokens,
            'target_tokens': target_tokens,
            'tokens_to_remove': tokens_to_remove,
            'compression_ratio': compression_ratio,
            'compression_percentage': compression_ratio * 100,
            'total_messages': len(self.conversation_data),
            'system_messages': len(system_messages),
            'conversation_messages': len(conversation_messages),
            'total_transitions': len(self.location_transitions)
        }
        
        return compression_stats
    
    def identify_compression_segments(self, preserve_recent_ratio: float = 0.5) -> List[Dict]:
        """
        Group consecutive location transitions for summarization
        Preserves recent activity and targets older segments
        """
        if not self.location_transitions:
            return []
            
        # Sort transitions by message index
        sorted_transitions = sorted(self.location_transitions, key=lambda x: x['message_index'])
        
        # Preserve the most recent percentage of transitions (default 50%)
        preserve_count = max(1, int(len(sorted_transitions) * preserve_recent_ratio))
        transitions_to_compress = sorted_transitions[:-preserve_count] if len(sorted_transitions) > preserve_count else []
        
        if not transitions_to_compress:
            return []
        
        # Group consecutive transitions into segments
        segments = []
        current_segment = []
        
        for i, transition in enumerate(transitions_to_compress):
            current_segment.append(transition)
            
            # Check if we should end this segment
            # End segment if: next transition is far away (>50 messages) or we reach the end
            should_end_segment = (
                i == len(transitions_to_compress) - 1 or  # Last transition
                (i + 1 < len(transitions_to_compress) and 
                 transitions_to_compress[i + 1]['message_index'] - transition['message_index'] > 50)
            )
            
            if should_end_segment and len(current_segment) >= 2:  # Only create segments with 2+ transitions
                segment = {
                    'start_index': current_segment[0]['message_index'],
                    'end_index': current_segment[-1]['message_index'],
                    'transitions': current_segment.copy(),
                    'estimated_tokens': 0,  # Will be calculated
                    'locations_visited': list(set(t['to_location'] for t in current_segment if t['to_location'])),
                    'compression_priority': 'high' if len(current_segment) >= 4 else 'medium'
                }
                
                # Estimate tokens for this segment
                segment_messages = self.conversation_data[segment['start_index']:segment['end_index'] + 1]
                segment['estimated_tokens'] = self.estimate_json_tokens(segment_messages)
                
                segments.append(segment)
                current_segment = []
        
        self.compression_segments = segments
        return segments
    
    def generate_analysis_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        if not self.conversation_data:
            return {}
        
        # Run all analysis steps
        self.find_location_transitions()
        compression_stats = self.calculate_compression_needed()
        compression_segments = self.identify_compression_segments()
        
        # Calculate additional statistics
        total_tokens = compression_stats.get('current_tokens', 0)
        compressible_tokens = sum(seg['estimated_tokens'] for seg in compression_segments)
        
        # Analyze message types
        message_types = defaultdict(int)
        for message in self.conversation_data:
            role = message.get('role', 'unknown')
            message_types[role] += 1
        
        # Generate report
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'conversation_file': str(self.conversation_file_path),
            'compression_statistics': compression_stats,
            'location_analysis': {
                'total_transitions': len(self.location_transitions),
                'unique_locations': len(set(t['to_location'] for t in self.location_transitions if t['to_location'])),
                'transitions_per_location': self._calculate_transitions_per_location(),
                'average_messages_per_transition': self._calculate_avg_messages_per_transition()
            },
            'compression_segments': {
                'total_segments': len(compression_segments),
                'compressible_tokens': compressible_tokens,
                'compression_potential': (compressible_tokens / total_tokens * 100) if total_tokens > 0 else 0,
                'segments': compression_segments
            },
            'message_analysis': {
                'total_messages': len(self.conversation_data),
                'message_types': dict(message_types),
                'average_tokens_per_message': total_tokens / len(self.conversation_data) if self.conversation_data else 0
            },
            'recommendations': self._generate_recommendations(compression_stats, compression_segments)
        }
        
        self.analysis_results = report
        return report
    
    def _calculate_transitions_per_location(self) -> Dict[str, int]:
        """Calculate how many times each location was visited"""
        location_counts = defaultdict(int)
        for transition in self.location_transitions:
            if transition['to_location']:
                location_counts[transition['to_location']] += 1
        return dict(location_counts)
    
    def _calculate_avg_messages_per_transition(self) -> float:
        """Calculate average number of messages between location transitions"""
        if not self.location_transitions:
            return 0.0
            
        message_counts = [t['message_count_since_last'] for t in self.location_transitions if t['message_count_since_last'] > 0]
        return sum(message_counts) / len(message_counts) if message_counts else 0.0
    
    def _generate_recommendations(self, compression_stats: Dict, compression_segments: List[Dict]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        compression_ratio = compression_stats.get('compression_ratio', 0)
        total_segments = len(compression_segments)
        
        if compression_ratio > 0.5:
            recommendations.append("High compression ratio needed (>50%) - consider multi-phase compression")
        elif compression_ratio > 0.3:
            recommendations.append("Moderate compression ratio needed (30-50%) - standard compression approach recommended")
        else:
            recommendations.append("Low compression ratio needed (<30%) - minimal compression required")
        
        if total_segments == 0:
            recommendations.append("No compression segments identified - may need to reduce preservation threshold")
        elif total_segments < 3:
            recommendations.append("Few compression segments available - consider alternative compression strategies")
        else:
            recommendations.append(f"Good compression opportunity with {total_segments} segments identified")
        
        if len(self.location_transitions) > 20:
            recommendations.append("High location transition frequency - excellent candidate for location-based summarization")
        
        return recommendations
    
    def save_analysis(self, output_file: Optional[str] = None) -> str:
        """Save analysis report to JSON file"""
        if not output_file:
            output_file = self.conversation_file_path.parent / "conversation_analysis.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"Analysis report saved to: {output_path}")
        return str(output_path)


def main():
    """Main execution function for standalone use"""
    import sys
    
    # Default conversation file path - always use the main conversation_history.json
    conversation_file = "/mnt/c/dungeon_master_v1/conversation_history.json"
    
    # Allow override from command line only if explicitly provided
    if len(sys.argv) > 1:
        conversation_file = sys.argv[1]
    
    # Create analyzer and run analysis
    analyzer = ConversationAnalyzer(conversation_file)
    
    if not analyzer.load_conversation():
        print("Failed to load conversation file")
        return 1
    
    # Generate analysis report with 10K token target for conversation
    report = analyzer.generate_analysis_report()
    
    # Print summary
    print("\n" + "="*80)
    print("CONVERSATION ANALYSIS SUMMARY")
    print("="*80)
    
    stats = report.get('compression_statistics', {})
    print(f"Total tokens: {stats.get('total_tokens', 0):,}")
    print(f"System prompt tokens: {stats.get('system_tokens', 0):,}")
    print(f"Conversation tokens: {stats.get('conversation_tokens', 0):,}")
    print(f"Target tokens: {stats.get('target_tokens', 0):,}")
    print(f"Compression needed: {stats.get('compression_percentage', 0):.1f}%")
    print(f"Total messages: {stats.get('total_messages', 0):,} ({stats.get('system_messages', 0)} system, {stats.get('conversation_messages', 0)} conversation)")
    print(f"Location transitions: {len(analyzer.location_transitions)}")
    print(f"Compression segments: {len(analyzer.compression_segments)}")
    
    # Save results
    output_file = analyzer.save_analysis()
    
    print(f"\nDetailed analysis saved to: {output_file}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    exit(main())