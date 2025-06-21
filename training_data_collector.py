#!/usr/bin/env python3
"""
Training Data Collector
Captures conversation history (input) and AI responses (output) for training data
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class TrainingDataCollector:
    """Collects input/output pairs for training data"""
    
    def __init__(self, output_file: str = "training_data.json"):
        self.output_file = output_file
        self.data = self.load_existing_data()
    
    def load_existing_data(self) -> List[Dict]:
        """Load existing training data if file exists"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load existing training data: {e}")
                return []
        return []
    
    def add_training_example(self, conversation_history: List[Dict], ai_response: str):
        """Add a new training example"""
        training_example = {
            "timestamp": datetime.now().isoformat(),
            "input": conversation_history,
            "output": ai_response,
            "example_id": len(self.data) + 1
        }
        
        self.data.append(training_example)
        self.save_data()
        
        print(f"Added training example #{training_example['example_id']}")
    
    def save_data(self):
        """Save training data to file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving training data: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about collected data"""
        return {
            "total_examples": len(self.data),
            "file_size_mb": os.path.getsize(self.output_file) / (1024*1024) if os.path.exists(self.output_file) else 0,
            "latest_timestamp": self.data[-1]["timestamp"] if self.data else None
        }

# Global collector instance
collector = TrainingDataCollector()

def log_training_data(conversation_history: List[Dict], ai_response: str):
    """Simple function to log training data"""
    collector.add_training_example(conversation_history, ai_response)

def get_training_stats():
    """Get training data statistics"""
    return collector.get_stats()