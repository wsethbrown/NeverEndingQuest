#!/usr/bin/env python3
# ============================================================================
# RUN_WEB.PY - WEB INTERFACE LAUNCHER
# ============================================================================
#
# ARCHITECTURE ROLE: User Interface Layer - Web Application Launcher
#
# This launcher script provides the entry point for the web-based user interface,
# coordinating Flask server startup and browser integration for cross-platform
# web-based game access.
#
# KEY RESPONSIBILITIES:
# - Web interface process management and startup coordination
# - Automatic browser launching for seamless user experience
# - Cross-platform compatibility for web server deployment
# - Integration with Flask + SocketIO web interface architecture
# - Error handling and graceful startup failure management
#

"""
Launcher script for the DungeonMasterAI web interface.
This script starts the Flask server and automatically opens the browser.
"""
import subprocess
import sys
import os
import time

def main():
    print("Launching DungeonMasterAI Web Interface...")
    print("The browser should open automatically. If not, navigate to http://localhost:5000")
    
    # Run the web interface with restart capability
    while True:
        try:
            # Run the web interface and capture the return code
            result = subprocess.run([sys.executable, "web_interface.py"])
            
            # Check if it was a planned restart (exit code 0)
            if result.returncode == 0:
                print("\n[RESTART] Server shutdown detected. Restarting in 2 seconds...")
                time.sleep(2)
                print("[RESTART] Starting server again...")
                continue
            else:
                # Non-zero exit code means an error occurred
                print(f"\n[ERROR] Server exited with code {result.returncode}")
                break
                
        except KeyboardInterrupt:
            print("\nShutting down DungeonMasterAI Web Interface...")
            break
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()