#!/usr/bin/env python3
"""
Gemini AI Tool for Claude
Provides access to Gemini 2.5 Pro for planning, analysis, and handling large files
"""

import os
import json
import time
import pickle
from typing import List, Optional, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
import google.api_core.exceptions

class GeminiTool:
    """Tool for querying Gemini AI with file upload support"""
    
    def __init__(self, model: str = "gemini-2.5-pro", temperature: float = 0.7):
        """Initialize Gemini client with API key and default settings"""
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
        
        # Default settings
        self.default_model = model
        self.default_temperature = temperature
        
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
        
        # Conversation history storage - stores native Gemini format
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # File upload sessions
        self.file_sessions: Dict[str, List[Any]] = {}
        
        # Rate limiting for Gemini Pro (2 RPM)
        self.last_request_time = 0
        self.min_request_interval = 30.0  # 30 seconds between requests for 2 RPM

    @retry(wait=wait_exponential_jitter(initial=1, max=60), stop=stop_after_attempt(3))
    def _upload_single_file(self, file_path: str) -> Any:
        """Upload a single file with retry logic"""
        try:
            print(f"Uploading {file_path}...")
            myfile = self.client.files.upload(file=file_path)
            print(f"Uploaded successfully: {myfile.name}")
            return myfile
        except Exception as e:
            print(f"Upload failed for {file_path}: {e}")
            raise
    
    def upload_files_for_session(self, file_paths: List[str], session_id: Optional[str] = None) -> List[Any]:
        """Upload files once and store for reuse in session"""
        uploaded_files = []
        
        # Use parallel uploads for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._upload_single_file, fp) for fp in file_paths]
            for future in futures:
                try:
                    file_obj = future.result()
                    if file_obj:
                        uploaded_files.append(file_obj)
                except Exception as e:
                    print(f"Failed to upload file: {e}")
                    # Continue with other files
        
        # Store in session if ID provided
        if session_id and uploaded_files:
            self.file_sessions[session_id] = uploaded_files
        
        return uploaded_files
    
    def get_session_files(self, session_id: str) -> List[Any]:
        """Get previously uploaded files for a session"""
        return self.file_sessions.get(session_id, [])
    
    def cleanup_session_files(self, session_id: str) -> None:
        """Clean up files for a specific session"""
        if session_id in self.file_sessions:
            self.cleanup_files(self.file_sessions[session_id])
            del self.file_sessions[session_id]
    
    def cleanup_files(self, uploaded_files: List):
        """Delete uploaded files after use"""
        for file in uploaded_files:
            try:
                self.client.files.delete(name=file.name)
                print(f"Cleaned up: {file.name}")
            except Exception as e:
                # Best effort cleanup
                print(f"Failed to cleanup {file.name}: {e}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting for Gemini Pro (2 RPM)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"Rate limiting: sleeping for {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @retry(wait=wait_exponential_jitter(initial=1, max=60), stop=stop_after_attempt(3))
    def _generate_content_with_retry(self, model: str, contents: List[Dict], 
                                     temperature: float, stream: bool) -> str:
        """Generate content with retry logic"""
        try:
            if stream:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=temperature),
                    stream=True
                )
                full_response = ""
                for chunk in response:
                    chunk_text = chunk.text
                    print(chunk_text, end="", flush=True)
                    full_response += chunk_text
                print()  # New line after streaming
                return full_response
            else:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=temperature)
                )
                return response.text
        except Exception as e:
            print(f"Generation failed: {e}. Retrying...")
            raise
    
    def count_tokens(self, contents: Union[str, List[Dict]]) -> int:
        """Count tokens for content before sending"""
        try:
            # Create a model instance for token counting
            model = genai.GenerativeModel(self.default_model)
            
            # Handle both string prompts and conversation history
            if isinstance(contents, str):
                result = model.count_tokens(contents)
            else:
                result = model.count_tokens(contents)
            
            return result.total_tokens
        except Exception as e:
            print(f"Token counting failed: {e}")
            return -1
    
    def save_conversations(self, filepath: str = "gemini_conversations.pkl"):
        """Save all conversations to disk"""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self.conversation_history, f)
            print(f"Saved {len(self.conversation_history)} conversations to {filepath}")
        except Exception as e:
            print(f"Failed to save conversations: {e}")
    
    def load_conversations(self, filepath: str = "gemini_conversations.pkl"):
        """Load conversations from disk"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.conversation_history = pickle.load(f)
                print(f"Loaded {len(self.conversation_history)} conversations from {filepath}")
            else:
                print(f"No saved conversations found at {filepath}")
        except Exception as e:
            print(f"Failed to load conversations: {e}")
    
    def query(self, 
              prompt: str, 
              files: Optional[List[str]] = None,
              file_handles: Optional[List[Any]] = None,
              file_session_id: Optional[str] = None,
              model: Optional[str] = None,
              temperature: Optional[float] = None,
              use_system_prompt: bool = True,
              conversation_id: Optional[str] = None,
              stream: bool = False,
              expect_json: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Query Gemini with optional file attachments
        
        Args:
            prompt: The question or request for Gemini
            files: Optional list of file paths to upload and analyze
            file_handles: Optional list of pre-uploaded file handles
            file_session_id: Optional session ID to reuse uploaded files
            model: Gemini model to use (default: from init)
            temperature: Response temperature (default: from init)
            use_system_prompt: Whether to include system prompt (default: True)
            conversation_id: Optional ID to track conversation history
            stream: Whether to stream the response (default: False)
            expect_json: Whether to parse response as JSON (default: False)
            
        Returns:
            String response from Gemini (or parsed JSON if expect_json=True)
        """
        uploaded_files = []
        
        try:
            # Use configured defaults if not specified
            model = model if model is not None else self.default_model
            temperature = temperature if temperature is not None else self.default_temperature
            
            # Rate limiting
            self._enforce_rate_limit()
            
            # Build conversation in native Gemini format
            contents = []
            
            # Get or create conversation history
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                    # Add system prompt as first exchange if requested
                    if use_system_prompt:
                        self.conversation_history[conversation_id].extend([
                            {"role": "user", "parts": [{"text": self.default_system_prompt}]},
                            {"role": "model", "parts": [{"text": "Understood. I'll help Claude plan and analyze code as requested."}]}
                        ])
                # Use existing history
                contents = list(self.conversation_history[conversation_id])
            elif use_system_prompt:
                # One-off query with system prompt
                contents = [
                    {"role": "user", "parts": [{"text": self.default_system_prompt + "\n\n" + prompt}]}
                ]
            
            # Build current message parts
            current_parts = []
            
            # Handle files - prioritize file_handles, then session, then upload new
            file_objects = []
            if file_handles:
                file_objects = file_handles
            elif file_session_id and file_session_id in self.file_sessions:
                file_objects = self.file_sessions[file_session_id]
            elif files:
                uploaded_files = self.upload_files_for_session(files)
                file_objects = uploaded_files
            
            # Add files to current message
            for file_obj in file_objects:
                current_parts.append(file_obj)
            
            # Add prompt text
            current_parts.append({"text": prompt})
            
            # Add current message to contents
            if conversation_id and contents:
                # Append to conversation
                contents.append({"role": "user", "parts": current_parts})
            elif not contents:
                # New conversation without system prompt
                contents = [{"role": "user", "parts": current_parts}]
            
            # Generate response with retry logic
            print(f"Querying {model}...")
            response_text = self._generate_content_with_retry(
                model=model,
                contents=contents,
                temperature=temperature,
                stream=stream
            )
            
            # Store in conversation history if tracking (native format)
            if conversation_id:
                # Only add the user message if we didn't already add it above
                if not (contents and contents[-1].get("role") == "user"):
                    self.conversation_history[conversation_id].append(
                        {"role": "user", "parts": current_parts}
                    )
                # Add model response
                self.conversation_history[conversation_id].append(
                    {"role": "model", "parts": [{"text": response_text}]}
                )
            
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
            
        except google.api_core.exceptions.PermissionDenied as e:
            return f"Permission denied: Check your API key. {str(e)}"
        except google.api_core.exceptions.InvalidArgument as e:
            return f"Invalid argument: {str(e)}"
        except google.api_core.exceptions.ResourceExhausted as e:
            return f"Quota exceeded: {str(e)}"
        except google.api_core.exceptions.TooManyRequests as e:
            return f"Rate limit exceeded: {str(e)}"
        except FileNotFoundError as e:
            return f"File error: {str(e)}"
        except ValueError as e:
            return f"Value error: {str(e)}"
        except Exception as e:
            error_type = type(e).__name__
            return f"Error querying Gemini ({error_type}): {str(e)}"
            
        finally:
            # Cleanup only if we uploaded new files (not reusing session files)
            if 'uploaded_files' in locals() and uploaded_files:
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
    return tool.query(
        prompt=prompt, 
        files=files, 
        model=model, 
        temperature=temperature, 
        use_system_prompt=use_system_prompt, 
        conversation_id=conversation_id, 
        stream=stream, 
        expect_json=expect_json
    )


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


