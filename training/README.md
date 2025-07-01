# Training Data Collection System

This folder contains the training data collection system for the D&D 5e Dungeon Master AI. The system automatically captures conversation data during gameplay to create datasets suitable for OpenAI fine-tuning.

## Overview

The training data collector captures complete conversation interactions between players and the AI Dungeon Master, storing them in OpenAI's fine-tuning format. This data can be used to train custom models that understand the game's specific context, rules, and storytelling style.

## How It Works

### Automatic Collection
- The system automatically logs every AI interaction during gameplay
- No manual intervention required - runs seamlessly in the background
- Captures full conversation context including system prompts, user messages, and AI responses

### Data Format
Training data is stored in OpenAI's fine-tuning format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "System prompt with game rules and context..."
    },
    {
      "role": "user", 
      "content": "Player's action or message..."
    },
    {
      "role": "assistant",
      "content": "AI Dungeon Master's response..."
    }
  ]
}
```

### File Structure
- `training_data.json` - Main training dataset file (JSONL format as array)
- Each entry represents one complete conversation turn
- Pretty-formatted JSON with 2-space indentation for readability

## Technical Implementation

### Core Components
- **SimpleTrainingCollector**: Main collector class handling data capture
- **OpenAI Format Conversion**: Automatically converts internal conversation format to OpenAI standard
- **Incremental Saving**: Appends new interactions to existing dataset without data loss

### Integration Points
- Integrated into `main.py` at the AI response generation level
- Captures full conversation history sent to AI models
- Logs complete AI responses including all JSON actions

### Data Flow
1. Player submits action/message
2. System builds full conversation history with context
3. AI generates response
4. Training collector captures: conversation history + AI response
5. Data is formatted and appended to training dataset

## Usage for Fine-Tuning

### Preparing Data
The collected data is ready for OpenAI fine-tuning with minimal preparation:

1. **Format**: Already in OpenAI's required format
2. **Quality**: Contains real gameplay interactions with proper context
3. **Diversity**: Captures various game scenarios, character interactions, and storytelling elements

### Training Considerations
- **Dataset Size**: Monitor file size - larger datasets generally improve model performance
- **Data Quality**: All interactions include full game context (character stats, location data, plot state)
- **Conversation Length**: Each training example includes complete conversation context for better model understanding

### File Management
- Training data automatically accumulates during normal gameplay
- Large files may need splitting for fine-tuning upload limits
- Consider periodic archiving of older training data

## Configuration

### Default Settings
- **Output File**: `training/training_data.json`
- **Format**: OpenAI fine-tuning format
- **Encoding**: UTF-8 with proper Unicode support
- **Pretty Printing**: 2-space indentation for readability

### Customization
The collector can be configured by modifying the `SimpleTrainingCollector` initialization in the code:

```python
# Default: saves to training/training_data.json
collector = SimpleTrainingCollector()

# Custom path:
collector = SimpleTrainingCollector("custom/path/training_data.json")
```

## Data Privacy and Security

### What's Collected
- Player actions and messages
- AI responses and generated content
- Game context (character stats, location data, plot information)
- Complete conversation history for context

### What's NOT Collected
- Personal identifying information
- Real-world user data
- System passwords or sensitive configuration

### Best Practices
- Regularly review collected data for any sensitive content
- Consider data retention policies for long-running campaigns
- Ensure compliance with any applicable privacy regulations

## Troubleshooting

### Common Issues
- **File Permission Errors**: Ensure write access to training folder
- **JSON Format Errors**: Usually indicates corruption - check recent entries
- **Large File Size**: Consider archiving or splitting files if needed

### Debug Information
The collector provides console output for successful logging:
```
[LOGGED] Training example with 15 messages
```

### Error Handling
- Graceful failure: errors don't interrupt gameplay
- Error messages logged to console with `[ERROR]` prefix
- Malformed data is skipped rather than corrupting the entire dataset

## Performance Impact

### Minimal Overhead
- Lightweight data capture process
- No impact on AI response generation speed
- Efficient incremental file appending

### Storage Considerations
- Training data files grow over time
- Typical size: ~1MB per 10-20 conversation turns
- Monitor disk space for long-running campaigns

---

*This training data system enables continuous improvement of the AI Dungeon Master through real gameplay interactions, creating increasingly sophisticated and context-aware gaming experiences.*