"""Ingestion fixture loader utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_fixture(fixture_path: Path) -> dict[str, Any]:
    """Load a JSON fixture file."""
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    with fixture_path.open() as f:
        return json.load(f)


def list_fixtures(fixture_dir: Path) -> list[Path]:
    """List all JSON fixtures in a directory."""
    if not fixture_dir.exists():
        return []
    return sorted(fixture_dir.glob("*.json"))
