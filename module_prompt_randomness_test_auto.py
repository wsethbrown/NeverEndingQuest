#!/usr/bin/env python3
"""
Module Prompt Randomness Test - Automated Version

This script tests whether the AI generates varied responses when presented with
the same module creation prompt multiple times. It helps identify if the prompt
structure is driving repetitive campaign suggestions.
"""

import json
import time
from openai import OpenAI
from datetime import datetime
import os
import difflib
import sys

# Initialize OpenAI client (using same configuration as main game)
client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

def load_module_creation_prompt():
    """Load the module creation prompt from file"""
    try:
        with open('module_creation_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("ERROR: module_creation_prompt.txt not found")
        return None

def create_test_context():
    """Create a standardized test context to ensure consistent conditions"""
    return """
CURRENT PARTY CONTEXT FOR TESTING:
- Party: Norn (Half-Elf Ranger, Level 8)
- Current Location: Harrow's Hollow 
- Just completed: Keep of Doom module
- Party dynamics: Solo adventurer, experienced with wilderness and combat
- Previous adventures: Dungeon exploration, undead encounters
- Current state: Looking for next adventure

PLAYER INPUT SIMULATION: "What adventures might be available to us now?"
"""

def run_single_test(test_number, base_prompt, context):
    """Run a single test iteration"""
    print(f"Running test #{test_number}...")
    
    # Combine the module creation prompt with test context
    full_prompt = context + "\n\n" + base_prompt
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",  # Same model as main game
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": "What adventures might be available to us now?"}
            ],
            temperature=0.7,  # Use same temperature as main game
            max_tokens=1500
        )
        
        result = response.choices[0].message.content.strip()
        print(f"Test #{test_number} completed")
        return result
        
    except Exception as e:
        print(f"ERROR in test #{test_number}: {e}")
        return None

def analyze_responses(responses):
    """Analyze the responses for similarity and patterns"""
    analysis = {
        'total_responses': len(responses),
        'successful_responses': len([r for r in responses if r is not None]),
        'similarity_scores': [],
        'common_themes': {},
        'unique_elements': set()
    }
    
    # Calculate similarity between all pairs
    valid_responses = [r for r in responses if r is not None]
    
    for i in range(len(valid_responses)):
        for j in range(i + 1, len(valid_responses)):
            similarity = difflib.SequenceMatcher(None, valid_responses[i], valid_responses[j]).ratio()
            analysis['similarity_scores'].append(similarity)
    
    # Extract module names and themes
    for response in valid_responses:
        if response:
            # Look for module names (patterns with underscores)
            import re
            module_matches = re.findall(r'[A-Z][a-zA-Z_]+_[a-zA-Z_]+', response)
            for match in module_matches:
                analysis['unique_elements'].add(f"Module: {match}")
            
            # Look for adventure types
            type_matches = re.findall(r'Adventure Type[:\s]+(dungeon|wilderness|urban|mixed)', response, re.IGNORECASE)
            for match in type_matches:
                theme_key = f"Type: {match.lower()}"
                analysis['common_themes'][theme_key] = analysis['common_themes'].get(theme_key, 0) + 1
    
    return analysis

def save_test_results(responses, analysis):
    """Save test results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"module_randomness_test_{timestamp}.json"
    
    results = {
        'timestamp': timestamp,
        'test_configuration': {
            'model': 'gpt-4-0125-preview',
            'temperature': 0.7,
            'max_tokens': 1500,
            'num_tests': len(responses)
        },
        'responses': responses,
        'analysis': {
            'total_responses': analysis['total_responses'],
            'successful_responses': analysis['successful_responses'],
            'average_similarity': sum(analysis['similarity_scores']) / len(analysis['similarity_scores']) if analysis['similarity_scores'] else 0,
            'max_similarity': max(analysis['similarity_scores']) if analysis['similarity_scores'] else 0,
            'min_similarity': min(analysis['similarity_scores']) if analysis['similarity_scores'] else 0,
            'common_themes': analysis['common_themes'],
            'unique_elements': list(analysis['unique_elements'])
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {filename}")
    return filename

def print_analysis_summary(analysis):
    """Print a summary of the analysis"""
    print("\n" + "="*60)
    print("RANDOMNESS TEST ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"Total Tests Run: {analysis['total_responses']}")
    print(f"Successful Responses: {analysis['successful_responses']}")
    
    if analysis['similarity_scores']:
        avg_similarity = sum(analysis['similarity_scores']) / len(analysis['similarity_scores'])
        print(f"Average Similarity: {avg_similarity:.3f}")
        print(f"Max Similarity: {max(analysis['similarity_scores']):.3f}")
        print(f"Min Similarity: {min(analysis['similarity_scores']):.3f}")
        
        # Interpretation
        if avg_similarity > 0.7:
            print("[WARNING] HIGH SIMILARITY - Responses are very similar (potential repetition issue)")
        elif avg_similarity > 0.4:
            print("[WARNING] MODERATE SIMILARITY - Some repetitive patterns detected")
        else:
            print("[OK] LOW SIMILARITY - Good response variation")
    
    print(f"\nUnique Elements Found: {len(analysis['unique_elements'])}")
    for element in sorted(analysis['unique_elements']):
        print(f"  - {element}")
    
    if analysis['common_themes']:
        print(f"\nCommon Themes:")
        for theme, count in sorted(analysis['common_themes'].items()):
            print(f"  - {theme}: {count} times")

def print_sample_responses(responses, num_samples=2):
    """Print sample responses for manual review"""
    print("\n" + "="*60)
    print("SAMPLE RESPONSES")
    print("="*60)
    
    valid_responses = [r for r in responses if r is not None]
    samples = min(num_samples, len(valid_responses))
    
    for i in range(samples):
        print(f"\n--- Response #{i+1} ---")
        print(valid_responses[i][:500] + "..." if len(valid_responses[i]) > 500 else valid_responses[i])

def main():
    """Main test execution"""
    print("Module Prompt Randomness Test - Automated")
    print("="*40)
    
    # Load the prompt
    base_prompt = load_module_creation_prompt()
    if not base_prompt:
        return
    
    print(f"Loaded module creation prompt ({len(base_prompt)} characters)")
    
    # Set test parameters
    num_tests = 5  # Run 5 tests
    delay = 2      # 2 second delay between tests
    
    print(f"\nRunning {num_tests} tests with {delay}s delay between calls...")
    
    # Create test context
    context = create_test_context()
    
    # Run tests
    responses = []
    for i in range(1, num_tests + 1):
        result = run_single_test(i, base_prompt, context)
        responses.append(result)
        
        if i < num_tests:  # Don't delay after the last test
            time.sleep(delay)
    
    # Analyze results
    print("\nAnalyzing responses...")
    analysis = analyze_responses(responses)
    
    # Save and display results
    filename = save_test_results(responses, analysis)
    print_analysis_summary(analysis)
    
    # Print sample responses for manual review
    print_sample_responses(responses)
    
    print(f"\nDetailed results saved to: {filename}")
    print("\nTest complete!")

if __name__ == "__main__":
    main()