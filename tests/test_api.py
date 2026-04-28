from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import select

from app.db.models import MarketSnapshot, Signal, WatchedToken
from app.execution.fill_simulator import simulate_entry_buy
from app.execution.pnl_attribution_engine import PnLAttributionEngine
from app.main import create_app


def test_health_endpoint_works() -> None:
    app = create_app()
    app.state.container.xrpl_client.health_check = lambda: {"ok": True, "validated_ledger_index": 1, "server_load_factor": 1}
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_token_and_list_tokens() -> None:
    app = create_app()
    client = TestClient(app)

    reg = client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    assert reg.status_code == 200
    assert reg.json()["ok"] is True

    listed = client.get("/tokens")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)


def test_market_orderbook_endpoint() -> None:
    app = create_app()
    app.state.container.xrpl_client.get_book_offers = lambda taker_gets, taker_pays: {
        "offers": [
            {"quality": 1.0, "taker_gets": 1000.0, "taker_pays": 1000.0},
            {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
            {"quality": 0.99, "taker_gets": 1000.0, "taker_pays": 990.0},
        ]
    }
    client = TestClient(app)

    client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    response = client.get("/market/orderbook")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_phase4_endpoints_after_pipeline_run() -> None:
    app = create_app()
    app.state.container.xrpl_client.get_book_offers = lambda taker_gets, taker_pays: {
        "offers": [
            {"quality": 0.99, "taker_gets": 990.0, "taker_pays": 1000.0},
            {"quality": 0.98, "taker_gets": 980.0, "taker_pays": 1000.0},
            {"quality": 0.97, "taker_gets": 970.0, "taker_pays": 1000.0},
            {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
            {"quality": 1.02, "taker_gets": 1000.0, "taker_pays": 1020.0},
            {"quality": 1.03, "taker_gets": 1000.0, "taker_pays": 1030.0},
        ]
    }
    client = TestClient(app)

    reg = client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    assert reg.status_code == 200
    run = client.post("/pipeline/run-once")
    assert run.status_code == 200

    alpha = client.get("/signals/alpha")
    assert alpha.status_code == 200
    assert isinstance(alpha.json(), list)

    depth = client.get("/market/depth")
    assert depth.status_code == 200
    assert "ok" in depth.json()

    history = client.get("/market/history")
    assert history.status_code == 200
    assert isinstance(history.json(), list)

    decisions = client.get("/risk/decisions")
    assert decisions.status_code == 200
    assert isinstance(decisions.json(), list)


def test_phase45_performance_endpoints() -> None:
    app = create_app()
    app.state.container.xrpl_client.get_book_offers = lambda taker_gets, taker_pays: {
        "offers": [
            {"quality": 0.99, "taker_gets": 990.0, "taker_pays": 1000.0},
            {"quality": 0.98, "taker_gets": 980.0, "taker_pays": 1000.0},
            {"quality": 0.97, "taker_gets": 970.0, "taker_pays": 1000.0},
            {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
            {"quality": 1.02, "taker_gets": 1000.0, "taker_pays": 1020.0},
            {"quality": 1.03, "taker_gets": 1000.0, "taker_pays": 1030.0},
        ]
    }
    client = TestClient(app)

    reg = client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    assert reg.status_code == 200
    run = client.post("/pipeline/run-once")
    assert run.status_code == 200

    summary = client.get("/performance/summary")
    assert summary.status_code == 200
    assert "win_rate" in summary.json()
    assert "fill_rate" in summary.json()

    trades = client.get("/performance/trades")
    assert trades.status_code == 200
    assert isinstance(trades.json(), list)

    breakdown = client.get("/performance/alpha-breakdown")
    assert breakdown.status_code == 200
    body = breakdown.json()
    assert "components" in body
    assert "manipulation_flags" in body


def test_strict_attribution_endpoints_available() -> None:
    app = create_app()
    client = TestClient(app)

    positions = client.get("/positions")
    assert positions.status_code == 200
    assert isinstance(positions.json(), list)

    realized = client.get("/pnl/realized")
    assert realized.status_code == 200
    assert "realized_pnl_xrp" in realized.json()
    assert "unrealized_pnl_xrp" not in realized.json()

    unrealized = client.get("/pnl/unrealized")
    assert unrealized.status_code == 200
    assert "positions" in unrealized.json()
    assert "realized_pnl_xrp" not in unrealized.json()

    failures = client.get("/failures")
    assert failures.status_code == 200
    assert isinstance(failures.json(), list)

    missing_execution = client.get("/execution/999999")
    assert missing_execution.status_code == 404

    quality = client.get("/execution/quality")
    assert quality.status_code == 200
    body = quality.json()
    assert "fill_efficiency" in body
    assert "avg_levels_consumed" in body
    assert "queue_impact_pct" in body
    assert "effective_vs_raw_liquidity" in body
    assert "avg_execution_latency_ms" in body
    assert "avg_snapshot_age_ms" in body
    assert "avg_snapshot_to_decision_ms" in body
    assert "avg_decision_to_submission_ms" in body
    assert "avg_submission_to_inclusion_ms" in body
    assert "avg_slippage_vs_top" in body
    assert "partial_fill_rate" in body
    assert "failure_rate_by_reason" in body

    latency = client.get("/execution/latency-summary")
    assert latency.status_code == 200
    assert "avg_total_execution_latency_ms" in latency.json()

    inclusion = client.get("/execution/inclusion-summary")
    assert inclusion.status_code == 200
    assert "inclusion_status_counts" in inclusion.json()

    slices_missing = client.get("/execution/ledger-slices/999999")
    assert slices_missing.status_code == 404


def test_replay_endpoint_exposes_replay_status() -> None:
    app = create_app()
    client = TestClient(app)

    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        sig = Signal(
            strategy_name="unit",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.9,
            risk_score=0.1,
            suggested_size_xrp=10.0,
            reason="unit",
        )
        session.add(sig)
        session.commit()
        session.refresh(sig)

        snap = MarketSnapshot(
            token_id=token.id,
            price_xrp=1.0,
            liquidity_xrp=1000.0,
            liquidity_bid_xrp=500.0,
            liquidity_ask_xrp=500.0,
            spread_pct=1.0,
            best_bid=0.99,
            best_ask=1.01,
            bid_count=2,
            ask_count=2,
        )
        session.add(snap)
        session.commit()
        session.refresh(snap)

        now = datetime.now(tz=timezone.utc)
        out = simulate_entry_buy(
            asks=[{"price": 1.01, "token_amount": 100.0, "xrp_value": 101.0}],
            best_bid=0.99,
            best_ask=1.01,
            requested_size_xrp=10.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )
        rec = PnLAttributionEngine().create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=snap.id,
            position_id=None,
            side="BUY",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=10,
            ledger_index_signal=11,
            ledger_index_execution=11,
            ledger_index_inclusion=12,
            inclusion_status="INCLUDED",
            min_ledger_delay=1,
            max_ledger_delay=3,
        )

    replay = client.get(f"/execution/replay/{rec.id}")
    assert replay.status_code == 200
    assert replay.json()["status"] in {"REPLAY_OK", "REPLAY_MISMATCH"}
