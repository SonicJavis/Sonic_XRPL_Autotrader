"""Persistent kill switch for execution safety.

This module is intentionally fail-closed: if state cannot be loaded,
execution is treated as blocked.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from sonic_xrpl.db.models import KillSwitchState


DEFAULT_KILLSWITCH_ID = "global"
DEFAULT_REASON = "manual_override"
DEFAULT_ACTOR = "system"
ACTIVE_REASON = "killswitch_active"


class PersistentKillSwitch:
    """SQLite-backed kill switch that survives container restarts."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._create_tables()
        self._ensure_default_row()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS killswitch_state (
                killswitch_id TEXT PRIMARY KEY,
                is_active INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_by TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _ensure_default_row(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT OR IGNORE INTO killswitch_state
            (killswitch_id, is_active, updated_at, reason, updated_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (DEFAULT_KILLSWITCH_ID, 0, now, "initialized", DEFAULT_ACTOR),
        )
        self._conn.commit()

    def get_state(self) -> KillSwitchState:
        row = self._conn.execute(
            """
            SELECT is_active, updated_at, reason, updated_by
            FROM killswitch_state
            WHERE killswitch_id = ?
            """,
            (DEFAULT_KILLSWITCH_ID,),
        ).fetchone()
        if row is None:
            # fail-closed behavior if row is missing unexpectedly
            return KillSwitchState(
                is_active=True,
                updated_at=datetime.now(timezone.utc).isoformat(),
                reason="state_missing_fail_closed",
                updated_by=DEFAULT_ACTOR,
            )
        return KillSwitchState(
            is_active=bool(row[0]),
            updated_at=str(row[1]),
            reason=str(row[2]),
            updated_by=str(row[3]),
        )

    def set_state(
        self,
        *,
        is_active: bool,
        reason: str = DEFAULT_REASON,
        updated_by: str = DEFAULT_ACTOR,
    ) -> KillSwitchState:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE killswitch_state
            SET is_active = ?, updated_at = ?, reason = ?, updated_by = ?
            WHERE killswitch_id = ?
            """,
            (
                1 if is_active else 0,
                now,
                reason,
                updated_by,
                DEFAULT_KILLSWITCH_ID,
            ),
        )
        self._conn.commit()
        return self.get_state()

    def assert_execution_allowed(self) -> None:
        state = self.get_state()
        if state.is_active:
            raise RuntimeError(ACTIVE_REASON)

    def close(self) -> None:
        self._conn.close()

    def to_dict(self) -> dict[str, object]:
        return asdict(self.get_state())

