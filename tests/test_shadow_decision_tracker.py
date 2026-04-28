import json
from datetime import datetime, timezone
from math import isfinite

from app.db.models import ShadowDecisionRecord
from app.feedback.shadow_decision_tracker import ShadowDecisionTracker


def _record(**overrides) -> ShadowDecisionRecord:
    values = {
        "token_id": 1,
        "issuer": "rIssuer",
        "currency": "USD",
        "observed_at": datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        "ledger_index": 100,
        "requested_size": 100.0,
        "latency_path_probability": 0.6,
        "memory_adjusted_probability": 0.5,
        "effective_size": 60.0,
        "memory_adjusted_effective_size": 50.0,
        "uncertainty_adjusted_value": 0.4,
        "drift_adjusted_ev": 0.3,
        "regime": "STABLE_SHADOW",
        "advisory_risk_level": "LOW",
        "risk_flags_json": "[]",
        "calibration_snapshot_json": "{}",
        "is_shadow": True,
        "is_executable": False,
    }
    values.update(overrides)
    return ShadowDecisionRecord(**values)


def test_tracker_empty_state_safe() -> None:
    summary = ShadowDecisionTracker().summarize([])

    assert summary.sample_count == 0
    assert summary.regime_distribution == {}
    assert summary.risk_flag_counts == {}
    assert summary.blocked_rate == 0.0


def test_tracker_counts_regimes_flags_and_blocked_rate() -> None:
    summary = ShadowDecisionTracker().summarize(
        [
            _record(regime="STABLE_SHADOW", risk_flags_json=json.dumps(["A"])),
            _record(
                regime="EXECUTION_COLLAPSE",
                advisory_risk_level="CRITICAL",
                memory_adjusted_probability=0.0,
                memory_adjusted_effective_size=0.0,
                drift_adjusted_ev=-1.0,
                risk_flags_json=json.dumps(["A", "B"]),
            ),
        ]
    )

    assert summary.sample_count == 2
    assert summary.regime_distribution == {"EXECUTION_COLLAPSE": 1, "STABLE_SHADOW": 1}
    assert summary.risk_flag_counts == {"A": 2, "B": 1}
    assert summary.blocked_rate == 0.5
    assert summary.over_risk_rate == 1.0
    assert isfinite(summary.avg_memory_adjusted_probability)
