from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dashboard.lib.artifact_formatting import safe_float, safe_int


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_production_snapshot() -> dict[str, Any]:
    market = _load_json(REPORTS / "phase47" / "market_snapshot_042b75dbd2a2_20260503T121647Z.json")
    readiness = _load_json(REPORTS / "phase53" / "calibration_readiness.json")
    outcomes = _load_json(REPORTS / "phase52" / "outcome_corpus_quality.json")
    proposal = _load_json(REPORTS / "phase54" / "calibration_proposal_pack.json")

    readiness_result = readiness.get("readiness_result", {}) if isinstance(readiness, dict) else {}

    alpha_score = safe_float((market or {}).get("quality", {}).get("score") if isinstance(market, dict) else None)
    blocked = safe_int(readiness_result.get("blockers") and len(readiness_result.get("blockers", [])))
    allowed = safe_int(readiness_result.get("status") == "READY_FOR_HUMAN_REVIEW")
    paper_pnl = None
    if isinstance(outcomes, dict):
        complete = safe_int(outcomes.get("complete_cases"))
        total = safe_int(outcomes.get("total_cases"))
        if complete is not None and total is not None and total > 0:
            paper_pnl = round(complete / total, 4)

    return {
        "alpha_score": alpha_score,
        "risk_blocked": blocked,
        "risk_allowed": allowed,
        "paper_pnl_attribution": paper_pnl,
        "signal_status": readiness_result.get("status") if readiness_result else None,
        "signal_lineage_note": (
            "Phase 49-50 signal review lineage detected from immutable artifacts."
            if readiness_result
            else "No source-backed signal review artifact found."
        ),
        "artifact_availability": {
            "signal_artifact": readiness is not None,
            "outcome_artifact": outcomes is not None,
            "calibration_artifact": proposal is not None,
            "source_type": "paper-only" if readiness is not None else "unknown",
        },
        "raw_signal_artifact": readiness,
        "raw_signal_source_path": str(REPORTS / "phase53" / "calibration_readiness.json"),
    }
