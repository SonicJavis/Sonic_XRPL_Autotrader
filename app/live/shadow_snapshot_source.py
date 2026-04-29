from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Protocol


def _utc(ts: datetime) -> datetime:
    if not isinstance(ts, datetime):
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _finite_int(raw: object, *, default: int = 0) -> int:
    try:
        return int(_finite_float(raw, default=float(default)))
    except (TypeError, ValueError, OverflowError):
        return default


@dataclass(frozen=True, slots=True)
class ShadowSnapshotInput:
    token_id: int
    issuer: str
    currency: str
    ledger_index: int
    snapshot_price: float
    execution_price_proxy: float
    requested_size: float
    snapshot_derived_liquidity: float
    observed_possible_fill: float
    path_complexity: int
    route_instability: float
    competition_penalty: float
    slippage_estimate: float
    observed_at: datetime
    snapshot_quality_score: float = 1.0
    ledger_latency_proxy: float = 0.0


class ShadowSnapshotSource(Protocol):
    def next_snapshot(self) -> ShadowSnapshotInput | None:
        """Return the next deterministic shadow observation, or None when unavailable."""


class StaticShadowSnapshotSource:
    def __init__(self, snapshots: list[ShadowSnapshotInput]) -> None:
        self._snapshots = list(snapshots)
        self._index = 0

    def next_snapshot(self) -> ShadowSnapshotInput | None:
        if self._index >= len(self._snapshots):
            return None
        snapshot = self._snapshots[self._index]
        self._index += 1
        return ShadowSnapshotInput(
            token_id=_finite_int(snapshot.token_id),
            issuer=str(snapshot.issuer),
            currency=str(snapshot.currency),
            ledger_index=max(0, _finite_int(snapshot.ledger_index)),
            snapshot_price=max(0.0, _finite_float(snapshot.snapshot_price)),
            execution_price_proxy=max(0.0, _finite_float(snapshot.execution_price_proxy)),
            requested_size=max(0.0, _finite_float(snapshot.requested_size)),
            snapshot_derived_liquidity=max(0.0, _finite_float(snapshot.snapshot_derived_liquidity)),
            observed_possible_fill=max(0.0, _finite_float(snapshot.observed_possible_fill)),
            path_complexity=max(0, _finite_int(snapshot.path_complexity)),
            route_instability=max(0.0, min(1.0, _finite_float(snapshot.route_instability))),
            competition_penalty=max(0.0, min(1.0, _finite_float(snapshot.competition_penalty))),
            slippage_estimate=max(0.0, _finite_float(snapshot.slippage_estimate)),
            observed_at=_utc(snapshot.observed_at),
            snapshot_quality_score=max(0.0, min(1.0, _finite_float(snapshot.snapshot_quality_score, default=1.0))),
            ledger_latency_proxy=max(0.0, _finite_float(snapshot.ledger_latency_proxy)),
        )
