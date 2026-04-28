from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import delete, select

from app.db.models import ShadowDecisionRecord, WatchedToken
from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop
from app.main import create_app


def _clear(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.exec(delete(WatchedToken))
        session.commit()


def _seed_token(app, issuer: str = "rIssuer", currency: str = "USD") -> int:
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer=issuer, currency=currency, is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)
        return int(token.id)


def _snapshot(token_id: int, *, risky: bool = False, offset: int = 0) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=token_id,
        issuer="rIssuer",
        currency="USD",
        ledger_index=100 + offset,
        snapshot_price=1.0,
        execution_price_proxy=1.35 if risky else 1.0,
        requested_size=100.0,
        snapshot_derived_liquidity=500.0 if risky else 120.0,
        observed_possible_fill=50.0 if risky else 90.0,
        path_complexity=2 if risky else 1,
        route_instability=0.5 if risky else 0.1,
        competition_penalty=0.5 if risky else 0.0,
        slippage_estimate=0.5 if risky else 0.01,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=offset),
    )


def test_run_tick_creates_one_shadow_decision_record() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id)]),
    )

    result = loop.run_tick()

    assert result.stored is True
    with app.state.container.session_factory() as session:
        rows = session.exec(select(ShadowDecisionRecord)).all()
    assert len(rows) == 1
    assert rows[0].is_shadow is True
    assert rows[0].is_executable is False


def test_run_n_ticks_creates_deterministic_count() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id, offset=idx) for idx in range(3)]),
    )

    results = loop.run_n_ticks(5)

    assert [row.stored for row in results] == [True, True, True, False, False]
    with app.state.container.session_factory() as session:
        rows = session.exec(select(ShadowDecisionRecord).order_by(ShadowDecisionRecord.ledger_index)).all()
    assert [row.ledger_index for row in rows] == [100, 101, 102]


def test_collapse_regime_risk_blocks_advisory_allow_trade() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id, risky=True)]),
    )

    result = loop.run_tick()

    assert result.record is not None
    assert result.record.memory_adjusted_probability < result.record.latency_path_probability
    assert result.record.drift_adjusted_ev <= 0.0
    assert result.record.is_executable is False


def test_shadow_loop_empty_source_fails_closed() -> None:
    app = create_app()
    _clear(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([]),
    )

    result = loop.run_tick()

    assert result.stored is False
    assert result.reason == "NO_SNAPSHOT_AVAILABLE"


def test_shadow_loop_source_has_no_execution_symbols() -> None:
    source = Path("app/live/xrpl_shadow_loop.py").read_text(encoding="utf-8")
    blocked = [
        "sub" + "mit",
        "sig" + "n",
        "wal" + "let",
        "auto" + "fill",
        "Offer" + "Create",
        "Pay" + "ment",
    ]

    for term in blocked:
        assert term not in source
