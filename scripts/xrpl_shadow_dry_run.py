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


def run_dry_run(*, replay_path: Path, ticks: int, database_url: str) -> dict[str, object]:
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
    return {
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run replay-only XRPL shadow validation.")
    parser.add_argument("--replay-path", default="data/xrpl_replay_regression_snapshots.json")
    parser.add_argument("--ticks", type=int, default=20)
    parser.add_argument("--database-url", default="sqlite:///./sonic_autotrader.db")
    args = parser.parse_args()
    print(json.dumps(run_dry_run(replay_path=Path(args.replay_path), ticks=args.ticks, database_url=args.database_url), sort_keys=True))


if __name__ == "__main__":
    main()
