#!/usr/bin/env python3
"""
Simple Training Data Collector for Web Interface
Captures input/output pairs during gameplay
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

class SimpleTrainingCollector:
    """Simple collector that just captures input->output pairs"""
    
    def __init__(self, output_file: str = "training_data.json"):
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
        """Log complete AI interaction for training"""
        # Create training example with full conversation as input
        training_example = {
            "id": self._get_next_id(),
            "timestamp": datetime.now().isoformat(),
            "input": full_message_history,  # Complete conversation history sent to AI
            "output": ai_response  # Complete AI response
        }
        
        # Save to file
        self._append_to_file(training_example)
        
        print(f"[LOGGED] Training example #{training_example['id']}")
    
    def _get_next_id(self) -> int:
        """Get next available ID"""
        if not os.path.exists(self.output_file):
            return 1
        
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return max(item.get('id', 0) for item in data) + 1
                return 1
        except:
            return 1
    
    def _append_to_file(self, training_example: Dict):
        """Append training example to file"""
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
        
        # Save back
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