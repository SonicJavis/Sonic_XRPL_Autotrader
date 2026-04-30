from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient

from app.db.models import ShadowValidationRecord, WatchedToken, XRPLOrderbookSnapshot
from app.main import create_app


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)


def test_validation_intents_empty_state_safe() -> None:
    client = TestClient(create_app())

    body = client.get("/validation/intents").json()
    summary = client.get("/validation/intents/summary").json()

    assert body["count"] >= 0
    assert "intents" in body
    assert summary["summary"]["is_executable"] is False
    _assert_meta(body)
    _assert_meta(summary)
    assert _finite_json(body)
    assert _finite_json(summary)


def test_validation_intents_populated_contract_and_detail() -> None:
    app = create_app()
    token_id = _seed(app)
    client = TestClient(app)

    body = client.get("/validation/intents?limit=100").json()

    matching = [row for row in body["intents"] if row["token_id"] == str(token_id)]
    assert matching
    intent = matching[0]
    assert intent["schema_version"] == "1.0"
    assert intent["source_recommendation_id"].startswith("rec_")
    assert intent["action"] in {"buy", "sell", "avoid"}
    assert intent["xrpl_context"]["validated"] is True
    assert "execution_estimates" in intent
    assert "execution_feasibility" in intent
    assert "fill_model" in intent
    assert "pathfinding" in intent
    assert 0.0 <= intent["execution_estimates"]["expected_fill_ratio"] <= 0.95
    feasibility = intent["execution_feasibility"]
    assert feasibility["schema_version"] == "1.0"
    assert feasibility["decision"] in {"feasible", "marginal", "avoid"}
    assert feasibility["route_type"] in {"direct", "xrp_bridge", "multi_hop", "none"}
    assert 0.0 <= feasibility["execution_feasibility_score"] <= 1.0
    assert feasibility["is_executable"] is False
    assert intent["is_executable"] is False

    detail = client.get(f"/validation/intents/{intent['intent_id']}").json()
    assert detail["intent"] == intent
    _assert_meta(detail)


def test_validation_intents_are_stable_and_limit_bounded() -> None:
    app = create_app()
    _seed(app)
    client = TestClient(app)

    first = client.get("/validation/intents?limit=999999").json()
    second = client.get("/validation/intents?limit=999999").json()
    low = client.get("/validation/intents?limit=0").json()
    summary = client.get("/validation/intents/summary").json()

    assert first == second
    assert first["limit"] == 5000
    assert low["limit"] == 1
    assert "avg_liquidity_score" in summary["summary"]
    assert _finite_json(first)
    assert _finite_json(summary)


def test_validation_intents_read_feasibility_idempotent_without_mutation() -> None:
    app = create_app()
    _seed(app)
    client = TestClient(app)

    first = client.get("/validation/intents?limit=100").json()
    second = client.get("/validation/intents?limit=100").json()

    assert first == second
    assert all("execution_feasibility" in row for row in first["intents"])


def _seed(app) -> int:
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rIntentIssuer", currency="USD")
        session.add(token)
        session.commit()
        session.refresh(token)
        assert token.id is not None
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token.id,
                ledger_index=700,
                best_bid=0.98,
                best_ask=1.02,
                bid_depth_xrp=160.0,
                ask_depth_xrp=95.0,
                spread_pct=4.0,
                observed_at=BASE,
            )
        )
        for idx in range(3):
            session.add(
                ShadowValidationRecord(
                    decision_id=10_000 + idx,
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
        return int(token.id)


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
