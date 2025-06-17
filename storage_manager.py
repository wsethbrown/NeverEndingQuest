# ============================================================================
# STORAGE_MANAGER.PY - PLAYER STORAGE SYSTEM WITH ATOMIC FILE PROTECTION
# ============================================================================
# 
# ARCHITECTURE ROLE: Player Storage Management Layer
# 
# This module implements a safe, atomic player storage system that allows
# players to create and manage storage containers at specific locations.
# All operations use backup/restore patterns to ensure data integrity.
# 
# KEY RESPONSIBILITIES:
# - Manage player-created storage containers
# - Execute atomic inventory transfers between characters and storage
# - Provide backup/restore functionality for all file operations
# - Validate all operations against schemas
# - Maintain storage persistence across sessions and modules
# 
# SAFETY FEATURES:
# - Atomic file operations with automatic rollback
# - Character file backup before inventory modifications
# - Storage file backup before any changes
# - Schema validation for all data structures
# - Full operation rollback on any failure
# 
# STORAGE DESIGN:
# - Central player_storage.json repository
# - Location-tied storage containers
# - Player-initiated storage creation only
# - Party-accessible storage by default
# ============================================================================

import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import jsonschema
from encoding_utils import safe_json_load, safe_json_dump
from module_path_manager import ModulePathManager

