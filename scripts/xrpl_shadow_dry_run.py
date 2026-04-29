from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from statistics import mean

from sqlmodel import Session, SQLModel, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.live.replay_snapshot_source import ReplaySnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop
from app.validation.xrpl_outcome_window_builder import build_outcome_windows
from app.validation.xrpl_validation_engine import compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLShadowPrediction


def _float(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if value == value and value not in (float("inf"), float("-inf")) else 0.0


def _memory_value(record, key: str) -> float:
    try:
        payload = json.loads(record.calibration_snapshot_json or "{}")
    except json.JSONDecodeError:
        return 0.0
    memory = payload.get("memory", {}) if isinstance(payload, dict) else {}
    return _float(memory.get(key)) if isinstance(memory, dict) else 0.0


def _payload(record) -> dict[str, object]:
    try:
        payload = json.loads(record.calibration_snapshot_json or "{}")
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def run_dry_run(*, replay_path: Path, ticks: int, database_url: str, validate: bool = False) -> dict[str, object]:
    engine = create_engine(database_url)
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def session_factory():
        with Session(engine) as session:
            yield session

    source = ReplaySnapshotSource(replay_path)
    loop = XRPLShadowLoop(session_factory=session_factory, snapshot_source=source)
    results = loop.run_n_ticks(ticks)
    records = [result.record for result in results if result.record is not None]
    probabilities = [_float(record.memory_adjusted_probability) for record in records]
    evs = [_float(record.drift_adjusted_ev) for record in records]
    phantom = [_memory_value(record, "avg_phantom_penalty") for record in records]
    competition = [_memory_value(record, "avg_competition_penalty") for record in records]
    summary = {
        "ticks_processed": max(0, int(ticks)),
        "decisions_stored": len(records),
        "skipped_snapshots": loop.skipped_snapshot_count,
        "rejected_snapshots": loop.rejected_snapshot_count,
        "avg_probability": round(mean(probabilities), 6) if probabilities else 0.0,
        "avg_drift_adjusted_ev": round(mean(evs), 6) if evs else 0.0,
        "avg_phantom_penalty": round(mean(phantom), 6) if phantom else 0.0,
        "avg_competition_penalty": round(mean(competition), 6) if competition else 0.0,
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
    }
    if validate:
        summary.update(_validation_summary(replay_path=replay_path, records=records))
    return summary


def _validation_summary(*, replay_path: Path, records: list[object]) -> dict[str, object]:
    source = ReplaySnapshotSource(replay_path)
    snapshots = []
    while True:
        snapshot = source.next_snapshot()
        if snapshot is None:
            break
        snapshots.append(snapshot)
    windows = {(window.token_id, window.start_ledger - 1): window for window in build_outcome_windows(snapshots)}
    results = []
    for record in records:
        payload = _payload(record)
        memory = payload.get("memory", {}) if isinstance(payload, dict) else {}
        time_model = payload.get("time_model", {}) if isinstance(payload, dict) else {}
        window = windows.get((int(record.token_id), int(record.ledger_index)))
        if window is None:
            continue
        prediction = XRPLShadowPrediction(
            decision_id=int(record.id or 0),
            token_id=int(record.token_id),
            issuer=str(record.issuer),
            ledger_index_start=int(record.ledger_index),
            predicted_probability=_float(record.memory_adjusted_probability),
            predicted_effective_size=_float(record.memory_adjusted_effective_size),
            predicted_ev=_float(record.drift_adjusted_ev),
            predicted_path_complexity=int(_float(memory.get("avg_path_complexity", 1))) if isinstance(memory, dict) else 1,
            predicted_route_instability=_float(memory.get("avg_route_instability", 0.0)) if isinstance(memory, dict) else 0.0,
            predicted_competition_penalty=_float(memory.get("avg_competition_penalty", 0.0)) if isinstance(memory, dict) else 0.0,
            predicted_regime=str(record.regime),
            predicted_confidence=_float(record.memory_adjusted_probability),
            created_at=record.observed_at,
            requested_size=_float(record.requested_size),
            predicted_liquidity=_float(memory.get("avg_liquidity_decay", 0.0)) * _float(record.requested_size) if isinstance(memory, dict) else 0.0,
            predicted_latency_ms=_float(time_model.get("latency_seconds", 0.0)) * 1000.0 if isinstance(time_model, dict) else 0.0,
        )
        results.append(compare_prediction_to_window(prediction, window))
    count = len(results)
    attribution: dict[str, int] = {}
    for result in results:
        attribution[result.error_attribution] = attribution.get(result.error_attribution, 0) + 1
    return {
        "avg_disagreement_score": round(mean([item.disagreement_score for item in results]), 6) if results else 0.0,
        "avg_brier_score": round(mean([item.brier_score for item in results]), 6) if results else 0.0,
        "overconfidence_rate": round(sum(1 for item in results if item.overconfidence_flag) / count, 6) if count else 0.0,
        "attribution_breakdown": dict(sorted(attribution.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run replay-only XRPL shadow validation.")
    parser.add_argument("--replay-path", default="data/xrpl_replay_regression_snapshots.json")
    parser.add_argument("--ticks", type=int, default=20)
    parser.add_argument("--database-url", default="sqlite:///./sonic_autotrader.db")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_dry_run(replay_path=Path(args.replay_path), ticks=args.ticks, database_url=args.database_url, validate=args.validate), sort_keys=True))


if __name__ == "__main__":
    main()
