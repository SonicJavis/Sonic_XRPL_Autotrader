"""SQLite-backed storage for V2.

Uses Python stdlib sqlite3 — no external dependency.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sonic_xrpl.storage.models import StoredRecord


class SQLiteStore:
    """Simple SQLite storage for V2 records."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._path = str(db_path)
        self._conn = sqlite3.connect(self._path)
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                record_id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def save(self, record: StoredRecord) -> None:
        """Save a record."""
        self._conn.execute(
            "INSERT OR REPLACE INTO records VALUES (?, ?, ?, ?)",
            (
                record.record_id,
                record.record_type,
                json.dumps(record.data),
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def load(self, record_id: str) -> StoredRecord | None:
        """Load a record by ID. Returns None if not found."""
        cursor = self._conn.execute(
            "SELECT record_id, record_type, data, created_at FROM records WHERE record_id = ?",
            (record_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return StoredRecord(
            record_id=row[0],
            record_type=row[1],
            data=json.loads(row[2]),
            created_at=datetime.fromisoformat(row[3]),
        )

    def list_by_type(self, record_type: str) -> list[StoredRecord]:
        """List all records of a given type."""
        cursor = self._conn.execute(
            "SELECT record_id, record_type, data, created_at FROM records WHERE record_type = ?",
            (record_type,),
        )
        return [
            StoredRecord(
                record_id=row[0],
                record_type=row[1],
                data=json.loads(row[2]),
                created_at=datetime.fromisoformat(row[3]),
            )
            for row in cursor.fetchall()
        ]

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
