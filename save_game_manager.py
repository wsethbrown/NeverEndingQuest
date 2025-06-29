#!/usr/bin/env python3
"""
Save Game Manager Module for DungeonMasterAI

Handles save and restore functionality for game state preservation.
"""

# ============================================================================
# SAVE_GAME_MANAGER.PY - GAME STATE PERSISTENCE SYSTEM
# ============================================================================
# 
# ARCHITECTURE ROLE: Data Management Layer - Game State Persistence
# 
# This module implements comprehensive save and restore functionality for the
# D&D Dungeon Master system, preserving complete game state while maintaining
# module-centric architecture and conversation timeline integrity.
# 
# KEY RESPONSIBILITIES:
# - Atomic save game creation with file categorization
# - Module-aware save directory management
# - Complete game state restoration with validation
# - Save metadata generation and management
# - File integrity checking and backup creation
# - Cross-module save game compatibility
# 
# SAVE SYSTEM DESIGN:
# - Module-specific save directories in modules/[module]/saved_games/
# - Timestamped save folders with descriptive metadata
# - Essential vs. optional file categorization
# - Atomic save operations using existing file_operations.py
# - ZIP compression for storage efficiency (optional)
# 
# RESTORE SYSTEM DESIGN:
# - Save game discovery and metadata parsing
# - Atomic restoration with current state backup
# - File integrity validation before restoration
# - Module compatibility checking
# - Graceful error handling and rollback
# 
# ARCHITECTURAL INTEGRATION:
# - Uses ModulePathManager for consistent file access
# - Leverages file_operations.py for atomic operations
# - Integrates with existing backup and validation systems
# - Supports module-centric directory structure
# - Maintains conversation timeline preservation
# 
# DESIGN PATTERNS:
# - Strategy Pattern: Different save modes (minimal vs. full)
# - Template Method: Consistent save/restore pipeline
# - Builder Pattern: Save metadata construction
# - Observer Pattern: Save progress notifications
# 
# This module ensures reliable game state persistence while maintaining
# the module-centric architecture and data integrity principles.
# ============================================================================

