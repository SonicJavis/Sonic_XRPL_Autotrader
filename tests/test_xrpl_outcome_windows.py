from datetime import datetime, timezone

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.validation.xrpl_outcome_window_builder import build_outcome_windows


def _snap(ledger: int, *, fill: float, liquidity: float = 100.0, path: int = 1, latency: float = 4000.0) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=1,
        issuer="rIssuer",
        currency="USD",
        ledger_index=ledger,
        snapshot_price=1.0,
        execution_price_proxy=1.0 + (ledger * 0.001),
        requested_size=100.0,
        snapshot_derived_liquidity=liquidity,
        observed_possible_fill=fill,
        path_complexity=path,
        route_instability=0.1,
        competition_penalty=0.2,
        slippage_estimate=0.01,
        observed_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
        snapshot_quality_score=1.0,
        ledger_latency_proxy=latency,
    )


def test_multi_ledger_window_aggregation() -> None:
    windows = build_outcome_windows(
        [_snap(100, fill=80), _snap(101, fill=50, path=1), _snap(102, fill=25, path=3), _snap(103, fill=0, path=3)],
        window_size=3,
    )

    first = windows[0]
    assert first.start_ledger == 101
    assert first.end_ledger == 103
    assert first.max_possible_fill == 50.0
    assert first.min_possible_fill == 0.0
    assert first.avg_possible_fill == 25.0
    assert first.route_changes_count == 1
    assert first.liquidity_decay_curve == [0.5, 0.25, 0.0]


def test_window_builder_is_deterministic_and_finite() -> None:
    snapshots = [_snap(100, fill=80), _snap(101, fill=50), _snap(102, fill=25)]

    assert [w.to_dict() for w in build_outcome_windows(snapshots)] == [w.to_dict() for w in build_outcome_windows(snapshots)]