class StorageManager:
    """Manages player storage with atomic file protection"""
    
    def __init__(self):
        """Initialize storage manager"""
        self.storage_file = "player_storage.json"
        self.schema_file = "storage_action_schema.json"
        self.path_manager = ModulePathManager()
        self._ensure_storage_file_exists()
        
    def _ensure_storage_file_exists(self):
        """Ensure player storage file exists with proper structure"""
        if not os.path.exists(self.storage_file):
            initial_data = {
                "version": "1.0.0",
                "lastUpdated": datetime.now().isoformat(),
                "playerStorage": []
            }
            safe_json_dump(initial_data, self.storage_file)
            
    def _create_backup(self, file_path: str) -> str:
        """Create a timestamped backup of a file"""
        if not os.path.exists(file_path):
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path
        
    def _restore_backup(self, original_path: str, backup_path: str):
        """Restore a file from backup"""
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, original_path)
            os.remove(backup_path)
            
    def _cleanup_backup(self, backup_path: str):
        """Remove backup file after successful operation"""
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
            
    def _validate_storage_operation(self, operation: Dict[str, Any]) -> bool:
        """Validate storage operation against schema"""
        try:
            if os.path.exists(self.schema_file):
                schema = safe_json_load(self.schema_file)
                jsonschema.validate(operation, schema)
            return True
        except (jsonschema.ValidationError, Exception) as e:
            print(f"[ERROR] Storage operation validation failed: {e}")
            return False
            
    def _find_item_in_character(self, character_data: Dict[str, Any], item_name: str, quantity: int) -> Tuple[bool, int, Dict[str, Any]]:
        """Find and validate item in character inventory"""
        equipment = character_data.get("equipment", [])
        
        for item in equipment:
            if item.get("item_name") == item_name:
                available_quantity = item.get("quantity", 1)
                if available_quantity >= quantity:
                    return True, available_quantity, item
                else:
                    return False, available_quantity, item
                    
        return False, 0, None
        
    def _remove_item_from_character(self, character_data: Dict[str, Any], item_name: str, quantity: int) -> bool:
        """Remove item from character inventory"""
        equipment = character_data.get("equipment", [])
        
        for i, item in enumerate(equipment):
            if item.get("item_name") == item_name:
                current_quantity = item.get("quantity", 1)
                if current_quantity >= quantity:
                    if current_quantity == quantity:
                        # Remove item completely
                        equipment.pop(i)
                    else:
                        # Reduce quantity
                        item["quantity"] = current_quantity - quantity
                    return True
                    
        return False
        
    def _add_item_to_character(self, character_data: Dict[str, Any], item_data: Dict[str, Any], quantity: int):
        """Add item to character inventory"""
        equipment = character_data.get("equipment", [])
        
        # Check if item already exists in inventory
        for item in equipment:
            if item.get("item_name") == item_data["item_name"]:
                item["quantity"] = item.get("quantity", 1) + quantity
                return
                
        # Add new item to inventory
        new_item = item_data.copy()
        new_item["quantity"] = quantity
        equipment.append(new_item)
        
    def _find_storage_at_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Find all storage containers at a specific location"""
        storage_data = safe_json_load(self.storage_file)
        return [
            storage for storage in storage_data.get("playerStorage", [])
            if storage.get("locationId") == location_id
        ]
        
    def _get_location_info(self, location_description: str) -> Tuple[str, str, str, str]:
        """Get location information from description"""
        # This is a simplified implementation
        # In practice, this would use AI or lookup tables to map descriptions to IDs
        
        # For now, get current location from party tracker
        try:
            party_data = safe_json_load("party_tracker.json")
            current_location_id = party_data.get("worldConditions", {}).get("currentLocationId", "UNKNOWN")
            current_location_name = party_data.get("worldConditions", {}).get("currentLocation", "Unknown Location")
            current_area_id = party_data.get("worldConditions", {}).get("currentAreaId", "UNKNOWN")
            current_area_name = party_data.get("worldConditions", {}).get("currentArea", "Unknown Area")
            
            return current_location_id, current_location_name, current_area_id, current_area_name
        except:
            return "UNKNOWN", "Unknown Location", "UNKNOWN", "Unknown Area"
            
    def create_storage(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new storage container"""
        if not self._validate_storage_operation(operation):
            return {"success": False, "error": "Invalid storage operation"}
            
        storage_backup = None
        
        try:
            # Create backup of storage file
            storage_backup = self._create_backup(self.storage_file)
            
            # Load current storage data
            storage_data = safe_json_load(self.storage_file)
            
            # Get location information
            location_id, location_name, area_id, area_name = self._get_location_info(
                operation.get("location_description", "")
            )
            
            # Generate unique storage ID
            storage_id = f"storage_{uuid.uuid4().hex[:8]}"
            
            # Create storage entry
            new_storage = {
                "id": storage_id,
                "deviceType": operation["storage_type"],
                "deviceName": operation.get("storage_name", f"{operation['storage_type'].title()} at {location_name}"),
                "locationId": location_id,
                "locationName": location_name,
                "areaId": area_id,
                "areaName": area_name,
                "contents": [],
                "createdBy": operation["character"],
                "createdDate": datetime.now().isoformat(),
                "accessibility": "party",
                "lastAccessed": datetime.now().isoformat(),
                "accessLog": [
                    {
                        "character": operation["character"],
                        "action": "create",
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            # Add to storage data
            storage_data["playerStorage"].append(new_storage)
            storage_data["lastUpdated"] = datetime.now().isoformat()
            
            # Save updated storage data
            safe_json_dump(storage_data, self.storage_file)
            
            # Clean up backup
            self._cleanup_backup(storage_backup)
            
            return {
                "success": True,
                "storage_id": storage_id,
                "message": f"Created {operation['storage_type']} at {location_name}"
            }
            
        except Exception as e:
            # Restore backup on failure
            if storage_backup:
                self._restore_backup(self.storage_file, storage_backup)
                
            return {"success": False, "error": f"Failed to create storage: {str(e)}"}
            
    def store_item(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Store an item in a storage container"""
        if not self._validate_storage_operation(operation):
            return {"success": False, "error": "Invalid storage operation"}
            
        character_backup = None
        storage_backup = None
        
        try:
            # Get character file path
            character_file = self.path_manager.get_character_path(operation["character"])
            
            # Create backups
            character_backup = self._create_backup(character_file)
            storage_backup = self._create_backup(self.storage_file)
            
            # Load character data
            character_data = safe_json_load(character_file)
            
            # Validate item exists in character inventory
            has_item, available_quantity, item_data = self._find_item_in_character(
                character_data, operation["item_name"], operation["quantity"]
            )
            
            if not has_item:
                raise Exception(f"Character does not have {operation['item_name']}")
                
            if available_quantity < operation["quantity"]:
                raise Exception(f"Character only has {available_quantity} {operation['item_name']}, requested {operation['quantity']}")
                
            # Get or create storage
            storage_id = operation.get("storage_id")
            if not storage_id:
                # Create new storage first
                create_operation = {
                    "action": "create_storage",
                    "character": operation["character"],
                    "storage_type": operation.get("storage_type", "chest"),
                    "storage_name": operation.get("storage_name"),
                    "location_description": operation.get("location_description", "")
                }
                create_result = self.create_storage(create_operation)
                if not create_result["success"]:
                    raise Exception(f"Failed to create storage: {create_result['error']}")
                storage_id = create_result["storage_id"]
                
            # Load storage data
            storage_data = safe_json_load(self.storage_file)
            
            # Find the storage container
            storage_container = None
            for storage in storage_data["playerStorage"]:
                if storage["id"] == storage_id:
                    storage_container = storage
                    break
                    
            if not storage_container:
                raise Exception(f"Storage container {storage_id} not found")
                
            # Remove item from character
            if not self._remove_item_from_character(character_data, operation["item_name"], operation["quantity"]):
                raise Exception(f"Failed to remove {operation['item_name']} from character")
                
            # Add item to storage
            storage_contents = storage_container["contents"]
            
            # Check if item already exists in storage
            item_found = False
            for stored_item in storage_contents:
                if stored_item["item_name"] == operation["item_name"]:
                    stored_item["quantity"] = stored_item.get("quantity", 1) + operation["quantity"]
                    item_found = True
                    break
                    
            if not item_found:
                # Add new item to storage
                stored_item = {
                    "item_name": item_data["item_name"],
                    "item_type": item_data.get("item_type", "miscellaneous"),
                    "quantity": operation["quantity"],
                    "description": item_data.get("description", "")
                }
                storage_contents.append(stored_item)
                
            # Update access log
            storage_container["lastAccessed"] = datetime.now().isoformat()
            storage_container["accessLog"].append({
                "character": operation["character"],
                "action": "store_item",
                "item": operation["item_name"],
                "quantity": operation["quantity"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Save updated data
            safe_json_dump(character_data, character_file)
            safe_json_dump(storage_data, self.storage_file)
            
            # Clean up backups
            self._cleanup_backup(character_backup)
            self._cleanup_backup(storage_backup)
            
            return {
                "success": True,
                "message": f"Stored {operation['quantity']} {operation['item_name']} in {storage_container['deviceName']}"
            }
            
        except Exception as e:
            # Restore backups on failure
            if character_backup:
                self._restore_backup(character_file, character_backup)
            if storage_backup:
                self._restore_backup(self.storage_file, storage_backup)
                
            return {"success": False, "error": f"Failed to store item: {str(e)}"}
            
    def retrieve_item(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve an item from a storage container"""
        if not self._validate_storage_operation(operation):
            return {"success": False, "error": "Invalid storage operation"}
            
        character_backup = None
        storage_backup = None
        
        try:
            # Get character file path
            character_file = self.path_manager.get_character_path(operation["character"])
            
            # Create backups
            character_backup = self._create_backup(character_file)
            storage_backup = self._create_backup(self.storage_file)
            
            # Load data
            character_data = safe_json_load(character_file)
            storage_data = safe_json_load(self.storage_file)
            
            # Find storage container
            storage_container = None
            for storage in storage_data["playerStorage"]:
                if storage["id"] == operation["storage_id"]:
                    storage_container = storage
                    break
                    
            if not storage_container:
                raise Exception(f"Storage container {operation['storage_id']} not found")
                
            # Find item in storage
            stored_item = None
            for item in storage_container["contents"]:
                if item["item_name"] == operation["item_name"]:
                    stored_item = item
                    break
                    
            if not stored_item:
                raise Exception(f"{operation['item_name']} not found in storage")
                
            available_quantity = stored_item.get("quantity", 1)
            if available_quantity < operation["quantity"]:
                raise Exception(f"Storage only has {available_quantity} {operation['item_name']}, requested {operation['quantity']}")
                
            # Remove item from storage
            if available_quantity == operation["quantity"]:
                storage_container["contents"].remove(stored_item)
            else:
                stored_item["quantity"] = available_quantity - operation["quantity"]
                
            # Add item to character
            self._add_item_to_character(character_data, stored_item, operation["quantity"])
            
            # Update access log
            storage_container["lastAccessed"] = datetime.now().isoformat()
            storage_container["accessLog"].append({
                "character": operation["character"],
                "action": "retrieve_item",
                "item": operation["item_name"],
                "quantity": operation["quantity"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Save updated data
            safe_json_dump(character_data, character_file)
            safe_json_dump(storage_data, self.storage_file)
            
            # Clean up backups
            self._cleanup_backup(character_backup)
            self._cleanup_backup(storage_backup)
            
            return {
                "success": True,
                "message": f"Retrieved {operation['quantity']} {operation['item_name']} from {storage_container['deviceName']}"
            }
            
        except Exception as e:
            # Restore backups on failure
            if character_backup:
                self._restore_backup(character_file, character_backup)
            if storage_backup:
                self._restore_backup(self.storage_file, storage_backup)
                
            return {"success": False, "error": f"Failed to retrieve item: {str(e)}"}
            
    def view_storage(self, location_id: str = None) -> Dict[str, Any]:
        """View storage containers at a location"""
        try:
            storage_data = safe_json_load(self.storage_file)
            
            if location_id:
                # Get storage at specific location
                location_storage = self._find_storage_at_location(location_id)
            else:
                # Get all storage
                location_storage = storage_data.get("playerStorage", [])
                
            storage_info = []
            for storage in location_storage:
                storage_info.append({
                    "id": storage["id"],
                    "name": storage["deviceName"],
                    "type": storage["deviceType"],
                    "location": storage["locationName"],
                    "contents": storage["contents"],
                    "created_by": storage["createdBy"],
                    "last_accessed": storage["lastAccessed"]
                })
                
            return {
                "success": True,
                "storage": storage_info,
                "count": len(storage_info)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to view storage: {str(e)}"}
            
    def get_storage_at_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Get all storage containers at a specific location"""
        try:
            return self._find_storage_at_location(location_id)
        except:
            return []

# Convenience functions for external use
def get_storage_manager() -> StorageManager:
    """Get storage manager instance"""
    return StorageManager()

def execute_storage_operation(operation: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a storage operation"""
    manager = get_storage_manager()
    
    action = operation.get("action")
    
    if action == "create_storage":
        return manager.create_storage(operation)
    elif action == "store_item":
        return manager.store_item(operation)
    elif action == "retrieve_item":
        return manager.retrieve_item(operation)
    elif action == "view_storage":
        location_id = operation.get("location_id")
        return manager.view_storage(location_id)
    else:
        return {"success": False, "error": f"Unknown storage action: {action}"}