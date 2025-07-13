#!/usr/bin/env python3
"""
Character Backup Restoration Utility

This utility can restore character files from their .bak backups
when critical fields like currency are missing or corrupted.
"""

import json
import os
import shutil
from typing import Dict, Any, Optional
from file_operations import safe_read_json, safe_write_json
from enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("restore_character_backup")

def check_character_integrity(character_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Check if character data has all critical fields
    
    Args:
        character_data: Character data to check
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check currency fields
    if 'currency' not in character_data:
        issues.append("Missing 'currency' object")
    else:
        currency = character_data['currency']
        for field in ['gold', 'silver', 'copper']:
            if field not in currency:
                issues.append(f"Missing currency field: {field}")
    
    # Check other critical fields
    critical_fields = ['name', 'level', 'hitPoints', 'maxHitPoints', 'equipment']
    for field in critical_fields:
        if field not in character_data:
            issues.append(f"Missing critical field: {field}")
    
    return len(issues) == 0, issues

def restore_from_backup(file_path: str, force: bool = False) -> bool:
    """
    Restore character file from backup if integrity check fails
    
    Args:
        file_path: Path to character file
        force: Force restoration even if current file seems valid
        
    Returns:
        True if restoration successful or not needed
    """
    backup_path = f"{file_path}.bak"
    
    # Check if backup exists
    if not os.path.exists(backup_path):
        warning(f"No backup found at {backup_path}")
        return False
    
    # Check current file integrity
    current_data = safe_read_json(file_path)
    if current_data is None:
        error(f"Cannot read current file {file_path}")
        # Try to restore from backup
        info(f"Attempting to restore from backup...")
        try:
            shutil.copy2(backup_path, file_path)
            info(f"Successfully restored {file_path} from backup")
            return True
        except Exception as e:
            error(f"Failed to restore from backup: {e}")
            return False
    
    # Check integrity
    is_valid, issues = check_character_integrity(current_data)
    
    if is_valid and not force:
        info(f"Character file {file_path} is valid, no restoration needed")
        return True
    
    if issues:
        warning(f"Character file has issues: {issues}")
    
    # Load and check backup
    backup_data = safe_read_json(backup_path)
    if backup_data is None:
        error(f"Cannot read backup file {backup_path}")
        return False
    
    backup_valid, backup_issues = check_character_integrity(backup_data)
    
    if not backup_valid:
        warning(f"Backup also has issues: {backup_issues}")
        if not force:
            error("Both files have issues, not restoring unless forced")
            return False
    
    # Create a safety backup of current file
    safety_backup = f"{file_path}.corrupt"
    try:
        shutil.copy2(file_path, safety_backup)
        info(f"Created safety backup at {safety_backup}")
    except:
        pass
    
    # Restore from backup
    try:
        shutil.copy2(backup_path, file_path)
        info(f"Successfully restored {file_path} from backup")
        
        # Verify restoration
        restored_data = safe_read_json(file_path)
        if restored_data:
            restored_valid, _ = check_character_integrity(restored_data)
            if restored_valid:
                info("Restoration verified - character file is now valid")
                return True
            else:
                error("Restoration completed but file still has issues")
                return False
    except Exception as e:
        error(f"Failed to restore from backup: {e}")
        return False

def find_latest_backup(file_path: str) -> Optional[str]:
    """
    Find the most recent backup file
    
    Args:
        file_path: Base file path
        
    Returns:
        Path to most recent backup or None
    """
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    
    # Look for various backup patterns
    backup_patterns = [
        f"{base_name}.bak",
        f"{base_name}.backup_latest",
        f"{base_name}.backup"
    ]
    
    backups = []
    for pattern in backup_patterns:
        backup_path = os.path.join(directory, pattern)
        if os.path.exists(backup_path):
            stat = os.stat(backup_path)
            backups.append((backup_path, stat.st_mtime))
    
    if backups:
        # Sort by modification time, newest first
        backups.sort(key=lambda x: x[1], reverse=True)
        return backups[0][0]
    
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        force = "--force" in sys.argv
        
        info(f"Checking character file: {file_path}")
        
        # Try to find backup
        backup = find_latest_backup(file_path)
        if backup:
            info(f"Found backup: {backup}")
        
        # Attempt restoration
        if restore_from_backup(file_path, force):
            info("Character file restoration complete")
        else:
            error("Character file restoration failed")
    else:
        print("Usage: python restore_character_backup.py <character_file.json> [--force]")
        print("Example: python restore_character_backup.py characters/eirik_hearthwise.json")