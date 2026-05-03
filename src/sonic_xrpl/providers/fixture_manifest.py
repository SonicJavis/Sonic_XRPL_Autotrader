"""FixtureManifest for XRPL fixture metadata."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sonic_xrpl.providers.errors import FixtureMissingError


def compute_fixture_id(name: str, version: str, network: str) -> str:
    """Compute deterministic SHA256 fixture ID from name+version+network."""
    raw = f"{name}|{version}|{network}"
    return hashlib.sha256(raw.encode()).hexdigest()


def compute_checksum(data: dict[str, Any]) -> str:
    """Compute deterministic SHA256 checksum of sorted JSON."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class FixtureManifest:
    fixture_id: str
    name: str
    version: str
    network: str
    created_at: str
    source_summary: str
    source_urls: list[str]
    ledger_min: int
    ledger_max: int
    account_count: int
    transaction_count: int
    amm_count: int
    orderbook_count: int
    mpt_snapshot_count: int
    checksum: str
    limitations: list[str] = field(default_factory=list)


def load_manifest(path: Path) -> FixtureManifest:
    """Load FixtureManifest from path/manifest.json."""
    manifest_file = path / "manifest.json"
    if not manifest_file.exists():
        raise FixtureMissingError(f"manifest.json not found in {path}")
    try:
        data: dict[str, Any] = json.loads(manifest_file.read_text())
    except Exception as exc:
        raise FixtureMissingError(f"Failed to parse manifest.json: {exc}") from exc

    name = data.get("name", "")
    version = data.get("version", "")
    network = data.get("network", "unknown")
    fixture_id = compute_fixture_id(name, version, network)
    checksum = compute_checksum(data)

    return FixtureManifest(
        fixture_id=fixture_id,
        name=name,
        version=version,
        network=network,
        created_at=data.get("created_at", ""),
        source_summary=data.get("source_summary", ""),
        source_urls=data.get("source_urls", []),
        ledger_min=data.get("ledger_min", 0),
        ledger_max=data.get("ledger_max", 0),
        account_count=data.get("account_count", 0),
        transaction_count=data.get("transaction_count", 0),
        amm_count=data.get("amm_count", 0),
        orderbook_count=data.get("orderbook_count", 0),
        mpt_snapshot_count=data.get("mpt_snapshot_count", 0),
        checksum=checksum,
        limitations=data.get("limitations", []),
    )
