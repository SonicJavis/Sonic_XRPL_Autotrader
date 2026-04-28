import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ExecutionRecord, MarketSnapshot, Signal, WatchedToken, XRPLOrderbookSnapshot
from app.main import create_app


def _assert_shadow_calibration_meta(body: dict[str, object]) -> None:
    assert body["is_shadow_calibration"] is True
    assert body["is_truth"] is False
    assert body["is_executable"] is False
    assert body["auto_apply"] is False
    assert body["requires_manual_review"] is True
    assert "xrpl_warning" in body


def _clear_shadow_tables(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ExecutionRecord))
        session.exec(delete(XRPLOrderbookSnapshot))
        session.exec(delete(MarketSnapshot))
        session.exec(delete(Signal))
        session.exec(delete(WatchedToken))
        session.commit()


def test_shadow_calibration_endpoints_return_safe_empty_state() -> None:
    app = create_app()
    client = TestClient(app)
    _clear_shadow_tables(app)

    for path in (
        "/calibration/shadow/xrpl/errors",
        "/calibration/shadow/xrpl/reliability",
        "/calibration/shadow/xrpl/recommendations",
        "/calibration/shadow/xrpl/time-model",
    ):
        res = client.get(path)
        assert res.status_code == 200
        body = res.json()
        _assert_shadow_calibration_meta(body)
        assert body["sample_count"] == 0


def test_shadow_calibration_endpoints_expose_xrpl_specific_metrics() -> None:
    app = create_app()
    client = TestClient(app)
    _clear_shadow_tables(app)
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rBayes", currency="USD", is_xrp=False)
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
            reason="shadow",
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)

        snapshot = MarketSnapshot(
            token_id=token.id,
            price_xrp=1.0,
            liquidity_xrp=400.0,
            liquidity_bid_xrp=200.0,
            liquidity_ask_xrp=200.0,
            spread_pct=2.0,
            best_bid=0.99,
            best_ask=1.01,
            bid_count=2,
            ask_count=2,
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
                observed_at=now,
            )
        )
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token.id,
                ledger_index=102,
                best_bid=0.98,
                best_ask=1.03,
                bid_depth_xrp=210.0,
                ask_depth_xrp=160.0,
                spread_pct=3.0,
                observed_at=now,
            )
        )
        session.add(
            ExecutionRecord(
                token_id=token.id,
                signal_id=signal.id,
                snapshot_id=snapshot.id,
                side="BUY",
                requested_size=100.0,
                filled_size=70.0,
                fill_status="PARTIAL",
                avg_fill_price=1.03,
                snapshot_time=now,
                signal_time=now,
                execution_time=now,
                ledger_index_snapshot=100,
                ledger_index_signal=100,
                ledger_index_execution=102,
                ledger_index_inclusion=102,
                execution_details_json=json.dumps(
                    {
                        "shadow": True,
                        "observed_fill_ratio": 0.15,
                        "observed_possible_fill": 15.0,
                        "path_execution_risk": 0.6,
                        "route_confidence": 0.25,
                        "observation_confidence": 0.7,
                        "ledger_delay_error": 0.3,
                        "routes_seen": ["direct", "auto_bridge"],
                        "snapshot_price": 1.0,
                        "execution_price": 1.04,
                        "snapshot_derived_liquidity": 280.0,
                        "path_complexity": 2,
                        "slippage_estimate": 0.02,
                    }
                ),
            )
        )
        session.commit()

    errors = client.get("/calibration/shadow/xrpl/errors")
    assert errors.status_code == 200
    errors_body = errors.json()
    _assert_shadow_calibration_meta(errors_body)
    assert errors_body["sample_count"] == 1
    assert errors_body["errors"]["phantom_penalty_avg"] > 0.0
    assert errors_body["errors"]["competition_failure_rate"] == 1.0
    assert errors_body["errors"]["observed_possible_fill_avg"] == 15.0

    reliability = client.get("/calibration/shadow/xrpl/reliability")
    assert reliability.status_code == 200
    reliability_body = reliability.json()
    _assert_shadow_calibration_meta(reliability_body)
    assert reliability_body["reliability_lower_bounds"]["competition_reliability"] <= 1.0
    assert reliability_body["reliability_lower_bounds"]["drift_reliability"] <= 1.0
    assert reliability_body["reliability_lower_bounds"]["latency_stability"] <= 1.0
    assert reliability_body["reliability_lower_bounds"]["path_reliability_weighting"] <= 1.0
    assert reliability_body["adaptive_weights"]["competition_reliability"] >= 1.0

    time_model = client.get("/calibration/shadow/xrpl/time-model")
    assert time_model.status_code == 200
    time_model_body = time_model.json()
    _assert_shadow_calibration_meta(time_model_body)
    assert time_model_body["is_advisory"] is True
    assert time_model_body["is_shadow"] is True
    assert time_model_body["sample_count"] == 1
    assert time_model_body["latency_distribution"] == [8.0]
    assert time_model_body["drift_distribution"] == [0.04]
    assert time_model_body["path_complexity_stats"]["avg"] == 2.0
    assert time_model_body["decay_stats"]["avg"] > 0.0

    recommendations = client.get("/calibration/shadow/xrpl/recommendations")
    assert recommendations.status_code == 200
    recommendations_body = recommendations.json()
    _assert_shadow_calibration_meta(recommendations_body)
    assert recommendations_body["recommendations"]["liquidity_haircut"] >= 0.0
    assert recommendations_body["recommendations"]["expected_slippage_multiplier"] > 1.0
    assert recommendations_body["recommendations"]["competition_risk_multiplier"] >= 1.0
