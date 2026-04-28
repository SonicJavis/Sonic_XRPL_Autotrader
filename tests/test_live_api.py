import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.models import ExecutionRecord, MarketSnapshot, Signal, WatchedToken, XRPLOrderbookSnapshot
from app.main import create_app


def _assert_live_meta(body: dict[str, object]) -> None:
    assert body["is_live"] is True
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert body["is_truth"] is False
    assert "xrpl_warning" in body


def test_live_endpoints_have_safe_empty_state() -> None:
    app = create_app()
    client = TestClient(app)

    for path in ("/live/status", "/live/metrics", "/live/executions", "/live/uncertainty"):
        res = client.get(path)
        assert res.status_code == 200
        body = res.json()
        _assert_live_meta(body)

    assert client.get("/live/status").json()["status"]["feed_status"] == "IDLE"
    assert client.get("/live/executions").json()["count"] == 0
    assert client.get("/live/uncertainty").json()["sample_size"] == 0


def test_live_endpoints_expose_shadow_metrics_and_records() -> None:
    app = create_app()
    client = TestClient(app)
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rShadowIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        signal = Signal(
            strategy_name="shadow",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=100.0,
            reason="shadow test",
            created_at=now,
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)

        snapshot = MarketSnapshot(
            token_id=token.id,
            price_xrp=1.0,
            liquidity_xrp=600.0,
            liquidity_bid_xrp=300.0,
            liquidity_ask_xrp=300.0,
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

        session.add(
            XRPLOrderbookSnapshot(
                token_id=token.id,
                ledger_index=100,
                best_bid=0.99,
                best_ask=1.01,
                bid_depth_xrp=300.0,
                ask_depth_xrp=280.0,
                spread_pct=2.0,
                observed_at=now - timedelta(seconds=8),
            )
        )
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token.id,
                ledger_index=102,
                best_bid=0.98,
                best_ask=1.03,
                bid_depth_xrp=220.0,
                ask_depth_xrp=210.0,
                spread_pct=3.0,
                observed_at=now - timedelta(seconds=4),
            )
        )

        session.add(
            ExecutionRecord(
                token_id=token.id,
                signal_id=signal.id,
                snapshot_id=snapshot.id,
                side="BUY",
                requested_size=100.0,
                filled_size=60.0,
                fill_status="PARTIAL",
                snapshot_time=now - timedelta(seconds=8),
                signal_time=now - timedelta(seconds=8),
                execution_time=now - timedelta(seconds=4),
                ledger_index_snapshot=100,
                ledger_index_signal=100,
                ledger_index_execution=102,
                ledger_index_inclusion=102,
                snapshot_age_ms=4000,
                execution_details_json=json.dumps(
                    {
                        "shadow": True,
                        "entry_ledger": 100,
                        "mid_ledger_fills_disabled": True,
                        "disagreement_score": 0.7,
                        "path_execution_risk": 0.8,
                        "route_confidence": 0.2,
                        "observation_confidence": 0.65,
                        "observed_fill_ratio": 0.45,
                        "ledger_delay_error": 0.25,
                        "false_confidence_flag": True,
                    }
                ),
            )
        )
        session.commit()

    status = client.get("/live/status")
    assert status.status_code == 200
    status_body = status.json()
    _assert_live_meta(status_body)
    assert status_body["status"]["feed_status"] == "ACTIVE"
    assert status_body["status"]["latest_ledger_index"] == 102

    metrics = client.get("/live/metrics")
    assert metrics.status_code == 200
    metrics_body = metrics.json()
    _assert_live_meta(metrics_body)
    assert metrics_body["metrics"]["shadow_execution_count"] == 1
    assert metrics_body["metrics"]["disagreement_score_live"] == 0.7
    assert metrics_body["metrics"]["path_execution_risk"] == 0.8
    assert metrics_body["metrics"]["observation_confidence_live"] == 0.65
    assert metrics_body["metrics"]["ledger_delay_error"] == 0.25

    executions = client.get("/live/executions")
    assert executions.status_code == 200
    executions_body = executions.json()
    _assert_live_meta(executions_body)
    assert executions_body["count"] == 1
    assert executions_body["executions"][0]["mid_ledger_fills_disabled"] is True
    assert executions_body["executions"][0]["route_confidence"] == 0.2

    uncertainty = client.get("/live/uncertainty")
    assert uncertainty.status_code == 200
    uncertainty_body = uncertainty.json()
    _assert_live_meta(uncertainty_body)
    assert uncertainty_body["sample_size"] == 1
    assert uncertainty_body["uncertainty"]["false_confidence_rate_live"] == 1.0
    assert uncertainty_body["uncertainty"]["route_confidence_live"] == 0.2