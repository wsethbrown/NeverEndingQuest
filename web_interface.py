"""
Web Interface for DungeonMasterAI

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

# Import the main game module
import main as dm_main

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

class WebOutputCapture:
    """Captures output and routes it to appropriate queues"""
    def __init__(self, queue, original_stream, is_error=False):
        self.queue = queue
        self.original_stream = original_stream
        self.is_error = is_error
        self.buffer = ""
    
    def write(self, text):
        # Write to original stream for console visibility
        self.original_stream.write(text)
        
        # Buffer text until we have a complete line
        self.buffer += text
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            # Process all complete lines
            for line in lines[:-1]:
                if line.strip():
                    # Route to appropriate queue based on content
                    if any(keyword in line for keyword in ['DEBUG:', 'ERROR:', 'WARNING:']):
                        self.queue.put({
                            'type': 'debug',
                            'content': line,
                            'timestamp': datetime.now().isoformat(),
                            'is_error': self.is_error or 'ERROR:' in line
                        })
                    else:
                        # Check for colored output (DM narration)
                        if '\033[' in line:  # ANSI escape code
                            # Strip ANSI codes for web display
                            clean_line = self.strip_ansi_codes(line)
                            game_output_queue.put({
                                'type': 'narration',
                                'content': clean_line,
                                'timestamp': datetime.now().isoformat()
                            })
                        else:
                            game_output_queue.put({
                                'type': 'game',
                                'content': line,
                                'timestamp': datetime.now().isoformat()
                            })
            # Keep the incomplete line in buffer
            self.buffer = lines[-1]
    
    def strip_ansi_codes(self, text):
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def flush(self):
        if self.buffer:
            self.write('\n')
        self.original_stream.flush()

class WebInput:
    """Handles input from the web interface"""
    def __init__(self, queue):
        self.queue = queue
    
    def readline(self):
        # Wait for input from the web interface
        while True:
            try:
                user_input = self.queue.get(timeout=0.1)
                return user_input + '\n'
            except queue.Empty:
                continue

@app.route('/')
def index():
    """Serve the main game interface"""
    return render_template('game_interface.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to DungeonMasterAI'})
    
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
        'type': 'user_input',
        'content': f"> {user_input}",
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('start_game')
def handle_start_game():
    """Start the game in a separate thread"""
    global game_thread
    
    if game_thread and game_thread.is_alive():
        emit('error', {'message': 'Game is already running'})
        return
    
    # Set up output capture
    sys.stdout = WebOutputCapture(game_output_queue, original_stdout)
    sys.stderr = WebOutputCapture(debug_output_queue, original_stderr, is_error=True)
    sys.stdin = WebInput(user_input_queue)
    
    # Start the game in a separate thread
    game_thread = threading.Thread(target=run_game_loop, daemon=True)
    game_thread.start()
    
    emit('game_started', {'message': 'Game started successfully'})

def run_game_loop():
    """Run the main game loop"""
    try:
        # Start the output sender thread
        output_thread = threading.Thread(target=send_output_to_clients, daemon=True)
        output_thread.start()
        
        # Run the main game
        dm_main.main()
    except Exception as e:
        error_msg = f"Game error: {str(e)}"
        game_output_queue.put({
            'type': 'error',
            'content': error_msg,
            'timestamp': datetime.now().isoformat()
        })
    finally:
        # Restore original streams
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        sys.stdin = original_stdin

def send_output_to_clients():
    """Send queued output to all connected clients"""
    while True:
        # Send game output
        while not game_output_queue.empty():
            msg = game_output_queue.get()
            socketio.emit('game_output', msg)
        
        # Send debug output
        while not debug_output_queue.empty():
            msg = debug_output_queue.get()
            socketio.emit('debug_output', msg)
        
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
    
    print("Starting DungeonMasterAI Web Interface...")
    print("Opening browser at http://localhost:5000")
    
    # Run the Flask app with SocketIO
    socketio.run(app, 
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False)