import json
from collections.abc import Iterator
from datetime import datetime, timezone
from math import isfinite

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ExecutionRecord, MarketSnapshot, Signal, WatchedToken, XRPLOrderbookSnapshot
from app.main import create_app


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_advisory"] is True
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert "xrpl_warning" in body


def _assert_no_invalid_numbers(value: object) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_invalid_numbers(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_invalid_numbers(child)
    elif isinstance(value, float):
        assert isfinite(value)


def _clear_shadow_tables(app: FastAPI) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ExecutionRecord))
        session.exec(delete(XRPLOrderbookSnapshot))
        session.exec(delete(MarketSnapshot))
        session.exec(delete(Signal))
        session.exec(delete(WatchedToken))
        session.commit()


@pytest.fixture
def time_model_client() -> Iterator[tuple[TestClient, FastAPI]]:
    app = create_app()
    _clear_shadow_tables(app)
    with TestClient(app) as client:
        yield client, app
    _clear_shadow_tables(app)


def _add_shadow_rows(app: FastAPI, *, count: int = 1) -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rTimeModel", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)
        assert token.id is not None

        signal = Signal(
            strategy_name="time-model-shadow",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=100.0,
            reason="time model api test",
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

        rows = []
        for idx in range(count):
            rows.append(
                ExecutionRecord(
                    token_id=token.id,
                    signal_id=signal.id,
                    snapshot_id=snapshot.id,
                    side="BUY",
                    requested_size=100.0,
                    filled_size=80.0,
                    fill_status="PARTIAL",
                    avg_fill_price=1.02,
                    snapshot_time=now,
                    signal_time=now,
                    execution_time=now,
                    ledger_index_snapshot=100 + idx,
                    ledger_index_signal=100 + idx,
                    ledger_index_execution=102 + idx,
                    ledger_index_inclusion=102 + idx,
                    execution_details_json=json.dumps(
                        {
                            "shadow": True,
                            "predicted_fill_probability": 0.8,
                            "observed_fill_ratio": 0.4,
                            "observed_possible_fill": 40.0,
                            "snapshot_derived_liquidity": 100.0,
                            "snapshot_price": 1.0,
                            "execution_price": 1.04,
                            "path_complexity": 2,
                            "competition_penalty": 0.1,
                            "slippage_estimate": 0.02,
                        }
                    ),
                )
            )
        session.add_all(rows)
        session.commit()


def test_time_model_endpoint_empty_state(time_model_client: tuple[TestClient, FastAPI]) -> None:
    client, _app = time_model_client

    res = client.get("/calibration/shadow/xrpl/time-model")

    assert res.status_code == 200
    body = res.json()
    _assert_meta(body)
    assert body["sample_count"] == 0
    assert body["latency_distribution"] == []
    assert body["drift_distribution"] == []
    assert body["samples"] == []


def test_time_model_endpoint_populated_state(time_model_client: tuple[TestClient, FastAPI]) -> None:
    client, app = time_model_client
    _add_shadow_rows(app, count=1)

    res = client.get("/calibration/shadow/xrpl/time-model")

    assert res.status_code == 200
    body = res.json()
    _assert_meta(body)
    assert body["sample_count"] > 0
    assert "latency_distribution" in body
    assert "drift_distribution" in body
    for key in ("path_complexity_stats", "decay_stats", "fill_probability_stats", "drift_adjusted_ev_stats"):
        assert key in body
    row = body["samples"][0]
    assert "execution_id" in row
    assert "latency_seconds" in row
    assert "drift_adjusted_ev" in row


def test_time_model_endpoint_is_deterministic(time_model_client: tuple[TestClient, FastAPI]) -> None:
    client, app = time_model_client
    _add_shadow_rows(app, count=3)

    first = client.get("/calibration/shadow/xrpl/time-model").json()
    second = client.get("/calibration/shadow/xrpl/time-model").json()

    assert first == second


def test_time_model_endpoint_limit_is_bounded(time_model_client: tuple[TestClient, FastAPI]) -> None:
    client, app = time_model_client
    _add_shadow_rows(app, count=2)

    assert client.get("/calibration/shadow/xrpl/time-model?limit=0").json()["sample_count"] == 1
    assert client.get("/calibration/shadow/xrpl/time-model?limit=-100").json()["sample_count"] == 1

    _clear_shadow_tables(app)
    _add_shadow_rows(app, count=5001)
    res = client.get("/calibration/shadow/xrpl/time-model?limit=999999")

    assert res.status_code == 200
    assert res.json()["sample_count"] == 5000


def test_time_model_endpoint_numbers_are_finite_and_bounded(time_model_client: tuple[TestClient, FastAPI]) -> None:
    client, app = time_model_client
    _add_shadow_rows(app, count=1)

    body = client.get("/calibration/shadow/xrpl/time-model").json()

    _assert_no_invalid_numbers(body)
    for probability in [row["effective_fill_probability"] for row in body["samples"]]:
        assert 0.0 <= probability <= 1.0
    fill_stats = body["fill_probability_stats"]
    assert 0.0 <= fill_stats["min"] <= 1.0
    assert 0.0 <= fill_stats["max"] <= 1.0
    assert 0.0 <= fill_stats["avg"] <= 1.0
