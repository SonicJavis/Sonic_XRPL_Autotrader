import json
from datetime import datetime, timezone

from app.db.models import ShadowDecisionRecord
from app.feedback.shadow_decision_tracker import ShadowDecisionTracker


def _record(**overrides) -> ShadowDecisionRecord:
    values = {
        "token_id": 1,
        "observed_at": datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        "memory_adjusted_probability": 0.5,
        "memory_adjusted_effective_size": 10.0,
        "uncertainty_adjusted_value": 1.0,
        "drift_adjusted_ev": 1.0,
        "regime": "B",
        "advisory_risk_level": "LOW",
        "risk_flags_json": "[]",
    }
    values.update(overrides)
    return ShadowDecisionRecord(**values)


def test_tracker_dedupes_flags_and_sorts_outputs() -> None:
    summary = ShadowDecisionTracker().summarize(
        [
            _record(regime="B", risk_flags_json=json.dumps(["Z", "A", "A"])),
            _record(regime="A", risk_flags_json=json.dumps(["Z"])),
        ]
    )

    assert list(summary.regime_distribution) == ["A", "B"]
    assert list(summary.risk_flag_counts) == ["A", "Z"]
    assert summary.risk_flag_counts == {"A": 1, "Z": 2}


def test_tracker_ignores_malformed_flags() -> None:
    summary = ShadowDecisionTracker().summarize([_record(risk_flags_json="{bad")])

    assert summary.risk_flag_counts == {}


def test_tracker_rates_follow_shadow_rules() -> None:
    summary = ShadowDecisionTracker().summarize(
        [
            _record(memory_adjusted_probability=0.0),
            _record(memory_adjusted_effective_size=0.0),
            _record(drift_adjusted_ev=0.0),
            _record(advisory_risk_level="HIGH"),
            _record(risk_flags_json=json.dumps(["RISK"])),
        ]
    )

    assert summary.blocked_rate == 0.6
    assert summary.over_risk_rate == 0.4
