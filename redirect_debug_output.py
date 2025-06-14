"""
Redirect debug output from various modules to use the enhanced logger
This intercepts print statements and logging calls to provide cleaner output
"""

import sys
import re
from enhanced_logger import game_logger, game_event

class DebugOutputInterceptor:
    """Intercepts stdout to redirect debug messages to our logger"""
    
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.buffer = ""
        
    def write(self, text):
        """Intercept and process output"""
        # Handle both str and bytes
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
            
        if not text or text == '\n':
            return
            
        # Buffer lines until we have a complete line
        self.buffer += text
        if '\n' not in self.buffer:
            return
            
        lines = self.buffer.split('\n')
        self.buffer = lines[-1]  # Keep incomplete line in buffer
        
        for line in lines[:-1]:
            self._process_line(line)
    
    def _process_line(self, line):
        """Process a single line of output"""
        if not line.strip():
            return
            
        # Check for debug patterns
        if line.startswith("DEBUG:"):
            self._handle_debug_line(line)
        elif line.startswith("ERROR:"):
            game_logger.error(line[6:].strip())
        elif line.startswith("WARNING:"):
            game_logger.warning(line[8:].strip())
        elif line.startswith("INFO:"):
            game_logger.info(line[5:].strip())
        elif "HTTP Request:" in line or "httpx" in line:
            # Skip HTTP debug messages
            return
        else:
            # Pass through other output
            self.original_stdout.write(line + '\n')
            self.original_stdout.flush()
    
    def _handle_debug_line(self, line):
        """Handle DEBUG lines with intelligent categorization"""
        content = line[6:].strip()  # Remove "DEBUG:" prefix
        
        # Module loading
        if "ModulePathManager loaded module" in content:
            game_logger.debug(content, category="module_loading")
            
        # File operations
        elif "Successfully updated" in content or "File opened successfully" in content:
            game_logger.debug(content, category="file_success")
        elif "Error" in content or "Failed" in content:
            game_logger.error(content)
            
        # Location transitions
        elif "Transitioning from" in content:
            match = re.search(r"Transitioning from '(.+?)' to '(.+?)'", content)
            if match:
                game_event("location_transition", {
                    "from": match.group(1),
                    "to": match.group(2)
                })
            else:
                game_logger.debug(content, category="location_transitions")
                
        # Plot updates
        elif "Plot information updated" in content or "plotPointId" in content:
            game_logger.debug(content, category="plot_updates")
            
        # Summary operations
        elif "Building cumulative summary" in content or "Generating summary" in content:
            game_logger.debug(content, category="summary_building")
        elif "Summary generated" in content or "Built cumulative summary" in content:
            game_logger.debug(content, category="summary_details")
            
        # Character/inventory updates
        elif "character information updated" in content:
            match = re.search(r"(\w+)'s character information updated", content)
            if match:
                game_event("character_update", {
                    "character": match.group(1),
                    "change": "Information updated"
                })
            else:
                game_logger.debug(content, category="character_updates")
                
        # Validation
        elif "Validation passed" in content or "Valid response" in content:
            game_logger.debug(content, category="validation")
            
        # Default
        else:
            game_logger.debug(content)
    
    def flush(self):
        """Flush any buffered content"""
        if self.buffer:
            self._process_line(self.buffer)
            self.buffer = ""
        self.original_stdout.flush()

def install_debug_interceptor():
    """Install the debug output interceptor"""
    sys.stdout = DebugOutputInterceptor(sys.stdout)
    
def uninstall_debug_interceptor():
    """Restore original stdout"""
    if isinstance(sys.stdout, DebugOutputInterceptor):
        sys.stdout = sys.stdout.original_stdout