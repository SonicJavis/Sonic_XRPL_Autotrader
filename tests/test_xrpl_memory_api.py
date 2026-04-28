import json
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ExecutionRecord, MarketSnapshot, Signal, WatchedToken
from app.main import create_app


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_advisory"] is True
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert body["auto_apply"] is False
    assert body["requires_manual_review"] is True
    assert "xrpl_warning" in body


def _clear_tables(app: FastAPI) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ExecutionRecord))
        session.exec(delete(MarketSnapshot))
        session.exec(delete(Signal))
        session.exec(delete(WatchedToken))
        session.commit()


@pytest.fixture
def memory_client() -> Iterator[tuple[TestClient, FastAPI]]:
    app = create_app()
    _clear_tables(app)
    with TestClient(app) as client:
        yield client, app
    _clear_tables(app)


def _add_shadow_execution(
    app: FastAPI,
    *,
    issuer: str,
    currency: str,
    observed_possible_fill: float,
    snapshot_derived_liquidity: float,
    path_complexity: int = 1,
    route_instability: float = 0.1,
    competition_penalty: float = 0.0,
    ledger_gap: int = 1,
    execution_price: float = 1.0,
) -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer=issuer, currency=currency, is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)
        assert token.id is not None

        signal = Signal(
            strategy_name="memory-shadow",
            issuer=issuer,
            currency=currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=100.0,
            reason="memory api",
            created_at=now,
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)
        assert signal.id is not None

        snapshot = MarketSnapshot(
            token_id=token.id,
            price_xrp=1.0,
            liquidity_xrp=snapshot_derived_liquidity,
            liquidity_bid_xrp=snapshot_derived_liquidity / 2.0,
            liquidity_ask_xrp=snapshot_derived_liquidity / 2.0,
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

        session.add(
            ExecutionRecord(
                token_id=token.id,
                signal_id=signal.id,
                snapshot_id=snapshot.id,
                side="BUY",
                requested_size=100.0,
                filled_size=80.0,
                fill_status="PARTIAL",
                avg_fill_price=execution_price,
                snapshot_time=now,
                signal_time=now,
                execution_time=now,
                ledger_index_snapshot=100,
                ledger_index_signal=100,
                ledger_index_execution=100 + ledger_gap,
                ledger_index_inclusion=100 + ledger_gap,
                execution_details_json=json.dumps(
                    {
                        "shadow": True,
                        "predicted_fill_probability": 0.8,
                        "observed_possible_fill": observed_possible_fill,
                        "snapshot_derived_liquidity": snapshot_derived_liquidity,
                        "snapshot_price": 1.0,
                        "execution_price": execution_price,
                        "path_complexity": path_complexity,
                        "route_instability": route_instability,
                        "competition_penalty": competition_penalty,
                        "slippage_estimate": 0.02,
                        "routes_seen": ["direct", "auto_bridge"] if path_complexity > 1 else ["direct"],
                    }
                ),
            )
        )
        session.commit()


def test_memory_and_regime_api_empty_state_safe(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, _app = memory_client

    for path in ("/calibration/shadow/xrpl/memory", "/calibration/shadow/xrpl/regime"):
        res = client.get(path)
        assert res.status_code == 200
        body = res.json()
        _assert_meta(body)
        assert body["sample_count"] == 0


def test_memory_api_populated_state_valid(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, app = memory_client
    _add_shadow_execution(
        app,
        issuer="rIssuerA",
        currency="USD",
        observed_possible_fill=10.0,
        snapshot_derived_liquidity=100.0,
        path_complexity=2,
    )

    body = client.get("/calibration/shadow/xrpl/memory").json()

    _assert_meta(body)
    assert body["sample_count"] == 1
    assert body["global"]["sample_count"] == 1
    assert body["tokens"][0]["scope"] == "token"
    assert body["issuers"][0]["key"] == "rIssuerA"
    assert body["global"]["avg_phantom_penalty"] > 0.0


def test_regime_api_populated_state_valid(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, app = memory_client
    _add_shadow_execution(
        app,
        issuer="rIssuerRisk",
        currency="USD",
        observed_possible_fill=2.0,
        snapshot_derived_liquidity=100.0,
        path_complexity=3,
        route_instability=0.8,
        competition_penalty=0.8,
        ledger_gap=4,
        execution_price=1.2,
    )

    body = client.get("/calibration/shadow/xrpl/regime").json()

    _assert_meta(body)
    assert body["sample_count"] == 1
    assert body["global"]["regime"]["regime"] in {
        "LIQUIDITY_ILLUSION",
        "ROUTE_UNSTABLE",
        "COMPETITION_SPIKE",
        "LATENCY_DOMINATED",
        "DRIFT_RISK",
        "EXECUTION_COLLAPSE",
    }
    assert body["tokens"][0]["regime"]["is_shadow"] is True
    assert body["issuers"][0]["regime"]["is_executable"] is False


def test_memory_and_regime_api_are_deterministic(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, app = memory_client
    _add_shadow_execution(
        app,
        issuer="rIssuerStable",
        currency="USD",
        observed_possible_fill=70.0,
        snapshot_derived_liquidity=100.0,
    )

    assert client.get("/calibration/shadow/xrpl/memory").json() == client.get("/calibration/shadow/xrpl/memory").json()
    assert client.get("/calibration/shadow/xrpl/regime").json() == client.get("/calibration/shadow/xrpl/regime").json()


def test_memory_api_limit_bounds_and_deterministic_sorting(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, app = memory_client
    _add_shadow_execution(
        app,
        issuer="zIssuer",
        currency="USD",
        observed_possible_fill=50.0,
        snapshot_derived_liquidity=100.0,
    )
    _add_shadow_execution(
        app,
        issuer="aIssuer",
        currency="USD",
        observed_possible_fill=50.0,
        snapshot_derived_liquidity=100.0,
    )

    low_limit = client.get("/calibration/shadow/xrpl/memory?limit=0").json()
    high_limit = client.get("/calibration/shadow/xrpl/memory?limit=999999").json()

    assert low_limit["sample_count"] == 1
    token_keys = [int(row["key"]) for row in high_limit["tokens"]]
    issuer_keys = [row["key"] for row in high_limit["issuers"]]
    assert token_keys == sorted(token_keys)
    assert issuer_keys == sorted(issuer_keys)


def test_regime_api_limit_bounds_and_deterministic_sorting(memory_client: tuple[TestClient, FastAPI]) -> None:
    client, app = memory_client
    _add_shadow_execution(
        app,
        issuer="zIssuer",
        currency="USD",
        observed_possible_fill=50.0,
        snapshot_derived_liquidity=100.0,
    )
    _add_shadow_execution(
        app,
        issuer="aIssuer",
        currency="USD",
        observed_possible_fill=50.0,
        snapshot_derived_liquidity=100.0,
    )

    low_limit = client.get("/calibration/shadow/xrpl/regime?limit=-10").json()
    high_limit = client.get("/calibration/shadow/xrpl/regime?limit=999999").json()

    assert low_limit["sample_count"] == 1
    token_keys = [int(row["aggregate"]["key"]) for row in high_limit["tokens"]]
    issuer_keys = [row["aggregate"]["key"] for row in high_limit["issuers"]]
    assert token_keys == sorted(token_keys)
    assert issuer_keys == sorted(issuer_keys)
