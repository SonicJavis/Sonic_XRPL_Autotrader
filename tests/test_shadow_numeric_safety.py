from datetime import datetime, timezone
from math import isfinite

from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop
from app.main import create_app


def test_shadow_loop_outputs_are_finite_and_bounded() -> None:
    app = create_app()
    snapshot = ShadowSnapshotInput(
        token_id=1,
        issuer="rNumeric",
        currency="USD",
        ledger_index=100,
        snapshot_price=1.0,
        execution_price_proxy=1_000_000.0,
        requested_size=10_000_000.0,
        snapshot_derived_liquidity=1_000_000_000.0,
        observed_possible_fill=1.0,
        path_complexity=99,
        route_instability=1.0,
        competition_penalty=1.0,
        slippage_estimate=10_000.0,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    record = XRPLShadowLoop(
        session_factory=app.state.container.session_factory,
        snapshot_source=StaticShadowSnapshotSource([]),
    ).build_shadow_decision(snapshot)

    assert 0.0 <= record.latency_path_probability <= 1.0
    assert 0.0 <= record.memory_adjusted_probability <= 1.0
    assert record.effective_size >= 0.0
    assert record.memory_adjusted_effective_size >= 0.0
    assert isfinite(record.uncertainty_adjusted_value)
    assert isfinite(record.drift_adjusted_ev)
    assert abs(record.uncertainty_adjusted_value) < 1e12
    assert abs(record.drift_adjusted_ev) < 1e12
