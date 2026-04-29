from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient

from app.db.models import ShadowValidationRecord, WatchedToken, XRPLOrderbookSnapshot
from app.main import create_app


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)


def test_validation_simulations_empty_state_safe() -> None:
    client = TestClient(create_app())

    body = client.get("/validation/simulations").json()
    summary = client.get("/validation/simulations/summary").json()

    assert body["count"] >= 0
    assert "simulations" in body
    assert summary["summary"]["is_executable"] is False
    _assert_meta(body)
    _assert_meta(summary)
    assert _finite_json(body)


def test_validation_simulations_populated_contract_and_detail() -> None:
    app = create_app()
    _seed(app)
    client = TestClient(app)

    body = client.get("/validation/simulations?limit=100").json()

    assert body["count"] >= 1
    simulation = body["simulations"][0]
    assert simulation["schema_version"] == "1.0"
    assert simulation["simulation_id"].startswith("sim_")
    assert simulation["intent_id"].startswith("intent_")
    assert simulation["execution_status"] in {"full", "partial", "failed"}
    assert simulation["xrpl_execution_context"]["funded_liquidity_only"] is True
    assert 0.0 <= simulation["fill_ratio"] <= 1.0
    assert simulation["is_executable"] is False

    detail = client.get(f"/validation/simulations/{simulation['simulation_id']}").json()
    assert detail["simulation"] == simulation
    _assert_meta(detail)


def test_validation_simulations_are_stable_and_summary_bounded() -> None:
    app = create_app()
    _seed(app)
    client = TestClient(app)

    first = client.get("/validation/simulations?limit=999999").json()
    second = client.get("/validation/simulations?limit=999999").json()
    low = client.get("/validation/simulations?limit=0").json()
    summary = client.get("/validation/simulations/summary").json()

    assert first == second
    assert first["limit"] == 5000
    assert low["limit"] == 1
    assert 0.0 <= summary["summary"]["failure_rate"] <= 1.0
    assert 0.0 <= summary["summary"]["success_rate"] <= 1.0
    assert _finite_json(first)
    assert _finite_json(summary)


def _seed(app) -> None:
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rSimulationIssuer", currency="USD")
        session.add(token)
        session.commit()
        session.refresh(token)
        assert token.id is not None
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token.id,
                ledger_index=800,
                best_bid=0.98,
                best_ask=1.02,
                bid_depth_xrp=160.0,
                ask_depth_xrp=90.0,
                spread_pct=2.0,
                levels_json=[
                    {"side": "ask", "quality": 1.02, "price": 1.02, "available_size": 20.0, "funded": False},
                    {"side": "ask", "quality": 1.03, "price": 1.03, "available_size": 60.0, "funded": True},
                    {"side": "ask", "quality": 1.07, "price": 1.07, "available_size": 60.0, "funded": True},
                ],
                observed_at=BASE,
            )
        )
        for idx in range(3):
            session.add(
                ShadowValidationRecord(
                    decision_id=20_000 + idx,
                    token_id=token.id,
                    issuer=token.issuer,
                    predicted_regime="STABLE_SHADOW",
                    disagreement_score=0.35,
                    brier_score=0.30,
                    overconfidence_flag=True,
                    attribution="liquidity_illusion",
                    created_at=BASE + timedelta(seconds=idx),
                )
            )
        session.commit()


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert body["is_truth"] is False


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
