from __future__ import annotations

from collections.abc import Iterable
from statistics import mean

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow


def build_outcome_windows(snapshots: Iterable[ShadowSnapshotInput], window_size: int = 3) -> list[XRPLObservedOutcomeWindow]:
    ordered = sorted(list(snapshots), key=lambda item: (item.token_id, item.issuer, item.ledger_index))
    window_size = max(1, int(window_size))
    windows: list[XRPLObservedOutcomeWindow] = []
    for idx, snapshot in enumerate(ordered):
        forward = [
            item
            for item in ordered[idx + 1 :]
            if item.token_id == snapshot.token_id and item.issuer == snapshot.issuer and item.ledger_index > snapshot.ledger_index
        ][:window_size]
        if not forward:
            continue
        fills = [max(0.0, min(item.observed_possible_fill, item.snapshot_derived_liquidity)) for item in forward]
        first_price = max(snapshot.snapshot_price, 1e-9)
        path_values = [item.path_complexity for item in forward]
        windows.append(
            XRPLObservedOutcomeWindow(
                token_id=snapshot.token_id,
                issuer=snapshot.issuer,
                start_ledger=snapshot.ledger_index + 1,
                end_ledger=forward[-1].ledger_index,
                max_possible_fill=max(fills),
                min_possible_fill=min(fills),
                avg_possible_fill=mean(fills),
                liquidity_decay_curve=[
                    0.0 if item.snapshot_derived_liquidity <= 0 else min(item.observed_possible_fill / max(item.snapshot_derived_liquidity, 1e-9), 1.0)
                    for item in forward
                ],
                price_drift_curve=[(item.execution_price_proxy - first_price) / first_price for item in forward],
                route_changes_count=sum(1 for left, right in zip(path_values, path_values[1:]) if left != right),
                competition_events_proxy=max((item.competition_penalty for item in forward), default=0.0),
                latency_distribution_ms=[item.ledger_latency_proxy for item in forward],
                observed_at=forward[-1].observed_at,
            )
        )
    return windows
