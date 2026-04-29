from datetime import datetime, timezone

from app.calibration.xrpl_time_execution_model import XRPLTimeExecutionInput
from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop
from app.main import create_app


def _snap(ledger: int, *, slippage: float = 0.01, path: int = 1) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=1,
        issuer="r",
        currency="USD",
        ledger_index=ledger,
        snapshot_price=1.0,
        execution_price_proxy=1.0,
        requested_size=100.0,
        snapshot_derived_liquidity=100.0,
        observed_possible_fill=80.0,
        path_complexity=path,
        route_instability=0.1,
        competition_penalty=0.1,
        slippage_estimate=slippage,
        observed_at=datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc),
    )


def test_shadow_loop_handles_none_snapshot() -> None:
    loop = XRPLShadowLoop(session_factory=create_app().state.container.session_factory, snapshot_source=StaticShadowSnapshotSource([]))

    result = loop.run_tick()

    assert result.stored is False
    assert result.reason == "NO_SNAPSHOT_AVAILABLE"
    assert loop.skipped_snapshot_count == 1


def test_shadow_loop_rejects_ledger_regression() -> None:
    loop = XRPLShadowLoop(
        session_factory=create_app().state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([_snap(10), _snap(9)]),
    )

    assert loop.run_tick().stored is True
    result = loop.run_tick()

    assert result.reason == "LEDGER_REGRESSION"
    assert loop.rejected_snapshot_count == 1


def test_xrpl_specific_penalties_applied_for_bad_snapshot() -> None:
    loop = XRPLShadowLoop(session_factory=create_app().state.container.session_factory, snapshot_source=StaticShadowSnapshotSource([]))

    clean_snapshot = _snap(10)
    clean = loop._aggregate_from_tick(clean_snapshot, loop.time_model.evaluate(_time_input(clean_snapshot)))
    risky_snapshot = _snap(11, slippage=0.2, path=3)
    risky = loop._aggregate_from_tick(risky_snapshot, loop.time_model.evaluate(_time_input(risky_snapshot)))

    assert risky.avg_phantom_penalty > clean.avg_phantom_penalty
    assert risky.avg_route_instability > clean.avg_route_instability


def _time_input(snapshot: ShadowSnapshotInput) -> XRPLTimeExecutionInput:
    return XRPLTimeExecutionInput(
        snapshot_price=snapshot.snapshot_price,
        execution_price=snapshot.execution_price_proxy,
        requested_size=snapshot.requested_size,
        snapshot_derived_liquidity=snapshot.snapshot_derived_liquidity,
        observed_possible_fill=snapshot.observed_possible_fill,
        ledger_index_snapshot=snapshot.ledger_index,
        ledger_index_execution=snapshot.ledger_index + 1,
        competition_penalty=snapshot.competition_penalty,
        base_fill_probability=0.85,
        path_complexity=snapshot.path_complexity,
        slippage_estimate=snapshot.slippage_estimate,
    )
