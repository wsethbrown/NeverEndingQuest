#!/usr/bin/env python3
"""
Log viewer utility for NeverEndingQuest
Allows viewing and filtering of game logs
"""

import os
import sys
from datetime import datetime, timedelta

def view_recent_errors(minutes=10):
    """View errors from the last N minutes"""
    try:
        with open('modules/logs/game_errors.log', 'r') as f:
            lines = f.readlines()
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_errors = []
        
        for line in lines:
            try:
                # Parse timestamp from log line
                timestamp_str = line.split(' - ')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                if timestamp >= cutoff_time:
                    recent_errors.append(line.strip())
            except:
                continue
        
        if recent_errors:
            print(f"\n=== Errors from the last {minutes} minutes ===")
            for error in recent_errors:
                print(error)
        else:
            print(f"No errors in the last {minutes} minutes")
            
    except FileNotFoundError:
        print("No error log file found")

def view_recent_debug(minutes=10, filter_term=None):
    """View debug messages from the last N minutes"""
    try:
        with open('modules/logs/game_debug.log', 'r') as f:
            lines = f.readlines()
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_debug = []
        
        for line in lines:
            try:
                # Parse timestamp from log line
                timestamp_str = line.split(' - ')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                if timestamp >= cutoff_time:
                    if filter_term is None or filter_term.lower() in line.lower():
                        recent_debug.append(line.strip())
            except:
                continue
        
        if recent_debug:
            print(f"\n=== Debug messages from the last {minutes} minutes ===")
            if filter_term:
                print(f"(Filtered by: '{filter_term}')")
            for msg in recent_debug[-50:]:  # Show last 50 messages
                print(msg)
        else:
            print(f"No debug messages in the last {minutes} minutes")
            
    except FileNotFoundError:
        print("No debug log file found")

def tail_logs(log_type='error', lines=20):
    """Show the last N lines of a log file"""
    filename = 'modules/logs/game_errors.log' if log_type == 'error' else 'modules/logs/game_debug.log'
    
    try:
        with open(filename, 'r') as f:
            all_lines = f.readlines()
        
        print(f"\n=== Last {lines} lines from {filename} ===")
        for line in all_lines[-lines:]:
            print(line.strip())
            
    except FileNotFoundError:
        print(f"No {log_type} log file found")

def search_logs(search_term, log_type='both'):
    """Search logs for a specific term"""
    files = []
    if log_type in ['error', 'both']:
        files.append('modules/logs/game_errors.log')
    if log_type in ['debug', 'both']:
        files.append('modules/logs/game_debug.log')
    
    for filename in files:
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            matches = [line.strip() for line in lines if search_term.lower() in line.lower()]
            
            if matches:
                print(f"\n=== Found {len(matches)} matches in {filename} ===")
                for match in matches[-10:]:  # Show last 10 matches
                    print(match)
                    
        except FileNotFoundError:
            print(f"No {filename} found")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python view_logs.py errors [minutes]     - View recent errors")
        print("  python view_logs.py debug [minutes]      - View recent debug messages")
        print("  python view_logs.py tail [error|debug]   - Show last 20 lines")
        print("  python view_logs.py search <term>        - Search for a term")
        print("  python view_logs.py help                 - Show this help")
    else:
        command = sys.argv[1]
        
        if command == "errors":
            minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            view_recent_errors(minutes)
        elif command == "debug":
            minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            filter_term = sys.argv[3] if len(sys.argv) > 3 else None
            view_recent_debug(minutes, filter_term)
        elif command == "tail":
            log_type = sys.argv[2] if len(sys.argv) > 2 else 'error'
            tail_logs(log_type)
        elif command == "search":
            if len(sys.argv) > 2:
                search_logs(sys.argv[2])
            else:
                print("Please provide a search term")
        else:
            print("Unknown command. Use 'python view_logs.py help' for usage.")