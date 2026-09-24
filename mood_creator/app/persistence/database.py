import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.models.action_result import ActionResult

logger = logging.getLogger(__name__)


class Database:
    """SQLite database helper for structured execution logs."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    mode_id TEXT NOT NULL,
                    mode_name TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    message TEXT,
                    error TEXT
                )
                """
            )
            conn.commit()

    def log_execution(
        self,
        mode_id: str,
        mode_name: str,
        action_name: str,
        result: ActionResult,
    ) -> None:
        """Insert execution result entry."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO execution_logs (timestamp, mode_id, mode_name, action_name, success, duration, message, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.timestamp,
                        mode_id,
                        mode_name,
                        action_name,
                        1 if result.success else 0,
                        result.duration,
                        result.message,
                        result.error,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to write log entry to database: {e}")

    def get_recent_logs(self, limit: int = 100, mode_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent logs, optionally filtered by mode_id."""
        query = "SELECT * FROM execution_logs "
        params: list = []
        if mode_id:
            query += "WHERE mode_id = ? "
            params.append(mode_id)
        query += "ORDER BY id DESC LIMIT ?"
        params.append(limit)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query execution logs: {e}")
            return []

    def clear_logs(self) -> None:
        """Clear all stored execution logs."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM execution_logs")
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing log table: {e}")
