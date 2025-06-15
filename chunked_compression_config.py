"""
Configuration for chunked conversation compression
"""

# Chunked compression settings
COMPRESSION_TRIGGER = 15  # Number of location summaries to trigger compression
CHUNK_SIZE = 8           # Number of transitions to compress in each chunk
ENABLE_AUTO_COMPRESSION = True  # Enable automatic compression on location transitions

# Backup settings
CREATE_BACKUPS = True    # Create backups before compression
BACKUP_RETENTION_DAYS = 30  # How long to keep old backups

# File settings
CONVERSATION_FILE = "conversation_history.json"  # Main conversation history file