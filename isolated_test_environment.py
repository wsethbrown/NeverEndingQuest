#!/usr/bin/env python3
"""
Isolated Test Environment Manager for NeverEndingQuest
Creates completely isolated testing environments to prevent interference with main game
"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from encoding_utils import safe_json_load, safe_json_dump
from enhanced_logger import game_logger

class IsolatedTestEnvironment:
    """Manages isolated testing environments for comprehensive game testing"""
    
    def __init__(self, test_name: str, base_module: str = "Keep_of_Doom"):
        self.test_name = test_name
        self.base_module = base_module
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_id = f"{test_name}_{self.timestamp}"
        
        # Directory paths
        self.base_dir = Path.cwd()
        self.isolated_dir = self.base_dir / "isolated_testing" / self.test_id
        self.backup_dir = self.isolated_dir / "backups"
        self.logs_dir = self.isolated_dir / "logs"
        
        # File tracking
        self.original_files = {}
        self.test_files = {}
        self.created_files = []
        
        # State tracking
        self.is_active = False
        self.cleanup_registered = False
        
    def create_environment(self) -> bool:
        """Create isolated testing environment"""
        try:
            game_logger.info(f"Creating isolated test environment: {self.test_id}")
            
            # Create directory structure
            self.isolated_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            self.logs_dir.mkdir(exist_ok=True)
            
            # Copy essential files to isolated environment
            essential_files = [
                "main.py",
                "action_handler.py", 
                "ai_player.py",
                "enhanced_logger.py",
                "storage_manager.py",
                "storage_processor.py",
                "location_manager.py",
                "module_path_manager.py",
                "file_operations.py",
                "encoding_utils.py",
                "config.py",
                "test_objectives.json"
            ]
            
            # Copy Python modules
            for file_name in essential_files:
                if Path(file_name).exists():
                    shutil.copy2(file_name, self.isolated_dir)
                    self.test_files[file_name] = self.isolated_dir / file_name
                    
            # Copy module directory with clean state
            self._create_clean_module_copy()
            
            # Create clean game state files
            self._create_clean_game_state()
            
            # Create test-specific configuration
            self._create_test_config()
            
            self.is_active = True
            game_logger.info(f"Isolated environment created at: {self.isolated_dir}")
            return True
            
        except Exception as e:
            game_logger.error(f"Failed to create isolated environment: {str(e)}")
            return False
    
    def _create_clean_module_copy(self):
        """Create a clean copy of the game module for testing"""
        try:
            source_module = self.base_dir / "modules" / self.base_module
            target_module = self.isolated_dir / "modules" / self.base_module
            
            if source_module.exists():
                # Create target directory
                target_module.mkdir(parents=True, exist_ok=True)
                
                # Copy essential module files and directories
                essential_paths = [
                    "areas",
                    "characters", 
                    "monsters",
                    "module_plot.json",
                    "module_context.json"
                ]
                
                for path_name in essential_paths:
                    source_path = source_module / path_name
                    target_path = target_module / path_name
                    
                    if source_path.exists():
                        if source_path.is_dir():
                            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(source_path, target_path)
                            
                game_logger.info(f"Clean module copy created: {target_module}")
            else:
                game_logger.warning(f"Source module not found: {source_module}")
                
        except Exception as e:
            game_logger.error(f"Failed to create clean module copy: {str(e)}")
    
    def _create_clean_game_state(self):
        """Create clean game state files for testing"""
        try:
            # Clean party tracker
            clean_party_tracker = {
                "module": self.base_module,
                "partyMembers": ["norn"],
                "partyNPCs": [],
                "worldConditions": {
                    "year": 1492,
                    "month": "Ches",
                    "day": 1, 
                    "time": "08:00:00",
                    "weather": "Clear",
                    "season": "Spring",
                    "dayNightCycle": "Morning",
                    "moonPhase": "New Moon",
                    "currentLocation": "Harrow's Hollow General Store",
                    "currentLocationId": "R01",
                    "currentArea": "Harrow's Hollow", 
                    "currentAreaId": "HH001",
                    "majorEventsUnderway": [],
                    "politicalClimate": "",
                    "activeEncounter": "",
                    "activeCombatEncounter": ""
                },
                "activeQuests": []
            }
            
            party_file = self.isolated_dir / "party_tracker.json"
            safe_json_dump(clean_party_tracker, str(party_file))
            self.test_files["party_tracker.json"] = party_file
            
            # Clean conversation history
            clean_history = {
                "module": self.base_module,
                "conversation": []
            }
            
            history_file = self.isolated_dir / "conversation_history.json"
            safe_json_dump(clean_history, str(history_file))
            self.test_files["conversation_history.json"] = history_file
            
            # Clean journal
            clean_journal = {
                "module": self.base_module,
                "entries": []
            }
            
            journal_file = self.isolated_dir / "journal.json"
            safe_json_dump(clean_journal, str(journal_file))
            self.test_files["journal.json"] = journal_file
            
            # Clean storage
            clean_storage = {
                "version": "1.0.0",
                "lastUpdated": datetime.now().isoformat(),
                "playerStorage": []
            }
            
            storage_file = self.isolated_dir / "player_storage.json"
            safe_json_dump(clean_storage, str(storage_file))
            self.test_files["player_storage.json"] = storage_file
            
            game_logger.info("Clean game state files created")
            
        except Exception as e:
            game_logger.error(f"Failed to create clean game state: {str(e)}")
    
    def _create_test_config(self):
        """Create test-specific configuration"""
        try:
            test_config = {
                "test_environment": True,
                "test_id": self.test_id,
                "test_name": self.test_name,
                "base_module": self.base_module,
                "created_at": datetime.now().isoformat(),
                "isolation_enabled": True,
                "logging_enhanced": True,
                "validation_strict": True
            }
            
            config_file = self.isolated_dir / "test_config.json"
            safe_json_dump(test_config, str(config_file))
            self.test_files["test_config.json"] = config_file
            
            game_logger.info("Test configuration created")
            
        except Exception as e:
            game_logger.error(f"Failed to create test config: {str(e)}")
    
    def backup_original_files(self, file_paths: List[str]) -> bool:
        """Backup original files before testing"""
        try:
            for file_path in file_paths:
                file_obj = Path(file_path)
                if file_obj.exists():
                    backup_path = self.backup_dir / file_obj.name
                    shutil.copy2(file_obj, backup_path)
                    self.original_files[file_path] = backup_path
                    game_logger.debug(f"Backed up: {file_path} -> {backup_path}")
            
            return True
            
        except Exception as e:
            game_logger.error(f"Failed to backup files: {str(e)}")
            return False
    
    def switch_to_test_environment(self) -> bool:
        """Switch current working directory to test environment"""
        try:
            if not self.is_active:
                game_logger.error("Test environment not active")
                return False
                
            # Change to isolated directory
            os.chdir(self.isolated_dir)
            game_logger.info(f"Switched to test environment: {self.isolated_dir}")
            return True
            
        except Exception as e:
            game_logger.error(f"Failed to switch to test environment: {str(e)}")
            return False
    
    def restore_original_environment(self) -> bool:
        """Restore original working directory and files"""
        try:
            # Change back to original directory
            os.chdir(self.base_dir)
            
            # Restore any modified original files if needed
            # (Currently we don't modify originals, only work in isolation)
            
            game_logger.info("Restored to original environment")
            return True
            
        except Exception as e:
            game_logger.error(f"Failed to restore environment: {str(e)}")
            return False
    
    def get_test_results(self) -> Dict:
        """Collect and return test results"""
        try:
            results = {
                "test_id": self.test_id,
                "test_name": self.test_name,
                "environment_path": str(self.isolated_dir),
                "files_created": [str(f) for f in self.created_files],
                "logs_path": str(self.logs_dir),
                "timestamp": self.timestamp
            }
            
            # Collect log files
            log_files = list(self.logs_dir.glob("*.log"))
            results["log_files"] = [str(f) for f in log_files]
            
            # Check for test artifacts
            artifact_files = list(self.isolated_dir.glob("*test_results*.json"))
            results["artifact_files"] = [str(f) for f in artifact_files]
            
            return results
            
        except Exception as e:
            game_logger.error(f"Failed to collect test results: {str(e)}")
            return {"error": str(e)}
    
    def cleanup(self, preserve_logs: bool = True) -> bool:
        """Clean up test environment"""
        try:
            # Restore original environment first
            self.restore_original_environment()
            
            if preserve_logs:
                # Move logs to persistent location
                persistent_logs = self.base_dir / "test_logs" / self.test_id
                persistent_logs.mkdir(parents=True, exist_ok=True)
                
                if self.logs_dir.exists():
                    for log_file in self.logs_dir.glob("*"):
                        shutil.copy2(log_file, persistent_logs)
            
            # Remove isolated directory
            if self.isolated_dir.exists():
                shutil.rmtree(self.isolated_dir)
                game_logger.info(f"Cleaned up test environment: {self.test_id}")
            
            self.is_active = False
            return True
            
        except Exception as e:
            game_logger.error(f"Failed to cleanup test environment: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        if self.create_environment():
            self.switch_to_test_environment()
            return self
        else:
            raise RuntimeError("Failed to create test environment")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup(preserve_logs=True)

def create_isolated_test_environment(test_name: str, base_module: str = "Keep_of_Doom") -> IsolatedTestEnvironment:
    """Factory function to create isolated test environment"""
    return IsolatedTestEnvironment(test_name, base_module)

# Example usage
if __name__ == "__main__":
    # Test the isolated environment creation
    with create_isolated_test_environment("example_test") as test_env:
        print(f"Test environment created at: {test_env.isolated_dir}")
        print(f"Test files available: {list(test_env.test_files.keys())}")
        
        # Test environment is automatically cleaned up when exiting context