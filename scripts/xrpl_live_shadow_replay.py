from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.live.xrpl_live_shadow_pipeline import XRPLLedgerSequencer, XRPLLiveShadowPipeline
from app.validation.xrpl_validation_models import XRPLValidationResult


def run_fixture(path: Path) -> dict[str, object]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    base_time = _dt(fixture.get("base_time"))
    snapshots: dict[int, ShadowSnapshotInput | None] = {}
    for event in fixture.get("events", []):
        ledger_index = int(event.get("ledger_index", 0))
        snapshots[ledger_index] = _snapshot(ledger_index, event.get("snapshot"), base_time)
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: snapshots.get(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(
            initial_expected_ledger=int(fixture.get("initial_expected_ledger", 1)),
            max_gap_ledgers=int(fixture.get("max_gap_ledgers", 1)),
            max_buffer_size=int(fixture.get("max_buffer_size", 32)),
            max_processed_ledgers=int(fixture.get("max_processed_ledgers", 4096)),
        ),
        window_size=int(fixture.get("window_size", 3)),
        now_provider=lambda: base_time,
    )
    pipeline.replay_results = [_validation(row) for row in fixture.get("replay_results", [])]
    outputs: list[dict[str, object]] = []
    for event in fixture.get("events", []):
        ledger_index = int(event.get("ledger_index", 0))
        processing_time = base_time + timedelta(milliseconds=max(0.0, float(event.get("processing_delay_ms", 0))))
        outputs.extend(
            pipeline.ingest_ledger_event(
                XRPLLedgerEvent(
                    ledger_index=ledger_index,
                    ledger_hash=f"h{ledger_index}",
                    close_time=base_time + timedelta(seconds=ledger_index * 4),
                    validated=bool(event.get("validated", True)),
                    raw={"type": "ledgerClosed"},
                ),
                processing_time=processing_time,
                network_head=int(event.get("network_head", ledger_index)),
            )
        )
    report = pipeline.to_report()
    report["fixture"] = str(path)
    report["outputs"] = outputs
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline XRPL live shadow replay runner")
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    report = run_fixture(Path(args.fixture))
    print(json.dumps(report, sort_keys=True, indent=2))


def _snapshot(ledger_index: int, raw: Any, base_time: datetime) -> ShadowSnapshotInput | None:
    if raw is None:
        return None
    data = raw if isinstance(raw, dict) else {}
    observed = max(0.0, float(data.get("observed_possible_fill", 75.0)))
    liquidity = max(observed, float(data.get("snapshot_derived_liquidity", 100.0)))
    return ShadowSnapshotInput(
        token_id=int(data.get("token_id", 1)),
        issuer=str(data.get("issuer", "rIssuer")),
        currency=str(data.get("currency", "USD")),
        ledger_index=ledger_index,
        snapshot_price=float(data.get("snapshot_price", 1.0 + ledger_index * 0.001)),
        execution_price_proxy=float(data.get("execution_price_proxy", 1.0 + ledger_index * 0.001)),
        requested_size=max(0.0, float(data.get("requested_size", 100.0))),
        snapshot_derived_liquidity=liquidity,
        observed_possible_fill=min(observed, liquidity),
        path_complexity=max(0, int(data.get("path_complexity", 1))),
        route_instability=max(0.0, min(1.0, float(data.get("route_instability", 0.1)))),
        competition_penalty=max(0.0, min(1.0, float(data.get("competition_penalty", 0.1)))),
        slippage_estimate=max(0.0, float(data.get("slippage_estimate", 0.01))),
        observed_at=base_time + timedelta(seconds=ledger_index * 4),
        snapshot_quality_score=max(0.0, min(1.0, float(data.get("snapshot_quality_score", 0.9)))),
        ledger_latency_proxy=max(0.0, float(data.get("ledger_latency_proxy", 100.0))),
    )


def _validation(row: dict[str, object]) -> XRPLValidationResult:
    return XRPLValidationResult(
        decision_id=int(row.get("decision_id", 0)),
        fill_probability_error=0.0,
        effective_size_error=0.0,
        ev_error=0.0,
        liquidity_disappearance=0.0,
        path_failure_rate=0.0,
        competition_miss_rate=0.0,
        latency_miss=0.0,
        regime_mismatch=False,
        disagreement_score=float(row.get("disagreement_score", 0.0)),
        brier_score=float(row.get("brier_score", 0.0)),
        overconfidence_flag=False,
        underconfidence_flag=False,
        confidence_error=0.0,
        error_attribution=str(row.get("error_attribution", "unknown")),
    )


def _dt(raw: object) -> datetime:
    if isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            value = datetime.fromtimestamp(0, tz=timezone.utc)
    else:
        value = datetime.fromtimestamp(0, tz=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


if __name__ == "__main__":
    main()
