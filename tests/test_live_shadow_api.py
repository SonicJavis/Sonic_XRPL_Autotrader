import json
from datetime import datetime, timedelta, timezone
from math import isfinite

import pytest
from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ShadowDecisionRecord
from app.main import create_app


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_live"] is True
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert body["is_advisory"] is True
    assert "xrpl_warning" in body


@pytest.fixture
def live_shadow_client():
    app = create_app()
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.commit()
    with TestClient(app) as client:
        yield client, app
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.commit()


def _add_decision(app, *, idx: int, regime: str = "STABLE_SHADOW") -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        session.add(
            ShadowDecisionRecord(
                token_id=idx,
                issuer=f"rIssuer{idx}",
                currency="USD",
                observed_at=now + timedelta(seconds=idx),
                ledger_index=100 + idx,
                requested_size=100.0,
                latency_path_probability=0.7,
                memory_adjusted_probability=0.6,
                effective_size=70.0,
                memory_adjusted_effective_size=60.0,
                uncertainty_adjusted_value=0.5,
                drift_adjusted_ev=-0.1 if regime == "EXECUTION_COLLAPSE" else 0.4,
                regime=regime,
                advisory_risk_level="CRITICAL" if regime == "EXECUTION_COLLAPSE" else "LOW",
                risk_flags_json=json.dumps(["EXECUTION_MEMORY_COLLAPSE"] if regime == "EXECUTION_COLLAPSE" else []),
                calibration_snapshot_json=json.dumps({"is_shadow": True, "is_executable": False}),
                is_shadow=True,
                is_executable=False,
            )
        )
        session.commit()


def test_live_shadow_api_empty_state_safe(live_shadow_client) -> None:
    client, _app = live_shadow_client

    decisions = client.get("/live/shadow/decisions")
    summary = client.get("/live/shadow/summary")

    assert decisions.status_code == 200
    assert summary.status_code == 200
    _assert_meta(decisions.json())
    _assert_meta(summary.json())
    assert decisions.json()["count"] == 0
    assert summary.json()["summary"]["sample_count"] == 0


def test_live_shadow_api_populated_state_returns_records(live_shadow_client) -> None:
    client, app = live_shadow_client
    _add_decision(app, idx=1)
    _add_decision(app, idx=2, regime="EXECUTION_COLLAPSE")

    body = client.get("/live/shadow/decisions").json()
    summary = client.get("/live/shadow/summary").json()

    _assert_meta(body)
    assert body["count"] == 2
    assert body["decisions"][0]["ledger_index"] == 102
    assert body["decisions"][0]["risk_flags"] == ["EXECUTION_MEMORY_COLLAPSE"]
    _assert_meta(summary)
    assert summary["summary"]["sample_count"] == 2
    assert summary["summary"]["regime_distribution"]["EXECUTION_COLLAPSE"] == 1
    assert summary["summary"]["risk_flag_counts"]["EXECUTION_MEMORY_COLLAPSE"] == 1


def test_live_shadow_api_limit_bounds(live_shadow_client) -> None:
    client, app = live_shadow_client
    _add_decision(app, idx=1)
    _add_decision(app, idx=2)

    low = client.get("/live/shadow/decisions?limit=0").json()
    high = client.get("/live/shadow/summary?limit=999999").json()

    assert low["limit"] == 1
    assert low["count"] == 1
    assert high["limit"] == 5000


def test_live_shadow_api_outputs_are_finite(live_shadow_client) -> None:
    client, app = live_shadow_client
    _add_decision(app, idx=1)

    body = client.get("/live/shadow/decisions").json()
    row = body["decisions"][0]

    for key in (
        "requested_size",
        "latency_path_probability",
        "memory_adjusted_probability",
        "effective_size",
        "memory_adjusted_effective_size",
        "uncertainty_adjusted_value",
        "drift_adjusted_ev",
    ):
        assert isfinite(float(row[key]))