# New helper functions for file session management
def upload_files_once(files: List[str], session_id: str) -> List[Any]:
    """Upload files once and store them for reuse"""
    tool = get_gemini_tool()
    return tool.upload_files_for_session(files, session_id)


def query_with_session(prompt: str, session_id: str, **kwargs) -> Any:
    """Query using previously uploaded files from session"""
    tool = get_gemini_tool()
    return tool.query(prompt, file_session_id=session_id, **kwargs)


def cleanup_session(session_id: str) -> None:
    """Clean up files for a specific session"""
    tool = get_gemini_tool()
    tool.cleanup_session_files(session_id)


def check_token_count(prompt: str, conversation_id: Optional[str] = None) -> int:
    """Check token count before sending a query"""
    tool = get_gemini_tool()
    
    if conversation_id and conversation_id in tool.conversation_history:
        # Count tokens for full conversation
        contents = list(tool.conversation_history[conversation_id])
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        return tool.count_tokens(contents)
    else:
        # Count tokens for single prompt
        return tool.count_tokens(prompt)


def save_all_conversations(filepath: str = "gemini_conversations.pkl") -> None:
    """Save all conversation history to disk"""
    tool = get_gemini_tool()
    tool.save_conversations(filepath)


def load_all_conversations(filepath: str = "gemini_conversations.pkl") -> None:
    """Load conversation history from disk"""
    tool = get_gemini_tool()
    tool.load_conversations(filepath)


if __name__ == "__main__":
    # Test the tool
    print("Testing Gemini Tool...")
    result = query_gemini("What is 2+2? Answer in one word.")
    print(f"Response: {result}")