#!/usr/bin/env python3
"""
Gemini AI Tool for Claude
Provides access to Gemini 2.5 Pro for planning, analysis, and handling large files
"""

import os
import json
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

class GeminiTool:
    """Tool for querying Gemini AI with file upload support"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        # Load API key from google_api.pi file
        api_key_file = "google_api.pi"
        if os.path.exists(api_key_file):
            with open(api_key_file, 'r') as f:
                content = f.read().strip()
                # Extract API key from format: api_key=XXX
                if 'api_key=' in content:
                    self.api_key = content.split('api_key=')[1].strip()
                else:
                    self.api_key = content.strip()
        else:
            raise FileNotFoundError(f"API key file {api_key_file} not found")
        
        # Validate API key format
        if not self.api_key or not self.api_key.startswith('AIza'):
            raise ValueError("Invalid API key format")
        
        # Set environment variable for the client
        os.environ['GEMINI_API_KEY'] = self.api_key
        
        # Initialize client
        self.client = genai.Client()
        
        # Default system message for focused responses (can be overridden)
        self.default_system_prompt = """You are an AI assistant helping Claude plan and analyze code.

CRITICAL RULES:
1. Answer ONLY the specific question asked
2. Be concise but complete
3. Provide analysis and planning, NOT full implementations
4. When asked for a plan, give clear steps Claude can execute
5. Focus on the specific feature/issue, not general improvements
6. If code snippets needed, keep them minimal
7. Include specific line numbers or function names when referencing code

Remember: You're helping Claude plan, not doing the work."""
        
        # Conversation history storage - stores conversation history
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

    def upload_files(self, file_paths: List[str], uploaded_files: List) -> None:
        """Upload files to Gemini and append to uploaded_files list"""
        def upload_single_file(file_path: str):
            try:
                print(f"Uploading {file_path}...")
                myfile = self.client.files.upload(file=file_path)
                uploaded_files.append(myfile)
                print(f"Uploaded successfully: {myfile.name}")
                return myfile
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
                return None
        
        # Use parallel uploads for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(upload_single_file, file_paths))
    
    def cleanup_files(self, uploaded_files: List):
        """Delete uploaded files after use"""
        for file in uploaded_files:
            try:
                self.client.files.delete(name=file.name)
                print(f"Cleaned up: {file.name}")
            except Exception as e:
                # Best effort cleanup
                print(f"Failed to cleanup {file.name}: {e}")
    
    def query(self, 
              prompt: str, 
              files: Optional[List[str]] = None,
              model: str = "gemini-2.5-pro",
              temperature: float = 0.7,
              use_system_prompt: bool = True,
              conversation_id: Optional[str] = None,
              stream: bool = False,
              expect_json: bool = False) -> str:
        """
        Query Gemini with optional file attachments
        
        Args:
            prompt: The question or request for Gemini
            files: Optional list of file paths to upload and analyze
            model: Gemini model to use (default: gemini-2.5-pro)
            temperature: Response temperature (default: 0.7)
            use_system_prompt: Whether to include system prompt (default: True)
            conversation_id: Optional ID to track conversation history
            stream: Whether to stream the response (default: False)
            expect_json: Whether to parse response as JSON (default: False)
            
        Returns:
            String response from Gemini (or parsed JSON if expect_json=True)
        """
        uploaded_files = []
        
        try:
            # Get or create conversation history
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                history = self.conversation_history[conversation_id]
            
            # Build message content
            message_parts = []
            
            # Add system prompt
            if use_system_prompt:
                message_parts.append(self.default_system_prompt)
                message_parts.append("\n\n")
            
            # Add conversation history if tracking
            if conversation_id and history:
                for entry in history[-5:]:  # Last 5 exchanges for context
                    message_parts.append(f"User: {entry['user']}")
                    message_parts.append(f"Assistant: {entry['assistant']}")
                    message_parts.append("\n")
            
            # Upload files if provided
            if files:
                self.upload_files(files, uploaded_files)
                # Add uploaded files to message
                for file in uploaded_files:
                    message_parts.append(file)
                    message_parts.append("\n\n")
            
            # Add user prompt
            message_parts.append(prompt)
            
            # Generate response
            print(f"Querying {model}...")
            
            if stream:
                response = self.client.models.generate_content(
                    model=model,
                    contents=message_parts,
                    config=types.GenerateContentConfig(temperature=temperature),
                    stream=True
                )
                full_response = ""
                for chunk in response:
                    chunk_text = chunk.text
                    print(chunk_text, end="", flush=True)
                    full_response += chunk_text
                print()  # New line after streaming
                response_text = full_response
            else:
                response = self.client.models.generate_content(
                    model=model,
                    contents=message_parts,
                    config=types.GenerateContentConfig(temperature=temperature)
                )
                response_text = response.text
            
            # Store in conversation history if tracking
            if conversation_id:
                self.conversation_history[conversation_id].append({
                    'user': prompt,
                    'assistant': response_text
                })
            
            # Parse JSON if expected
            if expect_json:
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code block
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    return {"error": "Failed to parse JSON", "raw_response": response_text}
            
            return response_text
            
        except FileNotFoundError as e:
            return f"File error: {str(e)}"
        except ValueError as e:
            return f"Value error: {str(e)}"
        except Exception as e:
            error_type = type(e).__name__
            return f"Error querying Gemini ({error_type}): {str(e)}"
            
        finally:
            # Always cleanup uploaded files
            if uploaded_files:
                self.cleanup_files(uploaded_files)


# Global instance for easy access
_gemini_tool = None

