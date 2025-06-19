# Storage Cleanup Plan

## Objective
Remove all test storage containers from the General Store location in player_storage.json

## Current State
- 7 storage containers incorrectly reference location "R01" (General Store)
- 1 storage container correctly references location "A05" (The Wyrd Lantern Inn)
- Location "R01" doesn't exist in the game files - should be "A01"

## Tasks
1. Backup player_storage.json
2. Remove all storage containers with locationId "R01" 
3. Keep only the storage container at "A05" (The Wyrd Lantern Inn)
4. Verify the cleaned file structure

## Storage Containers to Remove
- storage_dfc39d52 - Iron Strongbox (empty)
- storage_c29b3c43 - Battered Coffer (contains various items)
- storage_307bc124 - Cupboard under the counter 
- storage_fd3ae6a3 - General Store Storage
- storage_cc3d6b17 - Osric's lockbox
- storage_992ab035 - Osric's storeroom crate
- storage_fa3e6e46 - Norn's Private Locker
- storage_5a4cde73 - Norn's Private Locker (duplicate, empty)

## Storage Container to Keep
- storage_d4b5fb1f - Cira's Sturdy Chest at The Wyrd Lantern Inn (A05)