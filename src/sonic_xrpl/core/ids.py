"""Deterministic ID generation utilities for V2 models."""

from __future__ import annotations

import hashlib
import uuid


def new_id() -> str:
    """Generate a new random UUID string."""
    return str(uuid.uuid4())


def deterministic_id(*parts: str) -> str:
    """Generate a deterministic 16-character hex ID from input strings."""
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
