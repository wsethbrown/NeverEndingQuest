# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
NeverEndingQuest Core Engine - Web Interface
Copyright (c) 2024 MoonlightByte
Licensed under Fair Source License 1.0

This software is free for non-commercial and educational use.
Commercial competing use is prohibited for 2 years from release.
See LICENSE file for full terms.
"""

# ============================================================================
# WEB_INTERFACE.PY - REAL-TIME WEB FRONTEND
# ============================================================================
#
# ARCHITECTURE ROLE: User Interface Layer - Real-Time Web Frontend
#
# This module provides a modern Flask-based web interface with SocketIO integration
# for real-time bidirectional communication between the browser and game engine,
# enabling responsive tabbed character data display and live game state updates.
#
# KEY RESPONSIBILITIES:
# - Flask + SocketIO real-time web server management
# - Tabbed interface design with dynamic character data presentation
# - Queue-based threaded output processing for responsive user experience
# - Real-time game state synchronization across multiple browser sessions
# - Cross-platform browser-based interface compatibility
# - Status broadcasting integration with console and web interfaces
# - Session state management linking web sessions to game state
#

"""
Web Interface for NeverEndingQuest

This module provides a Flask-based web interface for the dungeon master game,
with separate panels for game output and debug information.
"""
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import os
import sys
import json
import threading
import queue
import time
import webbrowser
from datetime import datetime
import io
from contextlib import redirect_stdout, redirect_stderr

# Add parent directory to path so we can import from utils, core, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Install debug interceptor before importing main
from utils.redirect_debug_output import install_debug_interceptor, uninstall_debug_interceptor
install_debug_interceptor()

# Import the main game module and reset logic
import main as dm_main
import utils.reset_campaign as reset_campaign
from core.managers.status_manager import set_status_callback
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("web_interface")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dungeon-master-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for managing output
game_output_queue = queue.Queue()
debug_output_queue = queue.Queue()
user_input_queue = queue.Queue()
game_thread = None
original_stdout = sys.stdout
original_stderr = sys.stderr
original_stdin = sys.stdin

# Status callback function
def emit_status_update(status_message, is_processing):
    """Emit status updates to the frontend"""
    socketio.emit('status_update', {
        'message': status_message,
        'is_processing': is_processing
    })

# Set the status callback
set_status_callback(emit_status_update)

class WebOutputCapture:
    """Captures output and routes it to appropriate queues"""
    def __init__(self, queue, original_stream, is_error=False):
        self.queue = queue
        self.original_stream = original_stream
        self.is_error = is_error
        self.buffer = ""
        self.in_dm_section = False
        self.dm_buffer = []
    
    def write(self, text):
        # Write to original stream for console visibility (with error handling)
        try:
            # Ensure text is a string and handle encoding issues
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            elif not isinstance(text, str):
                text = str(text)
            
            self.original_stream.write(text)
            self.original_stream.flush()
        except (BrokenPipeError, OSError, UnicodeEncodeError, AttributeError):
            # Ignore broken pipe errors, encoding errors, and attribute errors during output capture
            pass
        except Exception:
            # Catch any other unexpected errors and continue
            pass
        
        # Buffer text until we have a complete line
        self.buffer += text
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            # Process all complete lines
            for line in lines[:-1]:
                # Clean the line of ANSI codes for checking content
                clean_line = self.strip_ansi_codes(line)
                
                # Check if this is a player status/prompt line
                if clean_line.startswith('[') and ('HP:' in clean_line or 'XP:' in clean_line):
                    # This is a player prompt - send to debug
                    debug_output_queue.put({
                        'type': 'debug',
                        'content': clean_line,
                        'timestamp': datetime.now().isoformat()
                    })
                # Check if this starts a Dungeon Master section
                elif "Dungeon Master:" in clean_line:
                    try:
                        # Start capturing DM content
                        self.in_dm_section = True
                        self.dm_buffer = [clean_line]
                    except Exception:
                        # If DM section initialization fails, send to debug instead
                        debug_output_queue.put({
                            'type': 'debug',
                            'content': clean_line,
                            'timestamp': datetime.now().isoformat()
                        })
                elif self.in_dm_section:
                    # Check if we're still in DM section
                    if line.strip() == "":
                        try:
                            # Empty line - still part of DM section, add to buffer
                            self.dm_buffer.append("")
                        except Exception:
                            # If buffer append fails, reset DM section
                            self.in_dm_section = False
                            self.dm_buffer = []
                    elif any(marker in clean_line for marker in ['DEBUG:', 'ERROR:', 'WARNING:']) or \
                         clean_line.startswith('[') and ('HP:' in clean_line or 'XP:' in clean_line) or \
                         clean_line.startswith('>'):
                        # This ends the DM section - send accumulated DM content as single message
                        if self.dm_buffer:
                            try:
                                combined_content = '\n'.join(self.dm_buffer)
                                # Remove "Dungeon Master:" prefix from the beginning if present
                                combined_content = combined_content.replace('Dungeon Master:', '', 1).strip()
                                if combined_content.strip():  # Only send if there's actual content
                                    game_output_queue.put({
                                        'type': 'narration',
                                        'content': combined_content
                                    })
                            except Exception:
                                # If DM content processing fails, send raw content to debug
                                try:
                                    debug_output_queue.put({
                                        'type': 'debug',
                                        'content': f"DM content error: {str(self.dm_buffer)}",
                                        'timestamp': datetime.now().isoformat()
                                    })
                                except Exception:
                                    # If even debug fails, just continue
                                    pass
                        self.in_dm_section = False
                        self.dm_buffer = []
                        # Send this line to debug
                        try:
                            debug_output_queue.put({
                                'type': 'debug',
                                'content': clean_line,
                                'timestamp': datetime.now().isoformat(),
                                'is_error': self.is_error or 'ERROR:' in clean_line
                            })
                        except Exception:
                            # If debug queue fails, just continue
                            pass
                    else:
                        # Still in DM section - check if it's a debug message
                        if any(marker in clean_line for marker in [
                            'Lightweight chat history updated',
                            'System messages removed:',
                            'User messages:',
                            'Assistant messages:',
                            'not found. Skipping',
                            'not found. Returning None',
                            'has an invalid JSON format',
                            'Current Time:',
                            'Time Advanced:',
                            'New Time:',
                            'Days Passed:',
                            'Loading module areas',
                            'Graph built:',
                            '[OK] Loaded'
                        ]):
                            # This is a debug message - send to debug output instead
                            debug_output_queue.put({
                                'type': 'debug',
                                'content': clean_line,
                                'timestamp': datetime.now().isoformat()
                            })
                            # End the DM section and send what we have so far
                            if self.dm_buffer:
                                try:
                                    combined_content = '\n'.join(self.dm_buffer)
                                    combined_content = combined_content.replace('Dungeon Master:', '', 1).strip()
                                    if combined_content.strip():
                                        game_output_queue.put({
                                            'type': 'narration',
                                            'content': combined_content
                                        })
                                except Exception:
                                    # If DM content processing fails, just continue
                                    pass
                            self.in_dm_section = False
                            self.dm_buffer = []
                        else:
                            try:
                                # Not a debug message - add to buffer
                                self.dm_buffer.append(clean_line)
                            except Exception:
                                # If buffer append fails, reset DM section
                                self.in_dm_section = False
                                self.dm_buffer = []
                else:
                    # Not in DM section - check if it's a debug message that should be filtered
                    if any(marker in clean_line for marker in [
                        'Lightweight chat history updated',
                        'System messages removed:',
                        'User messages:',
                        'Assistant messages:',
                        'not found. Skipping',
                        'not found. Returning None',
                        'has an invalid JSON format',
                        'Current Time:',
                        'Time Advanced:',
                        'New Time:',
                        'Days Passed:',
                        'Loading module areas',
                        'Graph built:',
                        '[OK] Loaded'
                    ]):
                        # These are debug messages - send to debug output
                        debug_output_queue.put({
                            'type': 'debug',
                            'content': clean_line,
                            'timestamp': datetime.now().isoformat()
                        })
                    elif line.strip():  # Only send non-empty lines
                        debug_output_queue.put({
                            'type': 'debug',
                            'content': clean_line,
                            'timestamp': datetime.now().isoformat(),
                            'is_error': self.is_error or 'ERROR:' in clean_line
                        })
            # Keep the incomplete line in buffer
            self.buffer = lines[-1]
    
    def strip_ansi_codes(self, text):
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def flush(self):
        # If we're in a DM section, flush it as single message
        if self.in_dm_section and self.dm_buffer:
            combined_content = '\n'.join(self.dm_buffer)
            # Remove "Dungeon Master:" prefix from the beginning if present
            combined_content = combined_content.replace('Dungeon Master:', '', 1).strip()
            if combined_content.strip():  # Only send if there's actual content
                game_output_queue.put({
                    'type': 'narration',
                    'content': combined_content
                })
            self.in_dm_section = False
            self.dm_buffer = []
        
        if self.buffer:
            # Don't recursively call write() - just add newline to buffer
            self.buffer += '\n'
        try:
            self.original_stream.flush()
        except (BrokenPipeError, OSError, UnicodeEncodeError, AttributeError):
            # Ignore broken pipe errors, encoding errors, and attribute errors during flush
            pass
        except Exception:
            # Catch any other unexpected errors and continue
            pass

class WebInput:
    """Handles input from the web interface"""
    def __init__(self, queue):
        self.queue = queue
    
    def readline(self):
        # Signal that we're ready for input (with error handling)
        try:
            from core.managers.status_manager import status_ready
            status_ready()
        except Exception:
            # If status_ready fails, continue without it
            pass
        
        # Wait for input from the web interface
        retry_count = 0
        max_retries = 1000  # Prevent infinite loops
        
        while retry_count < max_retries:
            try:
                user_input = self.queue.get(timeout=0.1)
                # Ensure input is a string and handle encoding issues
                if isinstance(user_input, str):
                    return user_input + '\n'
                else:
                    # Convert to string if needed
                    return str(user_input) + '\n'
            except queue.Empty:
                retry_count += 1
                continue
            except (BrokenPipeError, OSError, IOError):
                # Handle pipe errors gracefully
                return '\n'  # Return empty input to keep game running
            except Exception:
                # Handle any other unexpected errors
                return '\n'
        
        # If we've retried too many times, return empty input
        return '\n'

@app.route('/')
def index():
    """Serve the main game interface"""
    return render_template('game_interface.html')

@app.route('/static/dm_logo.png')
def serve_dm_logo():
    """Serve the DM logo image"""
    import mimetypes
    from flask import send_file
    # Go up one directory to find dm_logo.png at the root
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dm_logo.png')
    return send_file(logo_path, mimetype='image/png')

@app.route('/static/icons/<path:filename>')
def serve_icon(filename):
    """Serve icon images from the icons directory"""
    import mimetypes
    from flask import send_file
    # Ensure the filename ends with .png for security
    if not filename.endswith('.png'):
        return "Not found", 404
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icons', filename)
    if os.path.exists(icon_path):
        return send_file(icon_path, mimetype='image/png')
    return "Not found", 404

@app.route('/spell-data')
def get_spell_data():
    """Serve spell repository data for tooltips"""
    try:
        with open('data/spell_repository.json', 'r') as f:
            spell_data = json.load(f)
        return jsonify(spell_data)
    except FileNotFoundError:
        return jsonify({})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to NeverEndingQuest'})
    
    # Send any queued messages
    while not game_output_queue.empty():
        msg = game_output_queue.get()
        emit('game_output', msg)
    
    while not debug_output_queue.empty():
        msg = debug_output_queue.get()
        emit('debug_output', msg)

@socketio.on('user_input')
def handle_user_input(data):
    """Handle input from the user"""
    user_input = data.get('input', '')
    user_input_queue.put(user_input)
    
    # Echo the input back to the game output
    emit('game_output', {
        'type': 'user-input',
        'content': user_input
    })

@socketio.on('action')
def handle_action(data):
    """Handle direct action requests from the UI (save, load, reset)."""
    action_type = data.get('action')
    parameters = data.get('parameters', {})
    debug(f"WEB_REQUEST: Received direct action from client: {action_type}", category="web_interface")

    if action_type == 'listSaves':
        try:
            from updates.save_game_manager import SaveGameManager
            manager = SaveGameManager()
            saves = manager.list_save_games()
            emit('save_list_response', saves)
        except Exception as e:
            print(f"Error listing saves: {e}")
            emit('save_list_response', [])

    elif action_type == 'saveGame':
        try:
            from updates.save_game_manager import SaveGameManager
            manager = SaveGameManager()
            description = parameters.get("description", "")
            save_mode = parameters.get("saveMode", "essential")
            success, message = manager.create_save_game(description, save_mode)
            if success:
                emit('system_message', {'content': f"Game saved: {message}"})
            else:
                emit('error', {'message': f"Save failed: {message}"})
        except Exception as e:
            emit('error', {'message': f"Save failed: {str(e)}"})

    elif action_type == 'restoreGame':
        try:
            from updates.save_game_manager import SaveGameManager
            manager = SaveGameManager()
            save_folder = parameters.get("saveFolder")
            success, message = manager.restore_save_game(save_folder)
            if success:
                emit('restore_complete', {'message': 'Game restored successfully. Server restarting...'})
                socketio.sleep(1)
                print("INFO: Game restore successful. Server is shutting down for restart.")
                os._exit(0)
            else:
                emit('error', {'message': f"Restore failed: {message}"})
        except Exception as e:
            emit('error', {'message': f"Restore failed: {str(e)}"})
    
    elif action_type == 'deleteSave':
        try:
            from updates.save_game_manager import SaveGameManager
            manager = SaveGameManager()
            save_folder = parameters.get("saveFolder")
            success, message = manager.delete_save_game(save_folder)
            if success:
                emit('system_message', {'content': f"Save deleted: {message}"})
            else:
                emit('error', {'message': f"Delete failed: {message}"})
        except Exception as e:
            emit('error', {'message': f"Delete failed: {str(e)}"})

    elif action_type == 'nuclearReset':
        try:
            reset_campaign.perform_reset_logic()
            emit('reset_complete', {'message': 'Campaign has been reset. Reloading...'})
            socketio.sleep(1) 
            print("INFO: Campaign reset complete. Server is shutting down for restart.")
            os._exit(0)
        except Exception as e:
            emit('error', {'message': f'Campaign reset failed: {str(e)}'})

@socketio.on('start_game')
def handle_start_game():
    """Start the game in a separate thread"""
    global game_thread
    
    if game_thread and game_thread.is_alive():
        emit('error', {'message': 'Game is already running'})
        return
    
    # Uninstall debug interceptor to prevent competing stdout redirections
    uninstall_debug_interceptor()
    
    # Set up output capture - both go to debug by default, filtering happens in write()
    sys.stdout = WebOutputCapture(debug_output_queue, original_stdout)
    sys.stderr = WebOutputCapture(debug_output_queue, original_stderr, is_error=True)
    sys.stdin = WebInput(user_input_queue)
    
    # Start the game in a separate thread
    game_thread = threading.Thread(target=run_game_loop, daemon=True)
    game_thread.start()
    
    emit('game_started', {'message': 'Game started successfully'})

@socketio.on('request_player_data')
def handle_player_data_request(data):
    """Handle requests for player data (inventory, stats, NPCs)"""
    try:
        dataType = data.get('dataType', 'stats')
        response_data = None
        
        # Load party tracker to get player name and NPCs
        party_tracker_path = 'party_tracker.json'
        if os.path.exists(party_tracker_path):
            with open(party_tracker_path, 'r', encoding='utf-8') as f:
                party_tracker = json.load(f)
        else:
            emit('player_data_response', {'dataType': dataType, 'data': None, 'error': 'Party tracker not found'})
            return
        
        if dataType == 'stats' or dataType == 'inventory' or dataType == 'spells':
            # Get player name from party tracker
            if party_tracker.get('partyMembers') and len(party_tracker['partyMembers']) > 0:
                from updates.update_character_info import normalize_character_name
                player_name = normalize_character_name(party_tracker['partyMembers'][0])
                
                # Try module-specific path first
                from utils.module_path_manager import ModulePathManager
                current_module = party_tracker.get("module", "").replace(" ", "_")
                path_manager = ModulePathManager(current_module)
                
                try:
                    player_file = path_manager.get_character_path(player_name)
                    if os.path.exists(player_file):
                        with open(player_file, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
                except:
                    # Fallback to characters directory
                    player_file = path_manager.get_character_path(player_name)
                    if os.path.exists(player_file):
                        with open(player_file, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
        
        elif dataType == 'npcs':
            # Get NPC data from party tracker
            npcs = []
            from utils.module_path_manager import ModulePathManager
            current_module = party_tracker.get("module", "").replace(" ", "_")
            path_manager = ModulePathManager(current_module)
            
            for npc_info in party_tracker.get('partyNPCs', []):
                npc_name = npc_info['name']
                
                try:
                    # Use fuzzy matching to find the correct NPC file
                    from updates.update_character_info import find_character_file_fuzzy
                    matched_name = find_character_file_fuzzy(npc_name)
                    
                    if matched_name:
                        npc_file = path_manager.get_character_path(matched_name)
                        if os.path.exists(npc_file):
                            with open(npc_file, 'r', encoding='utf-8') as f:
                                npc_data = json.load(f)
                                npcs.append(npc_data)
                except:
                    pass
            
            response_data = npcs
        
        emit('player_data_response', {'dataType': dataType, 'data': response_data})
    
    except Exception as e:
        emit('player_data_response', {'dataType': dataType, 'data': None, 'error': str(e)})

@socketio.on('request_location_data')
def handle_location_data_request():
    """Handle requests for current location information"""
    try:
        # Load party tracker to get current location
        party_tracker_path = 'party_tracker.json'
        if os.path.exists(party_tracker_path):
            with open(party_tracker_path, 'r', encoding='utf-8') as f:
                party_tracker = json.load(f)
            
            world_conditions = party_tracker.get('worldConditions', {})
            location_info = {
                'currentLocation': world_conditions.get('currentLocation', 'Unknown'),
                'currentArea': world_conditions.get('currentArea', 'Unknown'),
                'currentLocationId': world_conditions.get('currentLocationId', ''),
                'currentAreaId': world_conditions.get('currentAreaId', ''),
                'time': world_conditions.get('time', ''),
                'day': world_conditions.get('day', ''),
                'month': world_conditions.get('month', ''),
                'year': world_conditions.get('year', '')
            }
            
            emit('location_data_response', {'data': location_info})
        else:
            emit('location_data_response', {'data': None, 'error': 'Party tracker not found'})
    
    except Exception as e:
        emit('location_data_response', {'data': None, 'error': str(e)})

@socketio.on('request_npc_saves')
def handle_npc_saves_request(data):
    """Handle requests for NPC saving throws"""
    try:
        npc_name = data.get('npcName', '')
        
        # Load the NPC file
        from utils.module_path_manager import ModulePathManager
        from utils.encoding_utils import safe_json_load
        # Get current module from party tracker for consistent path resolution
        try:
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()  # Fallback to reading from file
        
        from updates.update_character_info import normalize_character_name, find_character_file_fuzzy
        
        # Use fuzzy matching to find the correct NPC file
        matched_name = find_character_file_fuzzy(npc_name)
        if matched_name:
            npc_file = path_manager.get_character_path(matched_name)
        else:
            # Fallback to normalized name if no match found
            npc_file = path_manager.get_character_path(normalize_character_name(npc_name))
        if os.path.exists(npc_file):
            with open(npc_file, 'r', encoding='utf-8') as f:
                npc_data = json.load(f)
            
            emit('npc_details_response', {'npcName': npc_name, 'data': npc_data, 'modalType': 'saves'})
        else:
            emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': 'NPC file not found'})
            
    except Exception as e:
        emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': str(e)})

@socketio.on('request_npc_skills')
def handle_npc_skills_request(data):
    """Handle requests for NPC skills"""
    try:
        npc_name = data.get('npcName', '')
        
        # Load the NPC file
        from utils.module_path_manager import ModulePathManager
        from utils.encoding_utils import safe_json_load
        # Get current module from party tracker for consistent path resolution
        try:
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()  # Fallback to reading from file
        
        from updates.update_character_info import normalize_character_name, find_character_file_fuzzy
        
        # Use fuzzy matching to find the correct NPC file
        matched_name = find_character_file_fuzzy(npc_name)
        if matched_name:
            npc_file = path_manager.get_character_path(matched_name)
        else:
            # Fallback to normalized name if no match found
            npc_file = path_manager.get_character_path(normalize_character_name(npc_name))
        if os.path.exists(npc_file):
            with open(npc_file, 'r', encoding='utf-8') as f:
                npc_data = json.load(f)
            
            emit('npc_details_response', {'npcName': npc_name, 'data': npc_data, 'modalType': 'skills'})
        else:
            emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': 'NPC file not found'})
            
    except Exception as e:
        emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': str(e)})

@socketio.on('request_npc_spells')
def handle_npc_spells_request(data):
    """Handle requests for NPC spellcasting"""
    try:
        npc_name = data.get('npcName', '')
        
        # Load the NPC file
        from utils.module_path_manager import ModulePathManager
        from utils.encoding_utils import safe_json_load
        # Get current module from party tracker for consistent path resolution
        try:
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()  # Fallback to reading from file
        
        from updates.update_character_info import normalize_character_name, find_character_file_fuzzy
        
        # Use fuzzy matching to find the correct NPC file
        matched_name = find_character_file_fuzzy(npc_name)
        if matched_name:
            npc_file = path_manager.get_character_path(matched_name)
        else:
            # Fallback to normalized name if no match found
            npc_file = path_manager.get_character_path(normalize_character_name(npc_name))
        if os.path.exists(npc_file):
            with open(npc_file, 'r', encoding='utf-8') as f:
                npc_data = json.load(f)
            
            emit('npc_details_response', {'npcName': npc_name, 'data': npc_data, 'modalType': 'spells'})
        else:
            emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': 'NPC file not found'})
            
    except Exception as e:
        emit('npc_details_response', {'npcName': npc_name, 'data': None, 'error': str(e)})

@socketio.on('request_npc_inventory')
def handle_npc_inventory_request(data):
    """Handle requests for NPC inventory"""
    try:
        npc_name = data.get('npcName', '')
        
        # Load the NPC file
        from utils.module_path_manager import ModulePathManager
        from utils.encoding_utils import safe_json_load
        # Get current module from party tracker for consistent path resolution
        try:
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()  # Fallback to reading from file
        
        from updates.update_character_info import normalize_character_name, find_character_file_fuzzy
        
        # Use fuzzy matching to find the correct NPC file
        matched_name = find_character_file_fuzzy(npc_name)
        if matched_name:
            npc_file = path_manager.get_character_path(matched_name)
        else:
            # Fallback to normalized name if no match found
            npc_file = path_manager.get_character_path(normalize_character_name(npc_name))
        if os.path.exists(npc_file):
            with open(npc_file, 'r', encoding='utf-8') as f:
                npc_data = json.load(f)
            
            # Extract equipment for inventory display
            equipment = npc_data.get('equipment', [])
            emit('npc_inventory_response', {'npcName': npc_name, 'data': equipment})
        else:
            emit('npc_inventory_response', {'npcName': npc_name, 'data': None, 'error': 'NPC file not found'})
            
    except Exception as e:
        emit('npc_inventory_response', {'npcName': npc_name, 'data': None, 'error': str(e)})

# CORRECTLY PLACED STORAGE HANDLER
@socketio.on('request_storage_data')
def handle_request_storage_data():
    """Handles a request from the client to view all player storage."""
    debug("WEB_REQUEST: Received request for storage data from client", category="web_interface")
    try:
        from core.managers.storage_manager import get_storage_manager
        manager = get_storage_manager()
        # Calling view_storage() with no location_id gets ALL storage containers.
        storage_data = manager.view_storage()
        
        if storage_data.get("success"):
            emit('storage_data_response', {'data': storage_data})
        else:
            emit('error', {'message': 'Failed to retrieve storage data.'})
            
    except Exception as e:
        print(f"ERROR handling storage request: {e}")
        emit('error', {'message': 'An internal error occurred while fetching storage data.'})

def run_game_loop():
    """Run the main game loop with enhanced error handling"""
    try:
        # Start the output sender thread
        output_thread = threading.Thread(target=send_output_to_clients, daemon=True)
        output_thread.start()
        
        # Run the main game
        dm_main.main_game_loop()
    except (BrokenPipeError, OSError) as e:
        # Handle broken pipe errors specifically
        try:
            print(f"Stream error detected: {e}")
        except Exception:
            pass  # If even this fails, continue silently
        
        try:
            # Attempt to reset streams
            sys.stdout = WebOutputCapture(debug_output_queue, original_stdout)
            sys.stderr = WebOutputCapture(debug_output_queue, original_stderr, is_error=True)
            sys.stdin = WebInput(user_input_queue)
            try:
                print("Stream recovery attempted")
            except Exception:
                pass
        except Exception:
            try:
                print("Stream recovery failed")
            except Exception:
                pass
        
        # Send a user-friendly message
        try:
            game_output_queue.put({
                'type': 'info',
                'content': 'Connection restored. You may continue playing.',
                'timestamp': datetime.now().isoformat()
            })
        except Exception:
            pass
    except Exception as e:
        # Handle other errors
        error_msg = f"Game error: {str(e)}"
        try:
            print(f"Game loop error: {error_msg}")
        except Exception:
            pass
        
        try:
            game_output_queue.put({
                'type': 'error',
                'content': error_msg,
                'timestamp': datetime.now().isoformat()
            })
        except Exception:
            pass
    finally:
        # Restore original streams safely
        try:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            sys.stdin = original_stdin
        except Exception:
            # If restoration fails, try to at least restore stdout
            try:
                sys.stdout = original_stdout
            except Exception:
                pass

def send_output_to_clients():
    """Send queued output to all connected clients"""
    while True:
        try:
            # Send game output
            while not game_output_queue.empty():
                try:
                    msg = game_output_queue.get()
                    socketio.emit('game_output', msg)
                except Exception:
                    # If queue operation or emit fails, just continue
                    break
            
            # Send debug output
            while not debug_output_queue.empty():
                try:
                    msg = debug_output_queue.get()
                    socketio.emit('debug_output', msg)
                except Exception:
                    # If queue operation or emit fails, just continue
                    break
        except Exception:
            # If any other error occurs, just continue
            pass
        
        time.sleep(0.1)  # Small delay to prevent CPU spinning

def open_browser():
    """Open the web browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Start browser opening in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("Starting NeverEndingQuest Web Interface...")
    print("Opening browser at http://localhost:5000")
    
    # Run the Flask app with SocketIO
    socketio.run(app, 
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True)