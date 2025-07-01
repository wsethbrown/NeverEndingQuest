#!/usr/bin/env python3
"""
Gemini AI Tool for Claude
Provides access to Gemini 2.5 Pro for planning, analysis, and handling large files
"""

import os
from typing import List, Optional
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
        
        # Conversation history storage
        self.conversation_history = []

    def upload_files(self, file_paths: List[str]) -> List:
        """Upload files to Gemini and return file objects"""
        uploaded_files = []
        for file_path in file_paths:
            try:
                print(f"Uploading {file_path}...")
                myfile = self.client.files.upload(file=file_path)
                uploaded_files.append(myfile)
                print(f"Uploaded successfully: {myfile.name}")
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
        return uploaded_files
    
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
              conversation_id: Optional[str] = None) -> str:
        """
        Query Gemini with optional file attachments
        
        Args:
            prompt: The question or request for Gemini
            files: Optional list of file paths to upload and analyze
            model: Gemini model to use (default: gemini-2.5-pro)
            temperature: Response temperature (default: 0.7)
            use_system_prompt: Whether to include system prompt (default: True)
            conversation_id: Optional ID to track conversation history
            
        Returns:
            String response from Gemini
        """
        uploaded_files = []
        
        try:
            # Build contents array
            contents = []
            
            # Add system prompt if requested (saves ~100 tokens when skipped)
            if use_system_prompt:
                contents.append(self.default_system_prompt)
                contents.append("\n\n")
            
            # Add conversation history if tracking
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                history = self.conversation_history[conversation_id]
                for entry in history[-10:]:  # Last 10 exchanges for context
                    contents.append(f"User: {entry['user']}")
                    contents.append(f"Assistant: {entry['assistant']}")
                    contents.append("\n")
            
            # Upload files if provided
            if files:
                uploaded_files = self.upload_files(files)
                # Add uploaded files to contents
                for file in uploaded_files:
                    contents.append(file)
                    contents.append("\n\n")
            
            # Add user prompt
            contents.append(prompt)
            
            # Generate response
            print(f"Querying {model}...")
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature
                    # Note: Gemini 2.5 Pro requires thinking mode, cannot be disabled
                )
            )
            
            response_text = response.text
            
            # Store in conversation history if tracking
            if conversation_id:
                if conversation_id not in self.conversation_history:
                    self.conversation_history[conversation_id] = []
                self.conversation_history[conversation_id].append({
                    'user': prompt,
                    'assistant': response_text
                })
            
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
                 conversation_id: Optional[str] = None) -> str:
    """
    Query Gemini AI for planning, analysis, or handling large files
    
    Args:
        prompt: Your question or request
        files: Optional list of file paths to analyze
        model: "gemini-2.5-pro" (default) or "gemini-2.5-flash"
        temperature: 0.7 (default) for balanced responses
        use_system_prompt: Include system prompt (default: True, set False to save tokens)
        conversation_id: Optional ID to maintain conversation context
        
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
    return tool.query(prompt, files, model, temperature, use_system_prompt, conversation_id)


# Helper functions for common use cases
def plan_feature(feature_description: str, files: Optional[List[str]] = None) -> str:
    """Get a plan for implementing a feature"""
    prompt = f"""Please provide a clear implementation plan for the following feature:

{feature_description}

Include:
1. Specific files/functions to modify
2. Step-by-step approach
3. Potential challenges to watch for
4. Line numbers or section names where changes are needed

Keep the plan concise and actionable."""
    
    return query_gemini(prompt, files)


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


def suggest_refactoring(file_path: str, focus: Optional[str] = None) -> str:
    """Get refactoring suggestions for a file"""
    prompt = f"""Please analyze this code and suggest refactoring improvements.
{f'Focus on: {focus}' if focus else ''}

Provide:
1. Top 3-5 refactoring opportunities
2. Specific line numbers/functions to change
3. Brief explanation of why each change improves the code
4. Priority order for changes

Keep suggestions practical and focused."""
    
    return query_gemini(prompt, files=[file_path], use_system_prompt=False)


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
        del tool.conversation_history[conversation_id]
        return True
    return False


if __name__ == "__main__":
    # Test the tool
    print("Testing Gemini Tool...")
    result = query_gemini("What is 2+2? Answer in one word.")
    print(f"Response: {result}")