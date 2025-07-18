#!/usr/bin/env python3
"""
Generate Compression Output Files

Creates two output files:
1. conversation_history_compressed.json - Full conversation with AI summary applied
2. generated_summary_only.md - Just the AI-generated summary for review
"""

import json
import shutil
from pathlib import Path
from conversation_analyzer import ConversationAnalyzer
from location_summarizer import LocationSummarizer
from datetime import datetime

def create_compression_outputs():
    """Generate both compressed conversation and standalone summary files"""
    
    print("Generating Compression Output Files")
    print("=" * 50)
    
    # Step 1: Create a copy of the original conversation history
    source_file = "modules/conversation_history/conversation_history.json"
    backup_file = "conversation_history_backup.json"
    compressed_file = "conversation_history_compressed.json"
    summary_file = "generated_summary_only.md"
    
    # Create backup
    print(f"Creating backup: {backup_file}")
    shutil.copy2(source_file, backup_file)
    
    # Create working copy for compression
    print(f"Creating working copy: {compressed_file}")
    shutil.copy2(source_file, compressed_file)
    
    # Step 2: Initialize analysis components
    analyzer = ConversationAnalyzer(compressed_file)
    if not analyzer.load_conversation():
        print("Failed to load conversation data!")
        return False
    
    print(f"Loaded conversation with {len(analyzer.conversation_data)} messages")
    
    # Step 3: Find transitions and segments
    transitions = analyzer.find_location_transitions()
    segments = analyzer.identify_compression_segments()
    
    print(f"Found {len(transitions)} location transitions")
    print(f"Identified {len(segments)} compression segments")
    
    if not segments:
        print("No compression segments found - nothing to compress")
        return False
    
    # Step 4: Process each segment for compression
    summarizer = LocationSummarizer()
    all_summaries = []
    
    for i, segment in enumerate(segments):
        print(f"\nProcessing segment {i+1}/{len(segments)}")
        print(f"  Transitions: {len(segment['transitions'])}")
        print(f"  Locations: {', '.join(segment['locations_visited'][:3])}{'...' if len(segment['locations_visited']) > 3 else ''}")
        
        # Extract segment data
        start_idx = segment['start_index']
        end_idx = segment['end_index']
        segment_messages = analyzer.conversation_data[start_idx:end_idx + 1]
        
        start_location = segment['transitions'][0]['from_location'] if segment['transitions'] else "Unknown"
        end_location = segment['transitions'][-1]['to_location'] if segment['transitions'] else "Unknown"
        intermediate_locations = segment['locations_visited'][1:-1] if len(segment['locations_visited']) > 2 else []
        
        print(f"  From: {start_location}")
        print(f"  To: {end_location}")
        print(f"  Messages: {len(segment_messages)}")
        
        # Generate AI summary
        try:
            result = summarizer.summarize_transition_group(
                start_location=start_location,
                end_location=end_location,
                messages=segment_messages,
                intermediate_locations=intermediate_locations
            )
            
            print(f"  ✅ Summary generated: {result['original_tokens']} → {result['summary_tokens']} tokens ({result['compression_ratio']:.1%} compression)")
            
            # Store summary info
            summary_info = {
                'segment_index': i,
                'start_location': start_location,
                'end_location': end_location,
                'intermediate_locations': intermediate_locations,
                'original_message_count': len(segment_messages),
                'original_tokens': result['original_tokens'],
                'summary_tokens': result['summary_tokens'],
                'compression_ratio': result['compression_ratio'],
                'events_preserved': result['events_preserved'],
                'summary_text': result['summary'],
                'message_indices': f"{start_idx}-{end_idx}"
            }
            all_summaries.append(summary_info)
            
            # Replace the segment in the conversation with a single summary message
            summary_message = {
                "role": "assistant",
                "content": f"Location transition summary: {start_location} to {end_location}\n\n{result['summary']}"
            }
            
            # Replace the segment messages with the single summary message
            analyzer.conversation_data[start_idx:end_idx + 1] = [summary_message]
            
            # Adjust indices for subsequent segments
            adjustment = len(segment_messages) - 1  # How many messages we removed
            for j in range(i + 1, len(segments)):
                segments[j]['start_index'] -= adjustment
                segments[j]['end_index'] -= adjustment
                for transition in segments[j]['transitions']:
                    transition['message_index'] -= adjustment
            
        except Exception as e:
            print(f"  ❌ Error generating summary: {e}")
            continue
    
    # Step 5: Save the compressed conversation
    print(f"\nSaving compressed conversation to: {compressed_file}")
    with open(compressed_file, 'w', encoding='utf-8') as f:
        json.dump(analyzer.conversation_data, f, indent=2, ensure_ascii=False)
    
    # Step 6: Generate standalone summary file
    print(f"Generating standalone summary file: {summary_file}")
    
    summary_content = f"""# AI-Generated Conversation Summaries
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

This document contains the AI-generated chronicle summaries that were used to compress the conversation history.

## Compression Overview
- **Original conversation**: {len(analyzer.conversation_data) + sum(len(s.get('segment_messages', [])) for s in all_summaries)} messages
- **Compressed conversation**: {len(analyzer.conversation_data)} messages  
- **Segments processed**: {len(all_summaries)}
- **Total summaries generated**: {len(all_summaries)}

---

"""
    
    for i, summary in enumerate(all_summaries):
        summary_content += f"""## Summary {i+1}: {summary['start_location']} → {summary['end_location']}

**Journey Path**: {summary['start_location']}"""
        
        if summary['intermediate_locations']:
            summary_content += f" → {' → '.join(summary['intermediate_locations'])}"
        
        summary_content += f" → {summary['end_location']}\n\n"
        
        summary_content += f"""**Compression Stats**:
- Original messages: {summary['original_message_count']}
- Original tokens: {summary['original_tokens']:,}
- Summary tokens: {summary['summary_tokens']:,}
- Compression ratio: {summary['compression_ratio']:.1%}
- Events preserved: {summary['events_preserved']}
- Message indices: {summary['message_indices']}

**AI-Generated Chronicle**:

{summary['summary_text']}

---

"""
    
    # Add review guidelines
    summary_content += """## Review Guidelines

When reviewing these summaries, please check for:

1. **Narrative Quality**: Does the prose feel immersive and fantasy-appropriate?
2. **Information Preservation**: Are important character actions, items, and plot points retained?
3. **Chronological Flow**: Does the sequence of events make sense?
4. **Character Details**: Are character names and specific actions preserved?
5. **Combat Descriptions**: Are fights depicted with appropriate stakes and outcomes?
6. **Environmental Details**: Are location-specific discoveries and atmosphere captured?

## Feedback Areas

- **Missing Information**: What critical details were lost?
- **Narrative Issues**: Where does the prose feel generic or unclear?
- **Continuity Problems**: What doesn't flow properly?
- **Tone Concerns**: Where does the fantasy voice break down?

---

*These summaries replace the original detailed conversation logs to reduce token usage while preserving story continuity.*
"""
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    # Step 7: Generate final report
    print(f"\n✅ Compression Complete!")
    print(f"📁 Files generated:")
    print(f"  - {backup_file} (original backup)")
    print(f"  - {compressed_file} (compressed conversation)")
    print(f"  - {summary_file} (standalone summaries for review)")
    
    # Calculate final stats
    original_size = Path(source_file).stat().st_size
    compressed_size = Path(compressed_file).stat().st_size
    size_reduction = (original_size - compressed_size) / original_size
    
    print(f"\n📊 Final Statistics:")
    print(f"  - File size reduction: {size_reduction:.1%}")
    print(f"  - Original size: {original_size:,} bytes")
    print(f"  - Compressed size: {compressed_size:,} bytes")
    print(f"  - Summaries generated: {len(all_summaries)}")
    print(f"  - Total events preserved: {sum(s['events_preserved'] for s in all_summaries)}")
    
    return True

if __name__ == "__main__":
    success = create_compression_outputs()
    if success:
        print(f"\n🎉 Output files generated successfully!")
        print(f"\nNext steps:")
        print(f"1. Review 'generated_summary_only.md' for summary quality")
        print(f"2. Check 'conversation_history_compressed.json' for proper integration")
        print(f"3. Provide feedback on narrative quality and information preservation")
    else:
        print(f"\n💥 Failed to generate output files!")