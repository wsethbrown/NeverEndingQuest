#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Token Estimation Utilities

Provides accurate token counting utilities for conversation analysis and compression.
Uses empirical ratios and handles JSON formatting overhead for precise estimates.
"""

import json
import re
from typing import Union, Dict, List, Any


class TokenEstimator:
    """Accurate token counting utilities for text and JSON data"""
    
    # Token estimation constants based on empirical testing
    WORDS_PER_TOKEN = 0.75  # Average words per token
    JSON_OVERHEAD_RATIO = 1.1  # JSON formatting adds ~10% overhead
    
    def __init__(self):
        """Initialize token estimator with calibration data"""
        self.calibration_data = []
        self.accuracy_metrics = {}
    
    @staticmethod
    def estimate_tokens_from_text(text: str) -> int:
        """
        Estimate tokens from plain text using word-based approximation
        
        Args:
            text: Input text string
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Clean and normalize text
        cleaned_text = TokenEstimator._clean_text(text)
        
        # Count words (more sophisticated than simple split)
        word_count = TokenEstimator._count_words(cleaned_text)
        
        # Apply token estimation ratio
        estimated_tokens = int(word_count / TokenEstimator.WORDS_PER_TOKEN)
        
        return max(1, estimated_tokens)  # Ensure minimum of 1 token
    
    @staticmethod
    def estimate_tokens_from_json(json_data: Union[Dict, List, str]) -> int:
        """
        Estimate tokens from JSON data including structural overhead
        
        Args:
            json_data: JSON data (dict, list, or JSON string)
            
        Returns:
            Estimated token count including JSON formatting
        """
        if isinstance(json_data, str):
            # Already a JSON string
            json_string = json_data
        else:
            # Convert to compact JSON string
            json_string = json.dumps(json_data, separators=(',', ':'), ensure_ascii=False)
        
        # Get base token estimate
        base_tokens = TokenEstimator.estimate_tokens_from_text(json_string)
        
        # Apply JSON overhead
        total_tokens = int(base_tokens * TokenEstimator.JSON_OVERHEAD_RATIO)
        
        return total_tokens
    
    @staticmethod
    def estimate_conversation_tokens(conversation_data: List[Dict]) -> Dict[str, int]:
        """
        Estimate tokens for conversation data with detailed breakdown
        
        Args:
            conversation_data: List of conversation messages
            
        Returns:
            Dictionary with token breakdown
        """
        if not conversation_data:
            return {'total': 0, 'messages': 0, 'content': 0, 'metadata': 0}
        
        total_tokens = 0
        content_tokens = 0
        metadata_tokens = 0
        
        for message in conversation_data:
            # Calculate tokens for this message
            message_tokens = TokenEstimator.estimate_tokens_from_json(message)
            total_tokens += message_tokens
            
            # Break down content vs metadata
            content = message.get('content', '')
            if content:
                content_tokens += TokenEstimator.estimate_tokens_from_text(content)
            
            # Metadata is everything else
            metadata_dict = {k: v for k, v in message.items() if k != 'content'}
            metadata_tokens += TokenEstimator.estimate_tokens_from_json(metadata_dict)
        
        return {
            'total': total_tokens,
            'messages': len(conversation_data),
            'content': content_tokens,
            'metadata': metadata_tokens,
            'avg_per_message': total_tokens / len(conversation_data) if conversation_data else 0
        }
    
    @staticmethod
    def estimate_compression_savings(original_tokens: int, summary_length: int) -> Dict[str, Union[int, float]]:
        """
        Calculate potential token savings from compression
        
        Args:
            original_tokens: Original token count
            summary_length: Length of summary in words
            
        Returns:
            Dictionary with compression metrics
        """
        # Estimate summary tokens
        summary_tokens = int(summary_length / TokenEstimator.WORDS_PER_TOKEN)
        
        # Calculate savings
        tokens_saved = original_tokens - summary_tokens
        compression_ratio = tokens_saved / original_tokens if original_tokens > 0 else 0
        
        return {
            'original_tokens': original_tokens,
            'summary_tokens': summary_tokens,
            'tokens_saved': tokens_saved,
            'compression_ratio': compression_ratio,
            'compression_percentage': compression_ratio * 100,
            'efficiency': tokens_saved / summary_tokens if summary_tokens > 0 else 0
        }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text for accurate word counting"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but keep punctuation
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @staticmethod
    def _count_words(text: str) -> int:
        """Count words with handling for special cases"""
        if not text:
            return 0
        
        # Split on whitespace and filter empty strings
        words = [word for word in text.split() if word.strip()]
        
        # Adjust for contractions and hyphenated words
        adjusted_count = 0
        for word in words:
            # Count contractions as separate tokens
            if "'" in word:
                adjusted_count += len(word.split("'"))
            # Count hyphenated words as separate tokens
            elif "-" in word and len(word) > 1:
                adjusted_count += len([part for part in word.split("-") if part])
            else:
                adjusted_count += 1
        
        return adjusted_count
    
    def calibrate_estimates(self, actual_tokens: int, estimated_tokens: int, context: str = ""):
        """
        Add calibration data to improve accuracy
        
        Args:
            actual_tokens: Actual token count from API
            estimated_tokens: Our estimated token count
            context: Context for this calibration (e.g., "conversation", "summary")
        """
        calibration_point = {
            'actual': actual_tokens,
            'estimated': estimated_tokens,
            'error': abs(actual_tokens - estimated_tokens),
            'error_percentage': abs(actual_tokens - estimated_tokens) / actual_tokens * 100 if actual_tokens > 0 else 0,
            'context': context
        }
        
        self.calibration_data.append(calibration_point)
        self._update_accuracy_metrics()
    
    def _update_accuracy_metrics(self):
        """Update accuracy metrics based on calibration data"""
        if not self.calibration_data:
            return
        
        errors = [point['error'] for point in self.calibration_data]
        error_percentages = [point['error_percentage'] for point in self.calibration_data]
        
        self.accuracy_metrics = {
            'total_calibrations': len(self.calibration_data),
            'average_error': sum(errors) / len(errors),
            'average_error_percentage': sum(error_percentages) / len(error_percentages),
            'max_error': max(errors),
            'min_error': min(errors),
            'accuracy_within_10_percent': sum(1 for p in error_percentages if p <= 10.0) / len(error_percentages) * 100
        }
    
    def get_accuracy_report(self) -> Dict:
        """Get accuracy report based on calibration data"""
        if not self.calibration_data:
            return {'status': 'No calibration data available'}
        
        return {
            'calibration_summary': self.accuracy_metrics,
            'calibration_data': self.calibration_data,
            'recommendations': self._generate_accuracy_recommendations()
        }
    
    def _generate_accuracy_recommendations(self) -> List[str]:
        """Generate recommendations for improving accuracy"""
        recommendations = []
        
        if not self.accuracy_metrics:
            return ["Collect calibration data to assess accuracy"]
        
        avg_error_pct = self.accuracy_metrics.get('average_error_percentage', 0)
        
        if avg_error_pct > 20:
            recommendations.append("High estimation error - consider adjusting WORDS_PER_TOKEN ratio")
        elif avg_error_pct > 10:
            recommendations.append("Moderate estimation error - collect more calibration data")
        else:
            recommendations.append("Good estimation accuracy - continue current approach")
        
        accuracy_within_10 = self.accuracy_metrics.get('accuracy_within_10_percent', 0)
        if accuracy_within_10 < 70:
            recommendations.append("Less than 70% of estimates within 10% - investigate systematic bias")
        
        return recommendations


