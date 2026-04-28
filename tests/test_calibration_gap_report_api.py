from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ExecutionRecord, Signal, WatchedToken, XRPLOrderbookSequence, XRPLOrderbookSnapshot
from app.main import create_app


def _seed_token_and_signal(app) -> tuple[int, int]:
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rGap", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        signal = Signal(
            strategy_name="unit",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=100.0,
            reason="unit",
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)

        return int(token.id), int(signal.id)


def test_gap_report_empty_is_safe() -> None:
    app = create_app()
    client = TestClient(app)

    with app.state.container.session_factory() as session:
        session.exec(delete(ExecutionRecord))
        session.exec(delete(XRPLOrderbookSequence))
        session.commit()

    response = client.get("/calibration/gap-report")
    assert response.status_code == 200

    body = response.json()
    assert body["sample_size"] == 0
    assert body["avg_execution_survivability_error"] == 0.0
    assert body["simulated_fail_in_real_rate"] == 0.0
    assert body["depth_illusion_rate"] == 0.0
    assert body["path_distortion_rate"] == 0.0
    assert body["fundedness_uncertainty_score"] >= 0.0
    assert body["ledger_delay_error"] == 0.0


def test_gap_report_returns_aggregates() -> None:
    app = create_app()
    client = TestClient(app)

    token_id, signal_id = _seed_token_and_signal(app)
    now = datetime.now(tz=timezone.utc)

    with app.state.container.session_factory() as session:
        session.add(
            ExecutionRecord(
                token_id=token_id,
                signal_id=signal_id,
                risk_decision_id=None,
                snapshot_id=1,
                position_id=None,
                side="BUY",
                requested_size=100.0,
                filled_size=100.0,
                fill_status="FILLED",
                avg_fill_price=1.02,
                slippage_vs_top=0.1,
                ledger_index_snapshot=100,
                ledger_index_signal=100,
                ledger_index_execution=101,
                ledger_index_inclusion=103,
                snapshot_time=now,
                signal_time=now,
                execution_time=now,
            )
        )
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token_id,
                ledger_index=100,
                best_bid=1.0,
                best_ask=1.02,
                bid_depth_xrp=160.0,
                ask_depth_xrp=120.0,
                spread_pct=2.0,
            )
        )
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token_id,
                ledger_index=101,
                best_bid=0.99,
                best_ask=1.03,
                bid_depth_xrp=90.0,
                ask_depth_xrp=55.0,
                spread_pct=3.2,
            )
        )
        session.add(
            XRPLOrderbookSnapshot(
                token_id=token_id,
                ledger_index=103,
                best_bid=0.98,
                best_ask=1.04,
                bid_depth_xrp=75.0,
                ask_depth_xrp=40.0,
                spread_pct=4.0,
            )
        )
        session.add(
            XRPLOrderbookSequence(
                token_id=token_id,
                start_ledger=100,
                end_ledger=103,
                snapshot_count=3,
                duration_ms=1200,
                decay_score=0.6,
                volatility_score=0.7,
                collapse_events=1,
            )
        )
        session.commit()

    response = client.get("/calibration/gap-report")
    assert response.status_code == 200

    body = response.json()
    assert body["sample_size"] >= 1
    assert body["sequence_count"] >= 1
    assert body["avg_execution_survivability_error"] > 0.0
    assert body["avg_depth_overestimation"] > 0.0
    assert body["avg_slippage_underestimation"] > 0.0
    assert body["avg_decay_score"] > 0.0
    assert body["avg_volatility_score"] > 0.0
    assert body["collapse_events_total"] >= 1
    assert "depth_illusion_rate" in body
    assert "path_distortion_rate" in body
    assert "fundedness_uncertainty_score" in body
    assert "ledger_delay_error" in body
