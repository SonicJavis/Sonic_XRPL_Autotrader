import json
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ExecutionRecord, MarketSnapshot, Signal, WatchedToken
from app.main import create_app


def _assert_feedback_meta(body: dict[str, object]) -> None:
    assert body["is_advisory"] is True
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert "xrpl_warning" in body


def _clear_feedback_tables(app: FastAPI) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ExecutionRecord))
        session.commit()


@pytest.fixture
def feedback_client() -> Iterator[tuple[TestClient, FastAPI]]:
    app = create_app()
    _clear_feedback_tables(app)
    with TestClient(app) as client:
        yield client, app
    _clear_feedback_tables(app)


def _add_shadow_executions(app: FastAPI, *, count: int = 1) -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rFeedback", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)
        assert token.id is not None

        signal = Signal(
            strategy_name="feedback-shadow",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=100.0,
            reason="feedback api smoke test",
            created_at=now,
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)
        assert signal.id is not None

        snapshot = MarketSnapshot(
            token_id=token.id,
            price_xrp=1.0,
            liquidity_xrp=500.0,
            liquidity_bid_xrp=250.0,
            liquidity_ask_xrp=250.0,
            spread_pct=2.0,
            best_bid=0.99,
            best_ask=1.01,
            bid_count=2,
            ask_count=2,
            created_at=now,
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        assert snapshot.id is not None

        details_json = json.dumps(
            {
                "shadow": True,
                "expected_profit": 20.0,
                "expected_loss": 10.0,
                "predicted_fill_probability": 0.8,
                "predicted_ev": 14.0,
                "observed_fill_ratio": 0.35,
                "observed_possible_fill": 35.0,
                "route_confidence": 0.4,
                "path_execution_risk": 0.6,
                "allow_trade": True,
            }
        )
        rows = [
            ExecutionRecord(
                token_id=token.id,
                signal_id=signal.id,
                snapshot_id=snapshot.id,
                side="BUY",
                requested_size=100.0,
                filled_size=80.0,
                fill_status="PARTIAL",
                snapshot_time=now,
                signal_time=now,
                execution_time=now,
                ledger_index_snapshot=100 + idx,
                ledger_index_signal=100 + idx,
                ledger_index_execution=102 + idx,
                ledger_index_inclusion=102 + idx,
                execution_details_json=details_json,
            )
            for idx in range(count)
        ]
        session.add_all(rows)
        session.commit()


def test_decision_quality_empty_state_returns_safe_metadata(feedback_client: tuple[TestClient, FastAPI]) -> None:
    client, _app = feedback_client

    res = client.get("/feedback/decision-quality")

    assert res.status_code == 200
    body = res.json()
    _assert_feedback_meta(body)
    assert body["sample_count"] == 0


def test_decision_quality_populated_shadow_execution_returns_metrics(
    feedback_client: tuple[TestClient, FastAPI],
) -> None:
    client, app = feedback_client
    _add_shadow_executions(app, count=1)

    res = client.get("/feedback/decision-quality")

    assert res.status_code == 200
    body = res.json()
    _assert_feedback_meta(body)
    assert body["sample_count"] > 0
    for key in (
        "avg_fill_error",
        "avg_ev_error",
        "overconfidence_rate",
        "avg_ledger_penalty",
        "avg_route_instability",
        "competition_proxy_rate",
    ):
        assert key in body


def test_decision_quality_limit_parameter_is_bounded_safely(feedback_client: tuple[TestClient, FastAPI]) -> None:
    client, app = feedback_client
    _add_shadow_executions(app, count=2)

    assert client.get("/feedback/decision-quality?limit=0").json()["sample_count"] == 1
    assert client.get("/feedback/decision-quality?limit=-100").json()["sample_count"] == 1

    _clear_feedback_tables(app)
    _add_shadow_executions(app, count=5001)
    res = client.get("/feedback/decision-quality?limit=999999")

    assert res.status_code == 200
    assert res.json()["sample_count"] == 5000
