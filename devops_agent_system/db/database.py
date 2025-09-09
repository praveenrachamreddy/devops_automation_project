
import aiosqlite
import logging
from pathlib import Path

# --- Constants and Configuration ---
DB_DIR = Path(__file__).parent.parent.parent
DB_FILE = DB_DIR / "adk_sessions.db"
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path

    async def init_database(self):
        """Initialize SQLite database with custom tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_connections (
                    session_id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
            logger.info("Custom database tables initialized successfully")

    async def add_connection(self, session_id: str, connection_id: str, user_id: str):
        """Adds a new connection to the active_connections table."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO active_connections 
                (session_id, connection_id, user_id, connected_at, last_activity)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (session_id, connection_id, user_id))
            await db.commit()

    async def remove_connection(self, session_id: str):
        """Removes a connection from the active_connections table."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM active_connections WHERE session_id = ?", (session_id,))
            await db.commit()

    async def update_connection_activity(self, session_id: str):
        """Updates the last_activity timestamp for a connection."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE active_connections 
                SET last_activity = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            await db.commit()
