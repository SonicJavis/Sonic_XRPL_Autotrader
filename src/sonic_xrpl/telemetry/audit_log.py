"""Append-only audit log for system operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEntry:
    """A single immutable audit log entry."""

    action: str
    actor: str
    result: str
    notes: str = ""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLog:
    """Append-only audit log. Entries cannot be removed after appending."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        """Append an audit entry."""
        self._entries.append(entry)

    def add(
        self,
        action: str,
        actor: str,
        result: str,
        notes: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Create and append an audit entry."""
        entry = AuditEntry(
            action=action,
            actor=actor,
            result=result,
            notes=notes,
            metadata=metadata or {},
        )
        self.append(entry)
        return entry

    def entries(self) -> list[AuditEntry]:
        """Return a copy of all entries."""
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
