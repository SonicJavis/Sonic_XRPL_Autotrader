"""Phase ledger checker — verifies phase evidence in docs."""

from __future__ import annotations

from pathlib import Path

REQUIRED_PHASE_DOCS = {
    "PHASE30": "docs/PHASE30_RECONCILIATION.md",
    "PHASE42": "docs/PHASE42_BACKTEST_DATASETS.md",
    "PHASE43": "docs/PHASE43_DATASET_STRATEGY_TOURNAMENT.md",
    "PHASE44": "docs/PHASE44_WALK_FORWARD_REPLAY.md",
}

PHASE_LEDGER = "docs/PHASE_LEDGER.md"


def check_phase_docs(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check that expected phase docs exist."""
    results = []
    for phase, path in REQUIRED_PHASE_DOCS.items():
        full = repo_root / path
        exists = full.exists()
        results.append((
            phase,
            exists,
            f"OK: {path}" if exists else f"MISSING: {path}",
        ))

    # Check the new V2 PHASE_LEDGER
    ledger = repo_root / PHASE_LEDGER
    results.append((
        "PHASE_LEDGER",
        ledger.exists(),
        f"OK: {PHASE_LEDGER}" if ledger.exists() else f"MISSING: {PHASE_LEDGER}",
    ))

    # Check Phase 45 entry in PHASE_LEDGER
    if ledger.exists():
        content = ledger.read_text()
        has_45 = "Phase 45" in content or "PHASE45" in content
        results.append((
            "Phase45_in_ledger",
            has_45,
            "Phase 45 entry found in PHASE_LEDGER.md"
            if has_45
            else "Phase 45 entry MISSING from PHASE_LEDGER.md",
        ))

    return results
