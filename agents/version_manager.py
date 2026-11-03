"""Version history manager for persistent file version tracking.

Uses SQLite to store file versions, supporting rollback and recovery.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Optional, Dict
from graph.state import FileVersion


class VersionManager:
    """Manages persistent version history for generated files."""

    def __init__(self, db_path: str = "version_history.db"):
        """Initialize version manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize SQLite database with version history tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create file_versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                generated_by TEXT,
                timestamp TEXT NOT NULL,
                description TEXT,
                syntax_valid BOOLEAN DEFAULT 1,
                is_working BOOLEAN DEFAULT 0,
                UNIQUE(file_path, version)
            )
        """)

        # Create rollback_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rollback_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                from_version INTEGER NOT NULL,
                to_version INTEGER NOT NULL,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_version(
        self,
        file_path: str,
        content: str,
        version: int,
        generated_by: str,
        description: str = "",
        syntax_valid: bool = True,
        is_working: bool = False,
    ) -> int:
        """Save a file version to the database.

        Args:
            file_path: Relative path to the file
            content: File content
            version: Version number
            generated_by: Subtask ID that generated this version
            description: Description of changes
            syntax_valid: Whether syntax is valid
            is_working: Whether this version passed tests

        Returns:
            Version ID in database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO file_versions
            (file_path, version, content, generated_by, timestamp, description, syntax_valid, is_working)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_path, version, content, generated_by, timestamp, description, syntax_valid, is_working),
        )

        version_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return version_id

    def get_version(self, file_path: str, version: int) -> Optional[FileVersion]:
        """Retrieve a specific version of a file.

        Args:
            file_path: Relative path to the file
            version: Version number

        Returns:
            FileVersion object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT version, content, generated_by, timestamp, description, syntax_valid
            FROM file_versions
            WHERE file_path = ? AND version = ?
            """,
            (file_path, version),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return FileVersion(
                version=row[0],
                content=row[1],
                generated_by=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                description=row[4],
                syntax_valid=row[5],
            )
        return None

    def get_latest_version(self, file_path: str) -> Optional[FileVersion]:
        """Retrieve the latest version of a file.

        Args:
            file_path: Relative path to the file

        Returns:
            FileVersion object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT version, content, generated_by, timestamp, description, syntax_valid
            FROM file_versions
            WHERE file_path = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (file_path,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return FileVersion(
                version=row[0],
                content=row[1],
                generated_by=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                description=row[4],
                syntax_valid=row[5],
            )
        return None

    def get_all_versions(self, file_path: str) -> List[FileVersion]:
        """Retrieve all versions of a file.

        Args:
            file_path: Relative path to the file

        Returns:
            List of FileVersion objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT version, content, generated_by, timestamp, description, syntax_valid
            FROM file_versions
            WHERE file_path = ?
            ORDER BY version ASC
            """,
            (file_path,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            FileVersion(
                version=row[0],
                content=row[1],
                generated_by=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                description=row[4],
                syntax_valid=row[5],
            )
            for row in rows
        ]

    def get_working_version(self, file_path: str) -> Optional[FileVersion]:
        """Retrieve the last known working version of a file.

        Args:
            file_path: Relative path to the file

        Returns:
            FileVersion object or None if no working version exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT version, content, generated_by, timestamp, description, syntax_valid
            FROM file_versions
            WHERE file_path = ? AND is_working = 1
            ORDER BY version DESC
            LIMIT 1
            """,
            (file_path,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return FileVersion(
                version=row[0],
                content=row[1],
                generated_by=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                description=row[4],
                syntax_valid=row[5],
            )
        return None

    def mark_as_working(self, file_path: str, version: int):
        """Mark a version as working (passed tests).

        Args:
            file_path: Relative path to the file
            version: Version number
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # First, unmark all versions of this file
        cursor.execute(
            """
            UPDATE file_versions
            SET is_working = 0
            WHERE file_path = ?
            """,
            (file_path,),
        )

        # Then mark the specific version as working
        cursor.execute(
            """
            UPDATE file_versions
            SET is_working = 1
            WHERE file_path = ? AND version = ?
            """,
            (file_path, version),
        )

        conn.commit()
        conn.close()

    def record_rollback(
        self,
        file_path: str,
        from_version: int,
        to_version: int,
        reason: str,
    ):
        """Record a rollback event.

        Args:
            file_path: Relative path to the file
            from_version: Version being rolled back from
            to_version: Version being rolled back to
            reason: Reason for rollback
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO rollback_events
            (file_path, from_version, to_version, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_path, from_version, to_version, reason, timestamp),
        )

        conn.commit()
        conn.close()

    def get_rollback_history(self, file_path: str) -> List[Dict]:
        """Get rollback history for a file.

        Args:
            file_path: Relative path to the file

        Returns:
            List of rollback event dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT from_version, to_version, reason, timestamp
            FROM rollback_events
            WHERE file_path = ?
            ORDER BY timestamp DESC
            """,
            (file_path,),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "from_version": row[0],
                "to_version": row[1],
                "reason": row[2],
                "timestamp": row[3],
            }
            for row in rows
        ]
