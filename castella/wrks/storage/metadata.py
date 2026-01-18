"""SQLite-based metadata storage for app-level data."""

import sqlite3
from pathlib import Path
from typing import Optional


class MetadataStore:
    """Persistent storage for app metadata like favorites.

    Stores data in ~/.wrks/metadata.db
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the metadata store.

        Args:
            db_path: Custom path for the database (mainly for testing)
        """
        if db_path is None:
            self._db_dir = Path.home() / ".wrks"
            self._db_path = self._db_dir / "metadata.db"
        else:
            self._db_path = db_path
            self._db_dir = db_path.parent

        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure database and tables exist."""
        self._db_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    encoded_name TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()

    def add_favorite(self, encoded_name: str) -> None:
        """Mark a project as favorite.

        Args:
            encoded_name: The encoded project name (directory name)
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO favorites (encoded_name) VALUES (?)",
                (encoded_name,),
            )
            conn.commit()

    def remove_favorite(self, encoded_name: str) -> None:
        """Remove a project from favorites.

        Args:
            encoded_name: The encoded project name (directory name)
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "DELETE FROM favorites WHERE encoded_name = ?",
                (encoded_name,),
            )
            conn.commit()

    def is_favorite(self, encoded_name: str) -> bool:
        """Check if a project is a favorite.

        Args:
            encoded_name: The encoded project name (directory name)

        Returns:
            True if the project is a favorite
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM favorites WHERE encoded_name = ?",
                (encoded_name,),
            )
            return cursor.fetchone() is not None

    def get_favorites(self) -> set[str]:
        """Get all favorite project names.

        Returns:
            Set of encoded project names that are favorites
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT encoded_name FROM favorites")
            return {row[0] for row in cursor.fetchall()}

    def set_setting(self, key: str, value: str) -> None:
        """Store a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()
            return row[0] if row else default
