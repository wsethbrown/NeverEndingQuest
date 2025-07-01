#!/usr/bin/env python3
"""
Simple Training Data Collector for Web Interface
Captures input/output pairs during gameplay for OpenAI fine-tuning
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

class SimpleTrainingCollector:
    """Simple collector that captures conversations in OpenAI fine-tuning format"""
    
    def __init__(self, output_file: str = "training/training_data.json"):
        self.output_file = output_file
        self.current_conversation = []
        
    def add_user_input(self, user_input: str):
        """Add user input to current conversation"""
        self.current_conversation.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_complete_interaction(self, full_message_history: List[Dict], ai_response: str):
        """Log complete AI interaction for training in OpenAI fine-tuning format"""
        # Convert to OpenAI fine-tuning format
        messages = []
        
        # Extract messages from conversation history
        for msg in full_message_history:
            if msg.get("role") in ["system", "user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add the AI response as the assistant message
        messages.append({
            "role": "assistant", 
            "content": ai_response
        })
        
        # Create training example in OpenAI format
        training_example = {
            "messages": messages
        }
        
        # Save to file
        self._append_to_file(training_example)
        
        print(f"[LOGGED] Training example with {len(messages)} messages")
    
    def _append_to_file(self, training_example: Dict):
        """Append training example to file in OpenAI format"""
        # Ensure training directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Load existing data
        data = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
            except:
                data = []
        
        # Add new example
        data.append(training_example)
        
        # Save back with pretty formatting
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Error saving training data: {e}")

# Global collector
collector = SimpleTrainingCollector()

def log_complete_interaction(full_message_history: List[Dict], ai_response: str):
    """Log complete AI interaction for training"""
    collector.log_complete_interaction(full_message_history, ai_response)