#!/bin/bash
# Repository cleanup script for DungeonMasterAI
# This removes non-game-related files and organizes the repository

echo "Starting repository cleanup..."

# Create a backup branch first
git checkout -b pre-cleanup-backup-$(date +%Y%m%d-%H%M%S)
git checkout main

# Remove game data files from root (should be in campaigns/)
echo "Removing game data files from root..."
git rm -f DS001.json EM001.json EM001_BU.json "EM001_BU copy.json" Echoes_of_the_Elemental_Forge_campaign.json Gnomengarde.json 2>/dev/null
git rm -f map_DS001.json map_EM001.json plot_EM001.json plot_EM001_BU.json 2>/dev/null

# Remove encounter files from root
echo "Removing encounter files from root..."
git rm -f encounter_B01-E1.json encounter_B03-E1.json encounter_R13-E1.json encounter_R14-E1.json random_encounter.json 2>/dev/null

# Remove character/NPC files from root
echo "Removing character files from root..."
git rm -f elara.json gilly.json thalor.json eor.json norn.json.bak 2>/dev/null

# Remove legacy/backup folders
echo "Removing legacy and backup folders..."
git rm -rf legacy/ old_files/ backup/ backup_2/ back_up_3/ 2>/dev/null

# Remove test results files
echo "Removing test result files..."
git rm -f test_results_*.json 2>/dev/null

# Remove log files (should be in .gitignore)
echo "Removing log files..."
git rm -f *.log 2>/dev/null
git rm -f combat_validation_log.json 2>/dev/null

# Remove debug files
echo "Removing debug files..."
git rm -f debug_*.json prompt_validation.json summary_dump.json trimmed_summary_dump.json 2>/dev/null

# Remove conversation/history files (runtime data)
echo "Removing runtime conversation files..."
git rm -f conversation_history.json conversation_history.json.bak "conversation_history copy.json" 2>/dev/null
git rm -f combat_conversation_history.json second_model_history.json third_model_history.json 2>/dev/null
git rm -f dialogue_summary.json chat_history.json 2>/dev/null

# Remove copy files
echo "Removing copy files..."
git rm -f "adv_summary copy.py" "campaign copy.json" "loca_schema copy.json" "main copy.py" 2>/dev/null
git rm -f "map copy.json" "monster_builder copy.py" "npc_builder copy.py" "party_schema copy.json" 2>/dev/null
git rm -f "party_tracker copy.json" "plot copy.json" "plot_update copy.py" "system_prompt copy 6.txt" 2>/dev/null
git rm -f "update_encounter copy.py" "update_npc_info copy.py" "update_player_info copy.py" "validation_prompt copy.txt" 2>/dev/null

# Remove other temporary files
echo "Removing other temporary files..."
git rm -f chronology.json current_location.json map.json plot.json journal.json journal.json.bak 2>/dev/null
git rm -f party_tracker.json.bak party_tracker_echoes_backup_*.json 2>/dev/null
git rm -f campaign_notes.txt leveling_info.txt work_session_summary.md 2>/dev/null
git rm -f capture_screenshot.py character_stats_screenshot*.png install_gh.sh 2>/dev/null
git rm -f clear_output.txt test.py quick_test.py claude.txt test_objectives.json 2>/dev/null
git rm -f test_character_sheet.html test_character_sheet_compact.html 2>/dev/null
git rm -f plot_BU.json 2>/dev/null

# Remove empty monsters directory
echo "Removing empty monsters directory..."
git rm -rf monsters/ 2>/dev/null

# Remove system prompt backups
echo "Removing system prompt backups..."
git rm -f system_prompt_backup_*.txt system_prompt_experiment.txt system_prompt_main_quest_speedrun.txt system_prompt_test.txt 2>/dev/null

# Remove backup files
echo "Removing backup files..."
git rm -f campaign_debugger.py.bak campaign_generator.py.bak location_manager.py.bak 2>/dev/null

# Create/update .gitignore with proper patterns
echo "Creating comprehensive .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Logs
*.log
logs/

# Runtime data
conversation_history.json
conversation_history.json.bak
combat_conversation_history.json
current_location.json
party_tracker.json.bak
journal.json
journal.json.bak
chronology.json

# Debug files
debug_*.json
*_debug.json
prompt_validation.json
summary_dump.json

# Test results
test_results_*.json
test_runs/

# Backup files
*.bak
*_BU.json
*_backup_*
backup/
backup_*/
old_files/
legacy/

# Copy files
*copy.*
* copy.*

# Temporary files
*.tmp
*.temp
clear_output.txt
test_objectives.json

# Screenshots
*.png
*.jpg
*.jpeg

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Game data in root (should be in campaigns/)
/DS*.json
/EM*.json
/encounter_*.json
/map_*.json
/plot_*.json
/norn.json
/elara.json
/gilly.json
/thalor.json
/eor.json
/Gnomengarde.json
/*_campaign.json

# Temporary test files
test_character_sheet*.html
capture_screenshot.py
install_gh.sh
EOF

# Stage the .gitignore
git add .gitignore

echo "Cleanup complete! Review changes with 'git status'"
echo "To commit: git commit -m 'Clean up repository: remove game data and temporary files from root'"