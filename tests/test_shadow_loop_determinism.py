from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
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


def _seed_token(app) -> int:
    with app.state.container.session_factory() as session:
        token = WatchedToken(issuer="rDeterministic", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)
        return int(token.id)


def _snapshot(token_id: int, offset: int = 0) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=token_id,
        issuer="rDeterministic",
        currency="USD",
        ledger_index=100 + offset,
        snapshot_price=1.0,
        execution_price_proxy=1.01,
        requested_size=100.0,
        snapshot_derived_liquidity=150.0,
        observed_possible_fill=90.0,
        path_complexity=1,
        route_instability=0.1,
        competition_penalty=0.05,
        slippage_estimate=0.01,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=offset),
    )


def _signature(row: ShadowDecisionRecord) -> tuple[float, float, float, str, str]:
    return (
        row.memory_adjusted_probability,
        row.effective_size,
        row.drift_adjusted_ev,
        row.regime,
        row.risk_flags_json,
    )


def test_same_input_snapshots_produce_same_field_level_outputs() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)

    first = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id)]),
    ).build_shadow_decision(_snapshot(token_id))
    second = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id)]),
    ).build_shadow_decision(_snapshot(token_id))

    assert _signature(first) == _signature(second)


def test_run_n_ticks_zero_negative_and_available_count() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snapshot(token_id, idx) for idx in range(2)]),
    )

    assert loop.run_n_ticks(0) == []
    assert loop.run_n_ticks(-1) == []
    assert [row.stored for row in loop.run_n_ticks(3)] == [True, True, False]
    with app.state.container.session_factory() as session:
        assert len(session.exec(select(ShadowDecisionRecord)).all()) == 2


def test_snapshot_exhaustion_does_not_persist_record() -> None:
    app = create_app()
    _clear(app)
    loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([]),
    )

    result = loop.run_tick()

    assert result.reason == "NO_SNAPSHOT_AVAILABLE"
    assert result.stored is False
    with app.state.container.session_factory() as session:
        assert session.exec(select(ShadowDecisionRecord)).all() == []


def test_decisions_endpoint_returns_newest_first_with_id_tiebreaker() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    observed_at = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        for ledger in (100, 101):
            row = XRPLShadowLoop(
                session_factory=app.state.container.session_factory,
                snapshot_source=StaticShadowSnapshotSource([]),
            ).build_shadow_decision(_snapshot(token_id))
            row.ledger_index = ledger
            row.observed_at = observed_at
            session.add(row)
        session.commit()

    body = TestClient(app).get("/live/shadow/decisions").json()
    ids = [row["id"] for row in body["decisions"]]

    assert ids == sorted(ids, reverse=True)


def test_idempotent_static_source_replay_outputs_match() -> None:
    app = create_app()
    _clear(app)
    token_id = _seed_token(app)
    snapshots = [_snapshot(token_id, idx) for idx in range(3)]

    first_loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource(snapshots),
    )
    first = [_signature(result.record) for result in first_loop.run_n_ticks(3) if result.record is not None]
    _clear(app)
    token_id = _seed_token(app)
    replay = [_snapshot(token_id, idx) for idx in range(3)]
    second_loop = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource(replay),
    )
    second = [_signature(result.record) for result in second_loop.run_n_ticks(3) if result.record is not None]

    assert first == second