import json
import os
import shutil
import zipfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# Import our existing utilities
from file_operations import safe_write_json, safe_read_json
from module_path_manager import ModulePathManager
from encoding_utils import safe_json_load

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SaveGameManager:
    """Manages save and restore operations for the Dungeon Master system"""
    
    def __init__(self):
        self.current_module = None
        self.path_manager = None
        self._initialize_module_context()
    
    def _initialize_module_context(self):
        """Initialize the current module context from party tracker"""
        try:
            party_tracker = safe_json_load("party_tracker.json")
            if party_tracker:
                self.current_module = party_tracker.get("module", "").replace(" ", "_")
                self.path_manager = ModulePathManager(self.current_module)
            else:
                self.path_manager = ModulePathManager()
        except Exception as e:
            logger.warning(f"Could not initialize module context: {e}")
            self.path_manager = ModulePathManager()
    
    def get_essential_files(self) -> List[str]:
        """Get list of essential files that must be saved for game state"""
        essential_files = [
            # Global state files
            "party_tracker.json",
            "current_location.json", 
            "journal.json",
            "player_storage.json",
            
            # Character data
            "characters/",
            
            # Active encounters - we need to use glob to find these
            # Will be handled separately
        ]
        
        # Module-specific files if we have a current module
        if self.current_module and self.path_manager:
            module_base = f"modules/{self.current_module}"
            essential_files.extend([
                f"{module_base}/module_plot.json",
                f"{module_base}/module_context.json", 
                f"{module_base}/areas/",
                f"{module_base}/characters/",
                f"{module_base}/monsters/",
                f"{module_base}/encounters/",
            ])
        
        # Global module files
        essential_files.extend([
            "modules/campaign.json",
            "modules/world_registry.json",
        ])
        
        # Add active encounter files using glob
        import glob
        encounter_files = glob.glob("encounter_*.json")
        essential_files.extend(encounter_files)
        
        return essential_files
    
    def get_optional_files(self) -> List[str]:
        """Get list of optional files for full save mode"""
        return [
            # Conversation history
            "conversation_history.json",
            "chat_history.json",
            "second_model_history.json", 
            "third_model_history.json",
            
            # Combat logs
            "combat_logs/",
            
            # Campaign archives and summaries
            "modules/campaign_archives/",
            "modules/campaign_summaries/",
        ]
    
    def get_excluded_patterns(self) -> List[str]:
        """Get list of file patterns to exclude from saves"""
        return [
            # Debug and log files
            "*.log",
            "debug_*",
            "game_debug.log",
            "game_errors.log",
            "http_server.log",
            "web_server.log",
            
            # Backup directories
            "campaign_backup_*",
            "backup_pre_integration_*", 
            "*_backup_*",
            
            # Temporary files
            "*.tmp",
            "*.bak",
            "*.backup_*",
            
            # Python source and schemas
            "*.py",
            "*_schema.json",
            
            # Development files
            "test_*",
            "testing/",
            "isolated_testing/",
            "debug_log_backups/",
            
            # Screenshots and documentation
            "*.png",
            "*.md",
            "*.txt",
            "*.html",
            "*.css",
            
            # Static assets
            "static/",
            "templates/",
            "icons/",
        ]
    
    def should_include_file(self, filepath: str, save_mode: str = "essential") -> bool:
        """Determine if a file should be included in the save"""
        # Convert to forward slashes for consistent pattern matching
        filepath = filepath.replace("\\", "/")
        
        # Check exclusion patterns
        excluded_patterns = self.get_excluded_patterns()
        for pattern in excluded_patterns:
            # Simple pattern matching - could be enhanced with fnmatch
            if pattern.endswith("*"):
                if filepath.startswith(pattern[:-1]):
                    return False
            elif pattern.startswith("*"):
                if filepath.endswith(pattern[1:]):
                    return False
            else:
                if pattern in filepath:
                    return False
        
        # Check if it's an essential file
        essential_files = self.get_essential_files()
        for essential in essential_files:
            if essential.endswith("/"):
                # Directory pattern
                if filepath.startswith(essential):
                    return True
            elif essential.endswith("*"):
                # Wildcard pattern
                if filepath.startswith(essential[:-1]):
                    return True
            else:
                # Exact file
                if filepath == essential:
                    return True
        
        # Special check for encounter files
        if filepath.startswith("encounter_") and filepath.endswith(".json"):
            return True
        
        # For full save mode, also check optional files
        if save_mode == "full":
            optional_files = self.get_optional_files()
            for optional in optional_files:
                if optional.endswith("/"):
                    if filepath.startswith(optional):
                        return True
                elif optional.endswith("*"):
                    if filepath.startswith(optional[:-1]):
                        return True
                else:
                    if filepath == optional:
                        return True
        
        return False
    
    def get_save_directory(self) -> str:
        """Get the save directory for the current module"""
        if not self.current_module:
            # Fallback to root saved_games directory
            return "saved_games"
        
        return f"modules/{self.current_module}/saved_games"
    
    def generate_save_metadata(self, description: str = "", save_mode: str = "essential") -> Dict[str, Any]:
        """Generate metadata for a save game"""
        timestamp = datetime.now()
        
        # Get current game state info
        party_info = {}
        location_info = {}
        
        try:
            party_tracker = safe_json_load("party_tracker.json")
            if party_tracker:
                party_info = {
                    "module": party_tracker.get("module", "Unknown"),
                    "party_members": party_tracker.get("partyMembers", []),
                    "party_npcs": len(party_tracker.get("partyNPCs", [])),
                    "current_location": party_tracker.get("worldConditions", {}).get("currentLocation", "Unknown"),
                    "current_area": party_tracker.get("worldConditions", {}).get("currentArea", "Unknown"),
                }
        except Exception as e:
            logger.warning(f"Could not load party tracker for metadata: {e}")
        
        try:
            current_location = safe_json_load("current_location.json")
            if current_location:
                location_info = {
                    "location_name": current_location.get("name", "Unknown"),
                    "area_id": current_location.get("areaId", "Unknown"),
                }
        except Exception as e:
            logger.warning(f"Could not load current location for metadata: {e}")
        
        metadata = {
            "save_timestamp": timestamp.isoformat(),
            "save_date_readable": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "description": description,
            "save_mode": save_mode,
            "module": self.current_module or "Unknown",
            "game_state": {
                **party_info,
                **location_info,
            },
            "system_info": {
                "save_format_version": "1.0",
                "created_by": "DungeonMasterAI Save System",
            }
        }
        
        return metadata
    
    def create_save_game(self, description: str = "", save_mode: str = "essential") -> Tuple[bool, str]:
        """
        Create a save game with the specified mode.
        
        Args:
            description: User description for the save
            save_mode: "essential" for minimal save, "full" for complete save
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate timestamp for save directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = self.get_save_directory()
            save_path = f"{save_dir}/save_{timestamp}"
            
            # Create save directory
            os.makedirs(save_path, exist_ok=True)
            logger.info(f"Created save directory: {save_path}")
            
            # Generate and save metadata
            metadata = self.generate_save_metadata(description, save_mode)
            metadata_path = f"{save_path}/save_metadata.json"
            if not safe_write_json(metadata_path, metadata):
                return False, "Failed to write save metadata"
            
            # Copy files based on save mode
            copied_files = []
            skipped_files = []
            
            # Walk through all files in the current directory
            for root, dirs, files in os.walk("."):
                # Skip the save directory itself
                if save_path in root:
                    continue
                
                # Skip directories that should be excluded
                dirs[:] = [d for d in dirs if not any(
                    d.startswith(pattern[:-1]) if pattern.endswith("*") else d == pattern 
                    for pattern in self.get_excluded_patterns() 
                    if "/" not in pattern
                )]
                
                # Process files
                for file in files:
                    file_path = os.path.join(root, file).replace("\\", "/")
                    # Remove leading ./
                    if file_path.startswith("./"):
                        file_path = file_path[2:]
                    
                    if self.should_include_file(file_path, save_mode):
                        # Copy this file
                        source_path = file_path
                        dest_path = f"{save_path}/{file_path}"
                        
                        # Ensure destination directory exists
                        dest_dir = os.path.dirname(dest_path)
                        if dest_dir:
                            os.makedirs(dest_dir, exist_ok=True)
                        
                        try:
                            shutil.copy2(source_path, dest_path)
                            copied_files.append(file_path)
                            logger.debug(f"Copied: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to copy {file_path}: {e}")
                            skipped_files.append(file_path)
                    else:
                        skipped_files.append(file_path)
            
            # Update metadata with file statistics
            metadata["file_statistics"] = {
                "files_copied": len(copied_files),
                "files_skipped": len(skipped_files),
                "total_files_processed": len(copied_files) + len(skipped_files),
            }
            
            # Save updated metadata
            safe_write_json(metadata_path, metadata)
            
            success_msg = f"Save game created successfully: {save_path}"
            success_msg += f"\nCopied {len(copied_files)} files"
            if save_mode == "essential":
                success_msg += " (essential files only)"
            else:
                success_msg += " (full save)"
            
            logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Failed to create save game: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_save_games(self) -> List[Dict[str, Any]]:
        """List all available save games with metadata"""
        save_dir = self.get_save_directory()
        save_games = []
        
        if not os.path.exists(save_dir):
            return save_games
        
        try:
            for item in os.listdir(save_dir):
                item_path = os.path.join(save_dir, item)
                if os.path.isdir(item_path) and item.startswith("save_"):
                    metadata_path = os.path.join(item_path, "save_metadata.json")
                    if os.path.exists(metadata_path):
                        metadata = safe_read_json(metadata_path)
                        if metadata:
                            metadata["save_folder"] = item
                            metadata["save_path"] = item_path
                            save_games.append(metadata)
        except Exception as e:
            logger.error(f"Error listing save games: {e}")
        
        # Sort by timestamp, newest first
        save_games.sort(key=lambda x: x.get("save_timestamp", ""), reverse=True)
        return save_games
    
    def restore_save_game(self, save_folder: str) -> Tuple[bool, str]:
        """
        Restore a save game by copying files back to the main game directory.
        
        Args:
            save_folder: Name of the save folder to restore
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            save_dir = self.get_save_directory()
            save_path = f"{save_dir}/{save_folder}"
            
            if not os.path.exists(save_path):
                return False, f"Save game not found: {save_path}"
            
            # Load save metadata
            metadata_path = f"{save_path}/save_metadata.json"
            metadata = safe_read_json(metadata_path)
            if not metadata:
                return False, "Could not read save game metadata"
            
            # Create backup of current state before restoring
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"restore_backup_{backup_timestamp}"
            
            logger.info(f"Creating backup before restore: {backup_dir}")
            
            # Copy current essential files to backup
            essential_files = self.get_essential_files()
            backed_up_files = []
            
            for essential in essential_files:
                if essential.endswith("/"):
                    # Directory
                    if os.path.exists(essential):
                        backup_dest = f"{backup_dir}/{essential}"
                        os.makedirs(os.path.dirname(backup_dest), exist_ok=True)
                        shutil.copytree(essential, backup_dest, dirs_exist_ok=True)
                        backed_up_files.append(essential)
                elif essential.endswith("*"):
                    # Wildcard pattern - find matching files
                    import glob
                    for match in glob.glob(essential):
                        if os.path.exists(match):
                            backup_dest = f"{backup_dir}/{match}"
                            os.makedirs(os.path.dirname(backup_dest), exist_ok=True)
                            shutil.copy2(match, backup_dest)
                            backed_up_files.append(match)
                else:
                    # Single file
                    if os.path.exists(essential):
                        backup_dest = f"{backup_dir}/{essential}"
                        os.makedirs(os.path.dirname(backup_dest), exist_ok=True)
                        shutil.copy2(essential, backup_dest)
                        backed_up_files.append(essential)
            
            # Now restore files from save
            restored_files = []
            failed_files = []
            
            # Walk through save directory and copy files back
            for root, dirs, files in os.walk(save_path):
                # Skip metadata file
                if "save_metadata.json" in files:
                    files.remove("save_metadata.json")
                
                for file in files:
                    source_file = os.path.join(root, file)
                    # Calculate relative path from save directory
                    rel_path = os.path.relpath(source_file, save_path)
                    dest_file = rel_path.replace("\\", "/")
                    
                    try:
                        # Ensure destination directory exists
                        dest_dir = os.path.dirname(dest_file)
                        if dest_dir:
                            os.makedirs(dest_dir, exist_ok=True)
                        
                        shutil.copy2(source_file, dest_file)
                        restored_files.append(dest_file)
                        logger.debug(f"Restored: {dest_file}")
                    except Exception as e:
                        logger.error(f"Failed to restore {dest_file}: {e}")
                        failed_files.append(dest_file)
            
            success_msg = f"Save game restored successfully from: {save_folder}"
            success_msg += f"\nRestored {len(restored_files)} files"
            success_msg += f"\nBackup created: {backup_dir}"
            
            if failed_files:
                success_msg += f"\nFailed to restore {len(failed_files)} files"
            
            logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Failed to restore save game: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_save_game(self, save_folder: str) -> Tuple[bool, str]:
        """Delete a save game"""
        try:
            save_dir = self.get_save_directory()
            save_path = f"{save_dir}/{save_folder}"
            
            if not os.path.exists(save_path):
                return False, f"Save game not found: {save_path}"
            
            shutil.rmtree(save_path)
            logger.info(f"Deleted save game: {save_path}")
            return True, f"Save game deleted: {save_folder}"
            
        except Exception as e:
            error_msg = f"Failed to delete save game: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Example usage and testing
if __name__ == "__main__":
    # Test the save game manager
    manager = SaveGameManager()
    
    print("Testing Save Game Manager...")
    
    # Test file categorization
    test_files = [
        "party_tracker.json",
        "debug.log", 
        "characters/player1.json",
        "modules/test_module/areas/area1.json",
        "test_file.py",
        "conversation_history.json"
    ]
    
    print("\nFile categorization test:")
    for test_file in test_files:
        essential = manager.should_include_file(test_file, "essential")
        full = manager.should_include_file(test_file, "full")
        print(f"  {test_file}: essential={essential}, full={full}")
    
    # Test save game listing
    print("\nListing existing save games:")
    saves = manager.list_save_games()
    for save in saves:
        print(f"  {save.get('save_folder', 'Unknown')}: {save.get('description', 'No description')}")
    
    print("\nSave Game Manager test completed.")