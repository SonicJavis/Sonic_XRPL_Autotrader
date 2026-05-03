"""Market Snapshot Builder — Phase 47.

Orchestrates all snapshot sections from Phase 46 fixture providers.

Rules:
- No live network calls.
- No transaction submission.
- No mutation.
- Deterministic output.
- Fail closed on invalid fixture manifest (in strict mode).
- Report limitations instead of inventing data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sonic_xrpl.market.manifest import build_snapshot_manifest, compute_source_hash
from sonic_xrpl.market.models import (
    AssetSnapshot,
    AssetType,
    MarketSnapshot,
)
from sonic_xrpl.market.amm_snapshot import build_amm_snapshot
from sonic_xrpl.market.orderbook_snapshot import build_orderbook_snapshot
from sonic_xrpl.market.account_context import build_account_context
from sonic_xrpl.market.trustline_context import build_trustline_contexts
from sonic_xrpl.market.mpt_snapshot import build_mpt_snapshot
from sonic_xrpl.market.metadata_signals import build_signals_from_fixture_metadata
from sonic_xrpl.market.quality import score_snapshot
from sonic_xrpl.market.errors import FixtureHealthError, SnapshotBuildError
from sonic_xrpl.protocol.capability_matrix import (
    CAPABILITY_MATRIX,
    is_capability_available,
)
from sonic_xrpl.protocol.amendments import AmendmentStatus
from sonic_xrpl.providers.fixture_store import FixtureStore
from sonic_xrpl.providers.errors import FixtureMissingError


_BUILDER_VERSION = "2.0.0-phase47"


def _asset_type_from_key(key: str) -> AssetType:
    if key == "XRP":
        return AssetType.XRP
    if ":" in key:
        return AssetType.IOU
    return AssetType.UNKNOWN


def _build_asset_from_key(key: str) -> AssetSnapshot:
    """Build an AssetSnapshot from an asset key string."""
    a_type = _asset_type_from_key(key)
    issuer: str | None = None
    currency: str | None = None
    risk_flags: list[str] = []
    limitations: list[str] = []
    cap_req: list[str] = []

    if a_type == AssetType.XRP:
        currency = "XRP"
    elif a_type == AssetType.IOU:
        parts = key.split(":", 1)
        currency = parts[0]
        issuer = parts[1] if len(parts) > 1 else None
        cap_req = []
        if is_capability_available("Clawback"):
            risk_flags.append("clawback_possible")
        if is_capability_available("DeepFreeze"):
            risk_flags.append("deep_freeze_possible")
    else:
        limitations.append(f"unknown asset type for key: {key}")

    return AssetSnapshot(
        asset_key=key,
        asset_type=a_type,
        issuer=issuer,
        currency=currency,
        mpt_id=None,
        capability_requirements=cap_req,
        risk_flags=risk_flags,
        limitations=limitations,
    )


def _collect_capabilities() -> dict[str, bool]:
    """Return all known capabilities with their enabled status."""
    return {
        name: (cap.status == AmendmentStatus.ENABLED)
        for name, cap in CAPABILITY_MATRIX.items()
    }


def build_market_snapshot(
    fixture_path: Path | str,
    *,
    ledger_index: int | None = None,
    accounts: list[str] | None = None,
    include_metadata: bool = True,
    include_mpt: bool = True,
    strict: bool = False,
) -> MarketSnapshot:
    """Build a complete MarketSnapshot from fixture data.

    Args:
        fixture_path: Path to the fixture directory.
        ledger_index: Explicit ledger index to snapshot. If None, uses latest.
        accounts: List of account IDs to include context for.
        include_metadata: Whether to parse metadata signals.
        include_mpt: Whether to include MPT holder context.
        strict: If True, raise FixtureHealthError on health failures.

    Returns:
        MarketSnapshot — immutable, deterministic.

    Raises:
        SnapshotBuildError: If mandatory fixture data is missing or corrupt.
        FixtureHealthError: If strict=True and fixture health fails.
    """
    fixture_path = Path(fixture_path)
    store = FixtureStore(fixture_path)
    accounts = accounts or []
    limitations: list[str] = []
    fixture_warnings: list[str] = []

    # ── 1. Load and validate manifest ────────────────────────────────────────
    manifest_valid = False
    fixture_id = "unknown"
    network = "unknown"
    try:
        manifest = store.load_manifest()
        manifest_valid = True
        fixture_id = manifest.fixture_id
        network = manifest.network
        limitations.extend(manifest.limitations)
    except (FixtureMissingError, Exception) as exc:
        msg = f"Failed to load fixture manifest: {exc}"
        limitations.append(msg)
        fixture_warnings.append(msg)
        if strict:
            raise FixtureHealthError(msg) from exc

    # ── 2. Health check ───────────────────────────────────────────────────────
    health = store.validate_health()
    if not health.get("ok"):
        for issue in health.get("issues", []):
            fixture_warnings.append(issue)
        if strict:
            raise FixtureHealthError(f"Fixture health check failed: {health.get('issues')}")

    # ── 3. Determine ledger index ─────────────────────────────────────────────
    resolved_ledger_index = ledger_index
    if resolved_ledger_index is None:
        try:
            latest = store.load_latest_ledger()
            resolved_ledger_index = latest.get("ledger", {}).get("ledger_index", 0)
            if not resolved_ledger_index:
                resolved_ledger_index = latest.get("ledger_index", 0)
        except Exception:
            if manifest_valid:
                resolved_ledger_index = manifest.ledger_max
            else:
                resolved_ledger_index = 0
    resolved_ledger_index = int(resolved_ledger_index or 0)

    # ── 4. Build AMM snapshots ────────────────────────────────────────────────
    amm_snapshots = []
    has_amm_data = False
    amm_dir = fixture_path / "amm"
    if amm_dir.exists():
        for f in sorted(amm_dir.glob("*.json")):
            try:
                raw = json.loads(f.read_text())
                snap = build_amm_snapshot(raw, resolved_ledger_index)
                amm_snapshots.append(snap)
                has_amm_data = True
            except Exception as exc:
                fixture_warnings.append(f"AMM fixture {f.name} failed: {exc}")

    # ── 5. Build orderbook snapshots ──────────────────────────────────────────
    orderbook_snapshots = []
    has_orderbook_data = False
    ob_dir = fixture_path / "orderbooks"
    if ob_dir.exists():
        for f in sorted(ob_dir.glob("*.json")):
            try:
                raw = json.loads(f.read_text())
                snap = build_orderbook_snapshot(raw, resolved_ledger_index)
                orderbook_snapshots.append(snap)
                has_orderbook_data = True
            except Exception as exc:
                fixture_warnings.append(f"Orderbook fixture {f.name} failed: {exc}")

    # ── 6. Build account contexts ─────────────────────────────────────────────
    account_contexts = []
    has_account_data = False
    for acct_id in accounts:
        try:
            raw = store.load_account_info(acct_id)
            ctx = build_account_context(raw, resolved_ledger_index)
            account_contexts.append(ctx)
            has_account_data = True
        except FixtureMissingError:
            limitations.append(f"account_info fixture not found for: {acct_id}")
        except Exception as exc:
            fixture_warnings.append(f"account_info {acct_id} failed: {exc}")

    if not accounts:
        # Try loading all available accounts
        accounts_dir = fixture_path / "accounts"
        if accounts_dir.exists():
            for f in sorted(accounts_dir.glob("*.json")):
                try:
                    raw = json.loads(f.read_text())
                    ctx = build_account_context(raw, resolved_ledger_index)
                    account_contexts.append(ctx)
                    has_account_data = True
                except Exception as exc:
                    fixture_warnings.append(f"account {f.name} failed: {exc}")

    # ── 7. Build trustline contexts ───────────────────────────────────────────
    trustline_contexts = []
    lines_dir = fixture_path / "account_lines"
    if lines_dir.exists():
        for f in sorted(lines_dir.glob("*_lines.json")):
            try:
                raw = json.loads(f.read_text())
                ctxs = build_trustline_contexts(raw)
                trustline_contexts.extend(ctxs)
            except Exception as exc:
                fixture_warnings.append(f"account_lines {f.name} failed: {exc}")

    # ── 8. Build MPT snapshots ────────────────────────────────────────────────
    mpt_snapshots = []
    has_mpt_data = False
    if include_mpt:
        mpt_dir = fixture_path / "mpt"
        if mpt_dir.exists():
            for f in sorted(mpt_dir.glob("*.json")):
                try:
                    raw = json.loads(f.read_text())
                    snap = build_mpt_snapshot(raw)
                    mpt_snapshots.append(snap)
                    has_mpt_data = True
                except Exception as exc:
                    fixture_warnings.append(f"MPT fixture {f.name} failed: {exc}")

    # ── 9. Metadata signals ───────────────────────────────────────────────────
    metadata_signals_list = []
    has_metadata = False
    metadata_sufficient_truth = True
    if include_metadata:
        metadata_dir = fixture_path / "metadata"
        signals, meta_warnings = build_signals_from_fixture_metadata(metadata_dir)
        metadata_signals_list = signals
        fixture_warnings.extend(meta_warnings)
        if signals:
            has_metadata = True
            # Check if any signal lacks sufficient truth
            for sig in signals:
                if "insufficient_truth" in sig.signal_flags:
                    metadata_sufficient_truth = False
                    break

    # ── 10. Collect assets from all data sources ──────────────────────────────
    asset_keys: set[str] = set()
    for amm in amm_snapshots:
        asset_keys.add(amm.asset_a)
        asset_keys.add(amm.asset_b)
    for ob in orderbook_snapshots:
        asset_keys.add(str(ob.taker_gets))
        asset_keys.add(str(ob.taker_pays))
    for tl in trustline_contexts:
        asset_keys.add(f"{tl.currency}:{tl.issuer}")

    asset_snapshots = [_build_asset_from_key(k) for k in sorted(asset_keys)]

    # ── 11. Capabilities ──────────────────────────────────────────────────────
    capabilities = _collect_capabilities()
    capability_warnings: list[str] = []
    if not is_capability_available("AMM") and has_amm_data:
        capability_warnings.append("AMM data present in fixture but AMM amendment is not ENABLED")

    # ── 12. Quality scoring ───────────────────────────────────────────────────
    quality = score_snapshot(
        manifest_valid=manifest_valid,
        has_amm_data=has_amm_data,
        amm_requested=True,
        has_orderbook_data=has_orderbook_data,
        has_metadata=has_metadata,
        metadata_sufficient_truth=metadata_sufficient_truth,
        has_mpt_data=has_mpt_data,
        mpt_requested=include_mpt,
        has_account_data=has_account_data,
        account_requested=bool(accounts),
        capability_warnings=capability_warnings,
        fixture_warnings=fixture_warnings,
    )

    # ── 13. Compute source hash ───────────────────────────────────────────────
    source_data = {
        "fixture_id": fixture_id,
        "ledger_index": resolved_ledger_index,
        "amm_count": len(amm_snapshots),
        "orderbook_count": len(orderbook_snapshots),
        "account_count": len(account_contexts),
        "trustline_count": len(trustline_contexts),
        "mpt_count": len(mpt_snapshots),
        "metadata_signal_count": len(metadata_signals_list),
    }
    source_hash = compute_source_hash(source_data)
    snapshot_id = compute_source_hash({
        "fixture_id": fixture_id,
        "ledger_index": resolved_ledger_index,
        "source_hash": source_hash,
    })[:32]

    created_at = datetime.now(timezone.utc).isoformat()

    return MarketSnapshot(
        snapshot_id=snapshot_id,
        created_at=created_at,
        fixture_id=fixture_id,
        ledger_index=resolved_ledger_index,
        network=network,
        assets=asset_snapshots,
        amms=amm_snapshots,
        orderbooks=orderbook_snapshots,
        accounts=account_contexts,
        trustlines=trustline_contexts,
        mpt_holders=mpt_snapshots,
        metadata_signals=metadata_signals_list,
        capabilities=capabilities,
        quality=quality,
        limitations=limitations,
        source_hash=source_hash,
    )
