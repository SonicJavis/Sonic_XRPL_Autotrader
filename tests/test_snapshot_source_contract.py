from datetime import datetime, timezone

from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource


class GeneratedSnapshotSource:
    def __init__(self) -> None:
        self.index = 0

    def next_snapshot(self) -> ShadowSnapshotInput | None:
        self.index += 1
        if self.index > 2:
            return None
        return ShadowSnapshotInput(
            token_id=self.index,
            issuer=f"rIssuer{self.index}",
            currency="USD",
            ledger_index=100 + self.index,
            snapshot_price=1.0,
            execution_price_proxy=1.0,
            requested_size=100.0,
            snapshot_derived_liquidity=100.0,
            observed_possible_fill=80.0,
            path_complexity=1,
            route_instability=0.1,
            competition_penalty=0.0,
            slippage_estimate=0.01,
            observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        )


def test_snapshot_source_contract_does_not_assume_static_data() -> None:
    source = GeneratedSnapshotSource()

    assert source.next_snapshot().token_id == 1
    assert source.next_snapshot().token_id == 2
    assert source.next_snapshot() is None


def test_static_source_supports_deterministic_replay() -> None:
    snapshots = [
        ShadowSnapshotInput(
            token_id=1,
            issuer="rIssuer",
            currency="USD",
            ledger_index=100,
            snapshot_price=1.0,
            execution_price_proxy=1.0,
            requested_size=100.0,
            snapshot_derived_liquidity=100.0,
            observed_possible_fill=80.0,
            path_complexity=1,
            route_instability=0.1,
            competition_penalty=0.0,
            slippage_estimate=0.01,
            observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        )
    ]

    assert StaticShadowSnapshotSource(snapshots).next_snapshot() == StaticShadowSnapshotSource(snapshots).next_snapshot()
