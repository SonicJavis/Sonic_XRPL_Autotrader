from __future__ import annotations

import json
from pathlib import Path

from app.live.shadow_snapshot_source import ShadowSnapshotInput, ShadowSnapshotSource
from app.live.xrpl_ingestion_models import finite_float, non_negative_int, utc_or_epoch


class ReplaySnapshotSource:
    def __init__(self, path: str | Path = "data/xrpl_replay_snapshots.json", *, cycle: bool = False) -> None:
        self.path = Path(path)
        self.cycle = bool(cycle)
        self._snapshots = self._load()
        self._index = 0

    def next_snapshot(self) -> ShadowSnapshotInput | None:
        if not self._snapshots:
            return None
        if self._index >= len(self._snapshots):
            if not self.cycle:
                return None
            self._index = 0
        row = self._snapshots[self._index]
        self._index += 1
        return row

    def _load(self) -> list[ShadowSnapshotInput]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        if not isinstance(payload, list):
            return []
        rows: list[ShadowSnapshotInput] = []
        last_ledger = -1
        for item in payload:
            if not isinstance(item, dict):
                continue
            ledger_index = non_negative_int(item.get("ledger_index"))
            token_id = non_negative_int(item.get("token_id"))
            if ledger_index <= last_ledger or token_id <= 0:
                continue
            snapshot = ShadowSnapshotInput(
                token_id=token_id,
                issuer=str(item.get("issuer", "")),
                currency=str(item.get("currency", "")),
                ledger_index=ledger_index,
                snapshot_price=max(0.0, finite_float(item.get("snapshot_price"))),
                execution_price_proxy=max(0.0, finite_float(item.get("execution_price_proxy", item.get("snapshot_price")))),
                requested_size=max(0.0, finite_float(item.get("requested_size", 100.0))),
                snapshot_derived_liquidity=max(0.0, finite_float(item.get("snapshot_derived_liquidity"))),
                observed_possible_fill=max(0.0, finite_float(item.get("observed_possible_fill"))),
                path_complexity=max(0, non_negative_int(item.get("path_complexity", 1))),
                route_instability=max(0.0, min(1.0, finite_float(item.get("route_instability", 0.25)))),
                competition_penalty=max(0.0, min(1.0, finite_float(item.get("competition_penalty", 0.25)))),
                slippage_estimate=max(0.0, finite_float(item.get("slippage_estimate", 0.0))),
                observed_at=utc_or_epoch(item.get("observed_at")),
                snapshot_quality_score=max(0.0, min(1.0, finite_float(item.get("snapshot_quality_score", 1.0), default=1.0))),
                ledger_latency_proxy=max(0.0, finite_float(item.get("ledger_latency_proxy", 0.0))),
            )
            if snapshot.snapshot_derived_liquidity <= 0.0:
                continue
            if snapshot.observed_possible_fill > snapshot.snapshot_derived_liquidity:
                snapshot = ShadowSnapshotInput(
                    token_id=snapshot.token_id,
                    issuer=snapshot.issuer,
                    currency=snapshot.currency,
                    ledger_index=snapshot.ledger_index,
                    snapshot_price=snapshot.snapshot_price,
                    execution_price_proxy=snapshot.execution_price_proxy,
                    requested_size=snapshot.requested_size,
                    snapshot_derived_liquidity=snapshot.snapshot_derived_liquidity,
                    observed_possible_fill=snapshot.snapshot_derived_liquidity,
                    path_complexity=snapshot.path_complexity,
                    route_instability=snapshot.route_instability,
                    competition_penalty=snapshot.competition_penalty,
                    slippage_estimate=snapshot.slippage_estimate,
                    observed_at=snapshot.observed_at,
                    snapshot_quality_score=snapshot.snapshot_quality_score,
                    ledger_latency_proxy=snapshot.ledger_latency_proxy,
                )
            rows.append(snapshot)
            last_ledger = ledger_index
        return rows
