from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ShadowDecisionRecord
from app.main import create_app


def _client_with_record() -> TestClient:
    app = create_app()
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.add(
            ShadowDecisionRecord(
                token_id=1,
                issuer="rContract",
                currency="USD",
                observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
                ledger_index=100,
                requested_size=100.0,
                latency_path_probability=0.7,
                memory_adjusted_probability=0.6,
                effective_size=70.0,
                memory_adjusted_effective_size=60.0,
                uncertainty_adjusted_value=0.5,
                drift_adjusted_ev=0.4,
                regime="STABLE_SHADOW",
                advisory_risk_level="LOW",
                risk_flags_json="[]",
                calibration_snapshot_json="{}",
            )
        )
        session.commit()
    return TestClient(app)


def test_live_shadow_decisions_contract_is_frozen() -> None:
    body = _client_with_record().get("/live/shadow/decisions").json()

    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert isinstance(body["count"], int)
    assert isinstance(body["limit"], int)
    row = body["decisions"][0]
    expected = {
        "id": int,
        "token_id": int,
        "issuer": str,
        "currency": str,
        "observed_at": str,
        "ledger_index": int,
        "requested_size": float,
        "latency_path_probability": float,
        "memory_adjusted_probability": float,
        "effective_size": float,
        "memory_adjusted_effective_size": float,
        "uncertainty_adjusted_value": float,
        "drift_adjusted_ev": float,
        "regime": str,
        "advisory_risk_level": str,
        "risk_flags": list,
        "calibration_snapshot": dict,
        "is_shadow": bool,
        "is_executable": bool,
    }
    assert set(expected).issubset(row)
    for key, typ in expected.items():
        assert isinstance(row[key], typ)


def test_live_shadow_summary_contract_is_frozen() -> None:
    body = _client_with_record().get("/live/shadow/summary").json()

    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    summary = body["summary"]
    expected = {
        "sample_count": int,
        "avg_memory_adjusted_probability": float,
        "avg_effective_size": float,
        "avg_adjusted_ev": float,
        "avg_drift_adjusted_ev": float,
        "over_risk_rate": float,
        "blocked_rate": float,
        "regime_distribution": dict,
        "risk_flag_counts": dict,
    }
    assert set(expected).issubset(summary)
    for key, typ in expected.items():
        assert isinstance(summary[key], typ)
