from datetime import datetime, timezone

from sqlmodel import delete, select

from app.db.models import ShadowDecisionRecord
from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop
from app.main import create_app


def _clear(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.commit()


def _loop(app, snapshot: ShadowSnapshotInput) -> XRPLShadowLoop:
    return XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([snapshot]),
    )


def test_invalid_token_id_rejected_before_persist() -> None:
    app = create_app()
    _clear(app)
    snapshot = ShadowSnapshotInput(
        token_id=0,
        issuer="",
        currency="USD",
        ledger_index=100,
        snapshot_price=1.0,
        execution_price_proxy=1.0,
        requested_size=100.0,
        snapshot_derived_liquidity=100.0,
        observed_possible_fill=90.0,
        path_complexity=1,
        route_instability=0.1,
        competition_penalty=0.0,
        slippage_estimate=0.01,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    result = _loop(app, snapshot).run_tick()

    assert result.reason == "INVALID_SHADOW_RECORD"
    with app.state.container.session_factory() as session:
        assert session.exec(select(ShadowDecisionRecord)).all() == []


def test_all_zero_metrics_rejected_before_persist() -> None:
    app = create_app()
    _clear(app)
    loop = XRPLShadowLoop(session_factory=app.state.container.session_factory, snapshot_source=StaticShadowSnapshotSource([]))
    record = ShadowDecisionRecord(
        token_id=1,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        latency_path_probability=0.0,
        memory_adjusted_probability=0.0,
        effective_size=0.0,
        memory_adjusted_effective_size=0.0,
        uncertainty_adjusted_value=0.0,
        drift_adjusted_ev=0.0,
    )

    assert loop._is_valid_record(record) is False
