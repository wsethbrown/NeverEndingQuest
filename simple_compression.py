#!/usr/bin/env python3
"""
Simple Conversation Compression

Straightforward approach:
1. Find first location summary (oldest)
2. Find last location summary (newest compression point)
3. Pass ALL messages between those points (inclusive) to AI
4. Replace entire range with single AI chronicle
5. Preserve following location transition
"""

import json
import shutil
from core.generators.location_summarizer import LocationSummarizer
from datetime import datetime

def find_location_summaries(conversation_data):
    """Find all location summary messages"""
    summaries = []
    
    for i, message in enumerate(conversation_data):
        content = message.get('content', '')
        if '=== LOCATION SUMMARY ===' in content:
            # Extract location name from summary
            lines = content.split('\n')
            location_name = "Unknown"
            for line in lines:
                if line.strip() and not line.startswith('===') and ':' in line:
                    location_name = line.split(':')[0].strip()
                    break
            
            summaries.append({
                'index': i,
                'location': location_name,
                'preview': content[:100] + "..." if len(content) > 100 else content
            })
    
    return summaries

def simple_compression():
    """Perform simple compression by compressing range of location summaries"""
    
    print("Simple Conversation Compression")
    print("=" * 40)
    
    # Load original conversation
    with open("modules/conversation_history/conversation_history.json", 'r', encoding='utf-8') as f:
        conversation_data = json.load(f)
    
    print(f"Total messages: {len(conversation_data)}")
    
    # Find all location summaries
    summaries = find_location_summaries(conversation_data)
    print(f"Location summaries found: {len(summaries)}")
    
    if len(summaries) < 2:
        print("Need at least 2 location summaries to compress!")
        return False
    
    # Show summaries for user to choose range
    print("\nLocation summaries:")
    for i, summary in enumerate(summaries):
        print(f"  {i+1}. Message {summary['index']}: {summary['location']}")
    
    # Transition-based compression logic:
    # Trigger: At 20+ transitions, compress all but most recent 10
    total_transitions = len(summaries)
    compression_trigger = 20
    keep_recent = 10
    
    print(f"Transition-based compression:")
    print(f"  Total transitions: {total_transitions}")
    print(f"  Compression trigger: {compression_trigger}")
    print(f"  Keep recent: {keep_recent}")
    
    if total_transitions < compression_trigger:
        print(f"  No compression needed ({total_transitions} < {compression_trigger})")
        return False
    
    # Calculate compression range
    transitions_to_compress = total_transitions - keep_recent
    first_summary_idx = 0
    last_summary_idx = transitions_to_compress - 1
    
    first_message_idx = summaries[first_summary_idx]['index']
    last_message_idx = summaries[last_summary_idx]['index']
    
    print(f"  Compressing {transitions_to_compress} transitions (keeping {keep_recent} recent)")
    print(f"  Range: summary {first_summary_idx} to {last_summary_idx}")
    print(f"  Messages: {first_message_idx} to {last_message_idx}")
    
    print(f"\nCompressing messages {first_message_idx} to {last_message_idx}")
    print(f"From: {summaries[first_summary_idx]['location']}")
    print(f"To: {summaries[last_summary_idx]['location']}")
    
    # Extract ALL messages in the range (inclusive)
    messages_to_compress = conversation_data[first_message_idx:last_message_idx + 1]
    print(f"Messages to compress: {len(messages_to_compress)}")
    
    # Initialize AI summarizer
    summarizer = LocationSummarizer()
    
    try:
        # Generate AI chronicle for the entire range
        result = summarizer.summarize_transition_group(
            start_location=summaries[first_summary_idx]['location'],
            end_location=summaries[last_summary_idx]['location'],
            messages=messages_to_compress,
            intermediate_locations=[s['location'] for s in summaries[first_summary_idx+1:last_summary_idx]]
        )
        
        print(f"\n✅ AI Chronicle Generated!")
        print(f"Original messages: {len(messages_to_compress)}")
        print(f"Original tokens: {result['original_tokens']}")
        print(f"Summary tokens: {result['summary_tokens']}")
        print(f"Compression ratio: {result['compression_ratio']:.1%}")
        
        # Create the compressed conversation
        compressed_conversation = conversation_data.copy()
        
        # Create single AI summary message to replace the entire range
        ai_summary_message = {
            "role": "assistant",
            "content": f"=== LOCATION SUMMARY ===\n\n{result['summary']}"
        }
        
        # Replace the entire range with the single AI summary
        compressed_conversation[first_message_idx:last_message_idx + 1] = [ai_summary_message]
        
        # Save files
        compressed_file = "conversation_history_simple_compressed.json"
        summary_file = "simple_compression_summary.md"
        
        # Save compressed conversation
        with open(compressed_file, 'w', encoding='utf-8') as f:
            json.dump(compressed_conversation, f, indent=2, ensure_ascii=False)
        
        # Create summary document
        summary_content = f"""# Simple Compression Results
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Compression Details
- **Original messages**: {len(conversation_data)}
- **Compressed messages**: {len(compressed_conversation)}
- **Messages removed**: {len(messages_to_compress) - 1}
- **Compression range**: Messages {first_message_idx}-{last_message_idx}

## Journey Compressed
- **From**: {summaries[first_summary_idx]['location']}
- **To**: {summaries[last_summary_idx]['location']}
- **Locations covered**: {len(summaries[first_summary_idx:last_summary_idx+1])} locations

## Compression Stats
- **Original tokens**: {result['original_tokens']:,}
- **Summary tokens**: {result['summary_tokens']:,}
- **Compression ratio**: {result['compression_ratio']:.1%}
- **Events preserved**: {result['events_preserved']}

## AI-Generated Chronicle

{result['summary']}

---

## Files Generated
- `{compressed_file}` - Complete conversation with compression applied
- `{summary_file}` - This summary document

The compression replaces messages {first_message_idx}-{last_message_idx} with a single AI-generated chronicle while preserving the location transition that follows.
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"\n📁 Files created:")
        print(f"  - {compressed_file}")
        print(f"  - {summary_file}")
        
        # Show the compression in context
        print(f"\n📖 Compression Preview:")
        print(f"Original range: Messages {first_message_idx}-{last_message_idx} ({len(messages_to_compress)} messages)")
        print(f"Replaced with: 1 AI summary message")
        
        if last_message_idx + 1 < len(conversation_data):
            next_message = conversation_data[last_message_idx + 1]
            print(f"Following message preserved: {next_message.get('content', '')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during compression: {e}")
        return False

if __name__ == "__main__":
    success = simple_compression()
    if success:
        print(f"\n🎉 Simple compression completed successfully!")
    else:
        print(f"\n💥 Simple compression failed!")