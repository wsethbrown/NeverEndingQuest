# level_up.py

import json
import re
import os
import time
from datetime import datetime
from jsonschema import validate, ValidationError
from openai import OpenAI
from update_character_info import update_character_info
from jsonschema import validate as jsonschema_validate

def load_schema():
    """Load the unified character schema"""
    with open("char_schema.json", "r") as schema_file:
        return json.load(schema_file)
from config import OPENAI_API_KEY, LEVEL_UP_MODEL, DM_VALIDATION_MODEL
from file_operations import safe_write_json, safe_read_json

client = OpenAI(api_key=OPENAI_API_KEY)

def load_leveling_info():
    with open("leveling_info.txt", "r") as file:
        return file.read().strip()

def read_prompt_from_file(filename):
    """Read a prompt file from the script directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return None

def parse_json_safely(text):
    """Parse JSON from text, handling various formats"""
    # First try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from code block
    try:
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass
    
    # Try to find any JSON-like structure
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass
    
    raise json.JSONDecodeError("Unable to parse JSON from the given text", text, 0)

def validate_leveling_response(response, character_data, current_level, new_level, leveling_info, conversation_history):
    """
    Validate a leveling assistant's response for rule accuracy
    Returns (is_valid, errors, warnings, recommendation)
    """
    print("DEBUG: Validating leveling response...")
    
    # Load validation prompt
    validation_prompt = read_prompt_from_file('leveling_validation_prompt.txt')
    if not validation_prompt:
        print("WARNING: Could not load validation prompt, skipping validation")
        return True, [], [], ""
    
    # Build validation conversation
    validation_conversation = [
        {"role": "system", "content": validation_prompt},
        {"role": "system", "content": f"Current Character Data:\n{json.dumps(character_data, indent=2)}"},
        {"role": "system", "content": f"Leveling from level {current_level} to {new_level}"},
        {"role": "system", "content": f"Leveling Rules:\n{leveling_info}"}
    ]
    
    # Add last 2 exchanges for context if available
    if len(conversation_history) > 4:
        recent_messages = [msg for msg in conversation_history[-4:] if msg["role"] in ["user", "assistant"]]
        validation_conversation.append({
            "role": "system",
            "content": "=== RECENT CONVERSATION CONTEXT ==="
        })
        validation_conversation.extend(recent_messages)
    
    # Add current response to validate
    validation_conversation.append({
        "role": "assistant",
        "content": f"Current response to validate:\n{response}"
    })
    
    try:
        validation_result = client.chat.completions.create(
            model=DM_VALIDATION_MODEL,
            temperature=0.3,  # Low temperature for consistent validation
            messages=validation_conversation
        )
        
        validation_response = validation_result.choices[0].message.content.strip()
        
        try:
            validation_json = parse_json_safely(validation_response)
            is_valid = validation_json.get("valid", False)
            errors = validation_json.get("errors", [])
            warnings = validation_json.get("warnings", [])
            recommendation = validation_json.get("recommendation", "")
            
            # Log validation results
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "character": character_data.get("name", "Unknown"),
                "level_transition": f"{current_level} -> {new_level}",
                "valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "response_snippet": response[:200] + "..." if len(response) > 200 else response
            }
            
            # Append to validation log
            validation_log = safe_read_json("leveling_validation_log.json") or []
            validation_log.append(log_data)
            safe_write_json("leveling_validation_log.json", validation_log)
            
            return is_valid, errors, warnings, recommendation
            
        except Exception as e:
            print(f"Error parsing validation response: {e}")
            return True, [], [], ""  # Default to valid if parsing fails
            
    except Exception as e:
        print(f"Error during validation: {e}")
        return True, [], [], ""  # Default to valid if validation fails

def level_up_character(character_name):
    # Load character data and schema
    file_name = f"{character_name}.json"
    schema = load_schema()

    character_data = safe_read_json(file_name)
    if not character_data:
        print(f"Error: Could not load character data for {character_name}")
        return
    
    current_level = character_data['level']
    new_level = current_level + 1

    # Load leveling information
    leveling_info = load_leveling_info()

    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": f"You are a 5th Edition role playing game character leveling assistant. You're helping level up the character {character_name} from level {current_level} to level {new_level}. Here's the current character data:\n\n{json.dumps(character_data, indent=2)}\n\nAnd here's the leveling information:\n\n{leveling_info}"},
        {"role": "system", "content": "Engage in a natural conversation with the player about leveling up their character. Ask questions about their choices, explain the options available, and guide them through the process. Once all decisions are made, provide a summary of changes."},
        {"role": "system", "content": "After the summary, provide a JSON representation of the updated character data, starting with 'JSON UPDATE:'. Include all fields from the original character data, updating only what has changed due to leveling up."}
    ]

    # Start the leveling conversation
    validation_retry_count = 0
    max_validation_retries = 3
    
    while True:
        response = client.chat.completions.create(
            model=LEVEL_UP_MODEL,
            messages=conversation_history
        )

        assistant_message = response.choices[0].message.content.strip()
        
        # Validate the response before showing to user (except for JSON updates)
        if "JSON UPDATE:" not in assistant_message.upper():
            is_valid, errors, warnings, recommendation = validate_leveling_response(
                assistant_message, 
                character_data, 
                current_level, 
                new_level, 
                leveling_info,
                conversation_history
            )
            
            # Show warnings to user regardless
            if warnings:
                print("\n[VALIDATION WARNINGS]:")
                for warning in warnings:
                    print(f"  ⚠️  {warning}")
            
            # Handle invalid responses
            if not is_valid:
                validation_retry_count += 1
                print(f"\n[VALIDATION ERROR - Attempt {validation_retry_count}/{max_validation_retries}]")
                for error in errors:
                    print(f"  ❌ {error}")
                
                if validation_retry_count < max_validation_retries:
                    # Add correction to conversation for AI to fix
                    correction_message = (
                        "SYSTEM VALIDATION: Your previous response contains rule violations. "
                        f"Errors found: {'; '.join(errors)}. "
                        f"Recommendation: {recommendation} "
                        "Please provide a corrected response that follows 5E rules exactly."
                    )
                    conversation_history.append({"role": "system", "content": correction_message})
                    continue  # Retry with correction
                else:
                    print("\n[VALIDATION FAILED] Too many invalid responses. Proceeding with caution.")
                    print("Please verify all leveling choices follow 5E rules.")
            else:
                validation_retry_count = 0  # Reset counter on valid response
        
        # Display the message to user
        print(f"\nDungeon Master: {assistant_message}")
        conversation_history.append({"role": "assistant", "content": assistant_message})

        if "JSON UPDATE:" in assistant_message.upper():
            break

        user_input = input("\nPlayer: ")
        conversation_history.append({"role": "user", "content": user_input})

    # Extract the JSON update from the assistant's last message
    json_update = assistant_message.split("JSON UPDATE:")[-1].strip()
    
    try:
        updated_character = json.loads(json_update)
        validate(instance=updated_character, schema=schema)
        
        # Final validation of the leveled up character
        final_validation_prompt = (
            "Validate that this final character JSON correctly reflects a level up from "
            f"level {current_level} to {new_level}. Check HP increase, spell slots, "
            "proficiency bonus, and any new features are correct."
        )
        
        is_valid, errors, warnings, recommendation = validate_leveling_response(
            json.dumps(updated_character, indent=2),
            character_data,
            current_level,
            new_level,
            leveling_info,
            conversation_history + [{"role": "system", "content": final_validation_prompt}]
        )
        
        if not is_valid:
            print("\n[FINAL VALIDATION ERROR]")
            print("The final character data has issues:")
            for error in errors:
                print(f"  ❌ {error}")
            print("\nRecommendation:", recommendation)
            print("\nPlease review the character data carefully before saving.")
            
            confirm = input("\nSave anyway? (yes/no): ").lower()
            if confirm != "yes":
                print("Character update cancelled.")
                return
        
        # Save the updated character data using atomic write
        if safe_write_json(file_name, updated_character):
            print(f"\n{character_name} has been successfully leveled up to level {new_level}.")
            
            # Save the conversation history
            # Sanitize the filename for the conversation log
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', character_name.lower())
            conversation_file = f"{safe_name}_level_up_conversation.json"
            if safe_write_json(conversation_file, conversation_history):
                print(f"The level-up conversation has been saved to {conversation_file}")
            else:
                print(f"Warning: Could not save conversation history to {conversation_file}")
        else:
            print(f"Error: Failed to save updated character data for {character_name}")
            print("The character file has not been modified.")
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error updating character data: {e}")
        print("Please review the AI's output and try again.")

if __name__ == "__main__":
    character_name = input("Enter character name: ")
    level_up_character(character_name)