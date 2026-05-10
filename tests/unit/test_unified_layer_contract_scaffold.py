from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_unified_architecture_target_doc_exists() -> None:
    doc = REPO_ROOT / "docs" / "UNIFIED_ARCHITECTURE_TARGET.md"
    assert doc.exists(), "Unified architecture target doc is required"


def test_unified_architecture_target_has_required_contract_sections() -> None:
    doc = REPO_ROOT / "docs" / "UNIFIED_ARCHITECTURE_TARGET.md"
    text = doc.read_text(encoding="utf-8")

    required_sections = [
        "## Architecture Diagram",
        "## Post-Migration File Organization",
        "### Safety Layer Interface",
        "### Market Data Freshness Contract",
        "### Execution Intent -> Result Reconciliation Contract",
        "### Governance Non-Mutation Contract",
        "## Migration Steps (3 Surfaces -> 1 Surface)",
        "## Scaffolding Test Plan (No Behavior Change)",
    ]
    for section in required_sections:
        assert section in text


def test_unified_scaffold_canonical_module_boundaries_exist() -> None:
    src_root = REPO_ROOT / "src" / "sonic_xrpl"
    required_paths = [
        src_root / "core",
        src_root / "providers",
        src_root / "signals",
        src_root / "execution",
        src_root / "outcomes",
        src_root / "calibration_review",
        src_root / "calibration_proposal",
        src_root / "calibration_approval",
        src_root / "calibration_implementation_plan",
    ]
    for path in required_paths:
        assert path.exists(), f"Missing required canonical boundary path: {path}"
