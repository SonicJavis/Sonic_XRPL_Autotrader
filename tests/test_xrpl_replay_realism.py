from math import isfinite

from app.live.replay_snapshot_source import ReplaySnapshotSource


def test_regression_replay_clamps_fills_and_enforces_monotonic_ledgers() -> None:
    source = ReplaySnapshotSource("data/xrpl_replay_regression_snapshots.json")
    rows = []
    while True:
        snapshot = source.next_snapshot()
        if snapshot is None:
            break
        rows.append(snapshot)

    assert [row.ledger_index for row in rows] == sorted({row.ledger_index for row in rows})
    assert all(row.snapshot_derived_liquidity > 0 for row in rows)
    assert all(row.observed_possible_fill <= row.snapshot_derived_liquidity for row in rows)
    assert all(isfinite(getattr(row, field)) for row in rows for field in _FLOAT_FIELDS)


def test_regression_replay_is_deterministic_and_phantom_heavy() -> None:
    first = ReplaySnapshotSource("data/xrpl_replay_regression_snapshots.json")
    second = ReplaySnapshotSource("data/xrpl_replay_regression_snapshots.json")
    first_rows = [first.next_snapshot() for _ in range(5)]
    second_rows = [second.next_snapshot() for _ in range(5)]

    assert first_rows == second_rows
    phantom_rows = [row for row in first_rows if row is not None and row.snapshot_derived_liquidity - row.observed_possible_fill > 100]
    assert phantom_rows


_FLOAT_FIELDS = (
    "snapshot_price",
    "execution_price_proxy",
    "requested_size",
    "snapshot_derived_liquidity",
    "observed_possible_fill",
    "route_instability",
    "competition_penalty",
    "slippage_estimate",
    "snapshot_quality_score",
    "ledger_latency_proxy",
)
