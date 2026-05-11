from __future__ import annotations

from dashboard.lib.canonical_loader import load_production_snapshot
from dashboard.lib.governance_loader import load_governance_snapshot
from dashboard.lib.safety_loader import load_safety_snapshot


def test_production_loader_returns_compact_contract() -> None:
    payload = load_production_snapshot()
    for key in (
        "alpha_score",
        "risk_blocked",
        "risk_allowed",
        "paper_pnl_attribution",
        "signal_status",
        "artifact_availability",
        "raw_signal_artifact",
    ):
        assert key in payload


def test_governance_loader_keeps_phase53_to_56_contract() -> None:
    payload = load_governance_snapshot()
    assert "summary" in payload
    assert "lineage" in payload
    assert "phase56_plan" in payload
    assert len(payload["lineage"]) == 4


def test_safety_loader_contract_is_read_only_snapshot() -> None:
    payload = load_safety_snapshot()
    assert "overall_status" in payload
    assert "checks" in payload
    assert "artifacts" in payload
    assert "raw" in payload
    assert payload["overall_status"] in {"pass", "fail", "review"}
