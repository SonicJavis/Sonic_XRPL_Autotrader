from datetime import datetime, timezone
from math import isfinite

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.validation.xrpl_outcome_window_builder import build_outcome_windows


def _snap(token: int, issuer: str, ledger: int, *, price: float = 1.0, fill: float = 50.0, liquidity: float = 100.0, path: int = 1):
    return ShadowSnapshotInput(
        token_id=token,
        issuer=issuer,
        currency="USD",
        ledger_index=ledger,
        snapshot_price=price,
        execution_price_proxy=price + 0.01,
        requested_size=100.0,
        snapshot_derived_liquidity=liquidity,
        observed_possible_fill=fill,
        path_complexity=path,
        route_instability=0.1,
        competition_penalty=0.2,
        slippage_estimate=0.01,
        observed_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
        snapshot_quality_score=1.0,
        ledger_latency_proxy=4000.0,
    )


def test_mixed_tokens_and_issuers_do_not_cross_contaminate() -> None:
    windows = build_outcome_windows(
        [_snap(1, "a", 1), _snap(2, "a", 2), _snap(1, "b", 2), _snap(1, "a", 2, fill=20)],
        window_size=2,
    )

    assert len(windows) == 1
    assert windows[0].token_id == 1
    assert windows[0].issuer == "a"
    assert windows[0].avg_possible_fill == 20.0


def test_unsorted_duplicate_and_window_size_edges_are_deterministic() -> None:
    snapshots = [_snap(1, "a", 3, path=2), _snap(1, "a", 1), _snap(1, "a", 2, path=1), _snap(1, "a", 2, fill=5, path=3)]

    zero = build_outcome_windows(snapshots, window_size=0)
    negative = build_outcome_windows(snapshots, window_size=-5)
    repeated = build_outcome_windows(list(reversed(snapshots)), window_size=0)

    assert [window.to_dict() for window in zero] == [window.to_dict() for window in negative]
    assert [window.to_dict() for window in zero] == [window.to_dict() for window in repeated]
    assert zero[0].end_ledger == 2
    assert zero[0].route_changes_count == 0


def test_missing_forward_and_ledger_gap_do_not_create_optimistic_window() -> None:
    assert build_outcome_windows([_snap(1, "a", 1)], window_size=3) == []
    assert build_outcome_windows([_snap(1, "a", 1), _snap(1, "a", 5, fill=100)], window_size=3) == []


def test_curves_are_finite_and_bounded_when_first_price_zero() -> None:
    windows = build_outcome_windows([_snap(1, "a", 1, price=0.0), _snap(1, "a", 2, fill=200, liquidity=100)], window_size=1)

    assert len(windows) == 1
    assert all(isfinite(value) for value in windows[0].price_drift_curve)
    assert all(isfinite(value) and 0.0 <= value <= 1.0 for value in windows[0].liquidity_decay_curve)