def validate_token_estimates(estimated: int, actual: int = None, tolerance: float = 0.15) -> Dict:
    """
    Validate token estimates against actual counts
    
    Args:
        estimated: Estimated token count
        actual: Actual token count (if available)
        tolerance: Acceptable error tolerance (default 15%)
        
    Returns:
        Validation results dictionary
    """
    if actual is None:
        return {
            'status': 'no_actual_count',
            'estimated': estimated,
            'message': 'No actual count available for validation'
        }
    
    error = abs(estimated - actual)
    error_percentage = (error / actual * 100) if actual > 0 else 0
    within_tolerance = error_percentage <= (tolerance * 100)
    
    return {
        'status': 'validated',
        'estimated': estimated,
        'actual': actual,
        'error': error,
        'error_percentage': error_percentage,
        'within_tolerance': within_tolerance,
        'tolerance_percentage': tolerance * 100,
        'accuracy_rating': 'good' if within_tolerance else 'needs_improvement'
    }


def estimate_batch_tokens(texts: List[str]) -> List[Dict]:
    """
    Estimate tokens for a batch of texts
    
    Args:
        texts: List of text strings
        
    Returns:
        List of dictionaries with text and token estimates
    """
    results = []
    
    for i, text in enumerate(texts):
        token_count = TokenEstimator.estimate_tokens_from_text(text)
        results.append({
            'index': i,
            'text_length': len(text),
            'word_count': len(text.split()) if text else 0,
            'estimated_tokens': token_count
        })
    
    return results


def main():
    """Main function for testing token estimation"""
    # Test cases
    test_texts = [
        "Hello world!",
        "This is a longer sentence with more words to test the token estimation accuracy.",
        json.dumps({"test": "data", "numbers": [1, 2, 3], "nested": {"key": "value"}}),
        ""
    ]
    
    print("Token Estimation Test Results")
    print("=" * 50)
    
    estimator = TokenEstimator()
    
    for i, text in enumerate(test_texts):
        print(f"\nTest {i + 1}:")
        print(f"Text: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"Length: {len(text)} characters")
        print(f"Words: {len(text.split()) if text else 0}")
        
        if text.startswith('{'):
            # JSON test
            tokens = TokenEstimator.estimate_tokens_from_json(text)
            print(f"Estimated tokens (JSON): {tokens}")
        else:
            # Text test
            tokens = TokenEstimator.estimate_tokens_from_text(text)
            print(f"Estimated tokens (text): {tokens}")
    
    print("\n" + "=" * 50)
    print("Token estimation testing completed")


if __name__ == "__main__":
    main()