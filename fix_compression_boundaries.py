#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Fix Compression Boundaries

This script fixes the compression algorithm to properly identify which messages
should be compressed vs. which are already summaries that should be preserved.
"""

import json
import shutil
from pathlib import Path
from conversation_analyzer import ConversationAnalyzer
from location_summarizer import LocationSummarizer
from datetime import datetime

def identify_compression_candidates(conversation_data):
    """
    Identify which message ranges need compression by finding consecutive
    user/assistant exchanges that aren't already summaries
    """
    compression_candidates = []
    current_segment = []
    
    for i, message in enumerate(conversation_data):
        role = message.get('role', '')
        content = message.get('content', '')
        
        # Skip system messages
        if role == 'system':
            if current_segment:
                # End current segment before system message
                compression_candidates.append({
                    'start_index': current_segment[0],
                    'end_index': current_segment[-1],
                    'message_indices': current_segment.copy()
                })
                current_segment = []
            continue
            
        # Check if this is already a location summary or transition
        is_summary = (
            "=== LOCATION SUMMARY ===" in content or
            "Location transition summary:" in content or
            "Location transition:" in content or
            len(content) > 500  # Assume long messages are summaries
        )
        
        if is_summary:
            if current_segment:
                # End current segment before summary
                compression_candidates.append({
                    'start_index': current_segment[0],
                    'end_index': current_segment[-1],
                    'message_indices': current_segment.copy()
                })
                current_segment = []
        else:
            # This is a regular message that could be compressed
            current_segment.append(i)
    
    # Add final segment if exists
    if current_segment:
        compression_candidates.append({
            'start_index': current_segment[0],
            'end_index': current_segment[-1],
            'message_indices': current_segment.copy()
        })
    
    # Filter out segments that are too small to compress
    compression_candidates = [
        segment for segment in compression_candidates 
        if len(segment['message_indices']) >= 5  # Only compress segments with 5+ messages
    ]
    
    return compression_candidates

def analyze_conversation_structure():
    """Analyze the current conversation to understand its structure"""
    
    print("Analyzing Conversation Structure")
    print("=" * 50)
    
    # Load the original conversation
    with open("modules/conversation_history/conversation_history.json", 'r', encoding='utf-8') as f:
        conversation_data = json.load(f)
    
    print(f"Total messages: {len(conversation_data)}")
    
    # Analyze message types
    message_types = {}
    summaries = []
    
    for i, message in enumerate(conversation_data):
        role = message.get('role', '')
        content = message.get('content', '')
        
        if role not in message_types:
            message_types[role] = 0
        message_types[role] += 1
        
        # Identify summaries
        if ("=== LOCATION SUMMARY ===" in content or 
            "Location transition summary:" in content or
            "Location transition:" in content):
            summaries.append({
                'index': i,
                'role': role,
                'type': 'location_summary' if "LOCATION SUMMARY" in content else 'transition_summary',
                'preview': content[:100] + "..." if len(content) > 100 else content
            })
    
    print(f"\nMessage types: {message_types}")
    print(f"\nExisting summaries found: {len(summaries)}")
    
    for summary in summaries:
        print(f"  [{summary['index']}] {summary['type']}: {summary['preview']}")
    
    # Find compression candidates
    candidates = identify_compression_candidates(conversation_data)
    
    print(f"\nCompression candidates: {len(candidates)}")
    for i, candidate in enumerate(candidates):
        start_idx = candidate['start_index']
        end_idx = candidate['end_index']
        msg_count = len(candidate['message_indices'])
        
        start_preview = conversation_data[start_idx]['content'][:50] + "..."
        end_preview = conversation_data[end_idx]['content'][:50] + "..."
        
        print(f"  Candidate {i+1}: Messages {start_idx}-{end_idx} ({msg_count} messages)")
        print(f"    Start: {start_preview}")
        print(f"    End: {end_preview}")
    
    return conversation_data, candidates, summaries

def create_corrected_compression():
    """Create a properly compressed conversation file"""
    
    print("\nCreating Corrected Compression")
    print("=" * 30)
    
    conversation_data, candidates, existing_summaries = analyze_conversation_structure()
    
    if not candidates:
        print("No compression candidates found!")
        return False
    
    # Create corrected version
    corrected_file = "conversation_history_corrected.json"
    summary_file = "corrected_summaries_only.md"
    
    # Work on a copy
    corrected_conversation = conversation_data.copy()
    summarizer = LocationSummarizer()
    generated_summaries = []
    
    # Process candidates in reverse order to maintain indices
    for candidate in reversed(candidates):
        start_idx = candidate['start_index']
        end_idx = candidate['end_index']
        segment_messages = conversation_data[start_idx:end_idx + 1]
        
        print(f"\nProcessing candidate: messages {start_idx}-{end_idx}")
        print(f"  Messages to compress: {len(segment_messages)}")
        
        # Try to determine locations from nearby messages
        start_location = "Unknown Location"
        end_location = "Unknown Location"
        
        # Look for location context in nearby messages
        context_start = max(0, start_idx - 3)
        context_end = min(len(conversation_data), end_idx + 4)
        
        for i in range(context_start, context_end):
            content = conversation_data[i].get('content', '')
            
            # Look for location transition patterns
            if "Location transition:" in content:
                if "to" in content:
                    parts = content.split("to")
                    if len(parts) >= 2:
                        end_location = parts[-1].strip().split("(")[0].strip()
                        if len(parts[0].split(":")) >= 2:
                            start_location = parts[0].split(":")[-1].strip().split("(")[0].strip()
                        break
        
        try:
            # Generate AI summary for this segment
            result = summarizer.summarize_transition_group(
                start_location=start_location,
                end_location=end_location,
                messages=segment_messages,
                intermediate_locations=[]
            )
            
            print(f"  ✅ Generated summary: {result['original_tokens']} → {result['summary_tokens']} tokens")
            
            # Create summary message
            summary_message = {
                "role": "assistant",
                "content": f"Location transition summary: {start_location} to {end_location}\n\n{result['summary']}"
            }
            
            # Replace the segment with the summary
            corrected_conversation[start_idx:end_idx + 1] = [summary_message]
            
            # Store summary info
            generated_summaries.append({
                'original_start': start_idx,
                'original_end': end_idx,
                'start_location': start_location,
                'end_location': end_location,
                'original_messages': len(segment_messages),
                'original_tokens': result['original_tokens'],
                'summary_tokens': result['summary_tokens'],
                'compression_ratio': result['compression_ratio'],
                'summary_text': result['summary']
            })
            
        except Exception as e:
            print(f"  ❌ Error generating summary: {e}")
            continue
    
    # Save corrected conversation
    print(f"\nSaving corrected conversation: {corrected_file}")
    with open(corrected_file, 'w', encoding='utf-8') as f:
        json.dump(corrected_conversation, f, indent=2, ensure_ascii=False)
    
    # Generate summary file
    print(f"Generating summary file: {summary_file}")
    
    summary_content = f"""# Corrected AI Compression Results
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Compression Overview
- **Original messages**: {len(conversation_data)}
- **Corrected messages**: {len(corrected_conversation)}
- **Segments compressed**: {len(generated_summaries)}
- **Existing summaries preserved**: {len(existing_summaries)}

