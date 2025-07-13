# ============================================================================
# CONFIG_TEMPLATE.PY - SYSTEM CONFIGURATION TEMPLATE
# ============================================================================
# 
# ARCHITECTURE ROLE: Configuration Management - Central System Settings Template
# 
# This template provides the structure for config.py including API keys, model
# selections, file paths, and operational parameters. It implements our
# "Configurable AI Strategy" by allowing model selection per use case.
# 
# KEY RESPONSIBILITIES:
# - API key and authentication management template
# - AI model configuration for different use cases
# - File system path configuration
# - System operational parameters
# - Environment-specific settings
# 
# CONFIGURATION CATEGORIES:
# - AI Models: Different models for DM, combat, validation, generation
# - File Paths: Module directories and schema locations
# - API Settings: Keys, timeouts, and retry parameters
# - System Parameters: Debug modes, logging levels, validation settings
# 
# SECURITY CONSIDERATIONS:
# - API keys should be moved to environment variables in production
# - Sensitive configuration should not be committed to version control
# - Copy this template to config.py and add your actual API key
# 
# ARCHITECTURAL INTEGRATION:
# - Used by all modules requiring AI model access
# - Provides centralized model selection strategy
# - Enables easy switching between different AI configurations
# - Supports our multi-model AI architecture
# 
# This module enables our flexible, multi-model AI strategy while
# maintaining centralized configuration management.
# ============================================================================

# WARNING: Replace with your actual OpenAI API key and move to environment variables in production
OPENAI_API_KEY = "your_openai_api_key_here"

# --- Module folder structure ---
MODULES_DIR = "modules"
DEFAULT_MODULE = "The_Thornwood_Watch"

# --- Main Game Logic Models (used in main.py) ---
DM_MAIN_MODEL = "gpt-4.1-2025-04-14"
DM_SUMMARIZATION_MODEL = "gpt-4.1-mini-2025-04-14"
DM_VALIDATION_MODEL = "gpt-4.1-2025-04-14"

# --- Combat Simulation Models (used in combat_manager.py) ---
COMBAT_MAIN_MODEL = "gpt-4.1-2025-04-14"
# COMBAT_SCHEMA_UPDATER_MODEL - This was defined but not directly used.
# If needed for update_player_info, update_npc_info, update_encounter called from combat_sim,
# those modules will use their own specific models defined below.
COMBAT_DIALOGUE_SUMMARY_MODEL = "gpt-4.1-mini-2025-04-14"

# --- Utility and Builder Models ---
NPC_BUILDER_MODEL = "gpt-4.1-2025-04-14"                # Used in npc_builder.py
ADVENTURE_SUMMARY_MODEL = "gpt-4.1-mini-2025-04-14"
CHARACTER_VALIDATOR_MODEL = "gpt-4.1-2025-04-14"    # Used in adv_summary.py
PLOT_UPDATE_MODEL = "gpt-4.1-mini-2025-04-14"          # Used in plot_update.py
PLAYER_INFO_UPDATE_MODEL = "gpt-4.1-mini-2025-04-14"   # Used in update_player_info.py
NPC_INFO_UPDATE_MODEL = "gpt-4.1-mini-2025-04-14"      # Used in update_npc_info.py
MONSTER_BUILDER_MODEL = "gpt-4.1-2025-04-14"
ENCOUNTER_UPDATE_MODEL = "gpt-4.1-mini-2025-04-14"
LEVEL_UP_MODEL = "gpt-4.1-2025-04-14"                  # Used in level_up.py

# --- Testing Models ---
DM_MINI_MODEL = "gpt-4.1-mini-2025-04-14"              # Used for AI player in automated tests

# --- END OF FILE config_template.py ---