from datetime import datetime, timezone

from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource


def _snapshot(token_id: int = 1) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=token_id,
        issuer="rIssuer",
        currency="USD",
        ledger_index=100,
        snapshot_price=1.0,
        execution_price_proxy=1.0,
        requested_size=100.0,
        snapshot_derived_liquidity=120.0,
        observed_possible_fill=80.0,
        path_complexity=1,
        route_instability=0.1,
        competition_penalty=0.0,
        slippage_estimate=0.01,
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )


def test_static_source_returns_deterministic_ticks() -> None:
    source = StaticShadowSnapshotSource([_snapshot(1), _snapshot(2)])

    assert source.next_snapshot().token_id == 1
    assert source.next_snapshot().token_id == 2
    assert source.next_snapshot() is None


def test_empty_static_source_fails_closed() -> None:
    assert StaticShadowSnapshotSource([]).next_snapshot() is None


def test_static_source_clamps_unsafe_values() -> None:
    source = StaticShadowSnapshotSource(
        [
            ShadowSnapshotInput(
                token_id=1,
                issuer="rIssuer",
                currency="USD",
                ledger_index=-5,
                snapshot_price=-1.0,
                execution_price_proxy=-2.0,
                requested_size=-10.0,
                snapshot_derived_liquidity=-100.0,
                observed_possible_fill=-50.0,
                path_complexity=-3,
                route_instability=8.0,
                competition_penalty=9.0,
                slippage_estimate=-0.1,
                observed_at=datetime(2026, 4, 28, 12, 0),
            )
        ]
    )

    tick = source.next_snapshot()

    assert tick.ledger_index == 0
    assert tick.snapshot_price == 0.0
    assert tick.requested_size == 0.0
    assert tick.route_instability == 1.0
    assert tick.competition_penalty == 1.0
    assert tick.observed_at.tzinfo is not None