## Analysis Results

### Existing Summaries (Preserved)
These summaries were already in the conversation and were NOT replaced:

"""
    
    for summary in existing_summaries:
        summary_content += f"- **Message {summary['index']}**: {summary['type']}\n"
        summary_content += f"  Preview: {summary['preview']}\n\n"
    
    summary_content += "### New AI-Generated Summaries\n\n"
    
    for i, summary in enumerate(generated_summaries):
        summary_content += f"""## Summary {i+1}: {summary['start_location']} → {summary['end_location']}

**Original Message Range**: {summary['original_start']}-{summary['original_end']}
**Compression Stats**:
- Original messages: {summary['original_messages']}
- Original tokens: {summary['original_tokens']:,}
- Summary tokens: {summary['summary_tokens']:,}
- Compression ratio: {summary['compression_ratio']:.1%}

**AI-Generated Chronicle**:

{summary['summary_text']}

---

"""
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"\n✅ Corrected compression complete!")
    print(f"📁 Files created:")
    print(f"  - {corrected_file} (corrected conversation)")
    print(f"  - {summary_file} (analysis and summaries)")
    
    return True

if __name__ == "__main__":
    success = create_corrected_compression()
    if success:
        print(f"\n🎉 Corrected compression files generated!")
        print(f"\nThe corrected version should properly:")
        print(f"1. Preserve existing location summaries")
        print(f"2. Only compress raw conversation exchanges")
        print(f"3. Maintain proper message boundaries")
    else:
        print(f"\n💥 Failed to create corrected compression!")