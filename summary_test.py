import json
import sys
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        print(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}.")
        sys.exit(1)

def trim_conversation(summary_dump):
    # Keep the system message and first two user messages
    trimmed_data = summary_dump[:3]
    
    # Find the last location transition
    last_transition_index = -1
    for i, message in enumerate(summary_dump[3:], start=3):
        if message['role'] == 'system' and 'Location transition:' in message['content']:
            last_transition_index = i

    # If a transition was found, trim everything before it
    if last_transition_index != -1:
        summary_dump = summary_dump[last_transition_index + 1:]
    else:
        summary_dump = summary_dump[3:]  # If no transition, start after initial messages

    # Find the first assistant message after the transition
    first_assistant_index = -1
    for i, message in enumerate(summary_dump):
        if message['role'] == 'assistant':
            first_assistant_index = i
            break

    # If an assistant message was found, trim everything before it
    if first_assistant_index != -1:
        summary_dump = summary_dump[first_assistant_index:]

    # Combine the initial messages with the trimmed conversation
    trimmed_data.extend(summary_dump)

    return trimmed_data

def convert_to_dialogue(trimmed_data):
    dialogue = "Summarize this conversation per instructions:\n\n"
    for message in trimmed_data[3:]:  # Skip the first 3 messages (system and 2 user messages with data)
        if message['role'] == 'assistant':
            dialogue += "Dungeon Master: " + message['content'] + "\n\n"
        elif message['role'] == 'user':
            dialogue += "Player: " + message['content'] + "\n\n"
        elif message['role'] == 'system' and 'Location transition:' in message['content']:
            dialogue += "[" + message['content'] + "]\n\n"
    
    return [
        trimmed_data[0],  # Keep the system message
        {
            "role": "user",
            "content": dialogue.strip()
        }
    ]

def generate_summary(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Make sure this matches the model used in the original script
            temperature=0.7,
            messages=messages
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

if __name__ == "__main__":
    # Load the original summary dump
    dump_data = load_json_file("summary_dump.json")

    # Trim the conversation
    trimmed_data = trim_conversation(dump_data)

    # Save the trimmed summary to a new file (optional)
    with open('trimmed_summary_dump.json', 'w') as f:
        json.dump(trimmed_data, f, indent=2)
    print("Trimmed summary has been saved to 'trimmed_summary_dump.json'")

    # Convert trimmed data to dialogue format
    dialogue_data = convert_to_dialogue(trimmed_data)

    # Save the dialogue format to a new file
    with open('dialogue_summary.json', 'w') as f:
        json.dump(dialogue_data, f, indent=2)
    print("Dialogue summary has been saved to 'dialogue_summary.json'")

    # Generate the summary using the dialogue data
    summary = generate_summary(dialogue_data)

    if summary:
        print("Generated Summary:")
        print(summary)
    else:
        print("Failed to generate summary.")