def get_gemini_tool():
    """Get or create the global Gemini tool instance"""
    global _gemini_tool
    if _gemini_tool is None:
        _gemini_tool = GeminiTool()
    return _gemini_tool


# Convenience function for Claude to use
def query_gemini(prompt: str, 
                 files: Optional[List[str]] = None,
                 model: str = "gemini-2.5-pro",
                 temperature: float = 0.7,
                 use_system_prompt: bool = True,
                 conversation_id: Optional[str] = None,
                 stream: bool = False,
                 expect_json: bool = False) -> Any:
    """
    Query Gemini AI for planning, analysis, or handling large files
    
    Args:
        prompt: Your question or request
        files: Optional list of file paths to analyze
        model: "gemini-2.5-pro" (default) or "gemini-2.5-flash"
        temperature: 0.7 (default) for balanced responses
        use_system_prompt: Include system prompt (default: True, set False to save tokens)
        conversation_id: Optional ID to maintain conversation context
        stream: Stream the response in real-time (default: False)
        expect_json: Parse response as JSON (default: False)
        
    Returns:
        Gemini's response as a string
        
    Example:
        # Simple query
        result = query_gemini("How should I implement feature X?")
        
        # With files
        result = query_gemini(
            "Plan how to add dark mode to this interface",
            files=["templates/game_interface.html"]
        )
        
        # Follow-up in same conversation
        result = query_gemini(
            "What about the mobile version?",
            conversation_id="dark-mode-discussion"
        )
    """
    tool = get_gemini_tool()
    return tool.query(prompt, files, model, temperature, use_system_prompt, conversation_id, stream, expect_json)


# Helper functions for common use cases
def plan_feature(feature_description: str, files: Optional[List[str]] = None, as_json: bool = False) -> Any:
    """Get a plan for implementing a feature"""
    json_instruction = """
Respond with a JSON object in this format:
{
  "files_to_modify": [{"path": "file_path", "changes": ["change1", "change2"]}],
  "steps": ["step1", "step2", ...],
  "challenges": ["challenge1", "challenge2", ...],
  "locations": [{"file": "file_path", "line_range": "100-150", "description": "what to change"}]
}""" if as_json else ""
    
    prompt = f"""Please provide a clear implementation plan for the following feature:

{feature_description}

Include:
1. Specific files/functions to modify
2. Step-by-step approach
3. Potential challenges to watch for
4. Line numbers or section names where changes are needed

Keep the plan concise and actionable.{json_instruction}"""
    
    return query_gemini(prompt, files, expect_json=as_json)


def analyze_large_file(file_path: str, question: str) -> str:
    """Analyze a large file that exceeds Claude's limits"""
    prompt = f"""Analyze this file and answer the following question:

{question}

Focus only on answering the specific question. Include line numbers or function names in your response."""
    
    return query_gemini(prompt, files=[file_path])


def get_unstuck(problem_description: str, context_files: Optional[List[str]] = None) -> str:
    """Get help when stuck on a problem"""
    prompt = f"""I'm stuck on the following problem:

{problem_description}

Please help me understand:
1. What might be causing this issue
2. A suggested approach to debug or solve it
3. Specific things to check or try

Be concise and focus on actionable advice."""
    
    return query_gemini(prompt, context_files)


def suggest_refactoring(file_path: str, focus: Optional[str] = None, as_json: bool = False) -> Any:
    """Get refactoring suggestions for a file"""
    json_instruction = """
Respond with a JSON object in this format:
{
  "refactorings": [
    {
      "priority": 1,
      "type": "extract_function|rename|restructure|etc",
      "location": {"lines": "100-150", "function": "function_name"},
      "description": "what to refactor",
      "rationale": "why this improves the code"
    }
  ]
}""" if as_json else ""
    
    prompt = f"""Please analyze this code and suggest refactoring improvements.
{f'Focus on: {focus}' if focus else ''}

Provide:
1. Top 3-5 refactoring opportunities
2. Specific line numbers/functions to change
3. Brief explanation of why each change improves the code
4. Priority order for changes

Keep suggestions practical and focused.{json_instruction}"""
    
    return query_gemini(prompt, files=[file_path], use_system_prompt=False, expect_json=as_json)


def generate_tests(file_path: str, specific_function: Optional[str] = None) -> str:
    """Get test generation suggestions"""
    prompt = f"""Analyze this code and suggest test cases.
{f'Focus on function: {specific_function}' if specific_function else ''}

Provide:
1. Key test scenarios to cover
2. Edge cases to test
3. Example test structure (brief)
4. Any mocking requirements

Be specific about what to test, not how to implement."""
    
    return query_gemini(prompt, files=[file_path])


def write_documentation(file_path: str, doc_type: str = "docstrings") -> str:
    """Get documentation suggestions"""
    prompt = f"""Analyze this code and suggest {doc_type}.

Provide:
1. Key functions/classes that need documentation
2. Brief suggested content for each
3. Important parameters/returns to document
4. Any complex logic that needs explanation

Keep suggestions concise and focused on clarity."""
    
    return query_gemini(prompt, files=[file_path])


def clear_conversation(conversation_id: str) -> bool:
    """Clear conversation history for a specific ID"""
    tool = get_gemini_tool()
    if hasattr(tool, 'conversation_history') and conversation_id in tool.conversation_history:
        tool.conversation_history.pop(conversation_id, None)
        return True
    return False


if __name__ == "__main__":
    # Test the tool
    print("Testing Gemini Tool...")
    result = query_gemini("What is 2+2? Answer in one word.")
    print(f"Response: {result}")