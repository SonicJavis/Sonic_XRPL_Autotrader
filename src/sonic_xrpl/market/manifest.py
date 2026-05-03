"""SnapshotManifest builder — provenance record for market snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sonic_xrpl.market.models import SnapshotManifest

BUILDER_VERSION = "2.0.0-phase47"


def compute_source_hash(data: Any) -> str:
    """Compute deterministic SHA-256 of sorted-JSON data."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_snapshot_id(fixture_id: str, ledger_index: int, generated_at: str) -> str:
    """Compute deterministic snapshot ID from fixture identity + ledger + timestamp."""
    raw = f"{fixture_id}|{ledger_index}|{generated_at}"
    return hashlib.sha256(raw.encode()).hexdigest()


def build_snapshot_manifest(
    *,
    fixture_id: str,
    ledger_index: int,
    input_paths: list[Path | str],
    limitations: list[str],
    source_hash: str,
) -> SnapshotManifest:
    """Build a SnapshotManifest with a deterministic snapshot_id."""
    generated_at = datetime.now(timezone.utc).isoformat()
    snapshot_id = compute_snapshot_id(fixture_id, ledger_index, generated_at)
    return SnapshotManifest(
        snapshot_id=snapshot_id,
        fixture_id=fixture_id,
        source_hash=source_hash,
        generated_at=generated_at,
        builder_version=BUILDER_VERSION,
        input_paths=[str(p) for p in input_paths],
        limitations=limitations,
    )
