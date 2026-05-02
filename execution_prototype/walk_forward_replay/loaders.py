"""Phase 44: Loaders for dataset and Phase 43 tournament outputs.

Read-only. Never modifies source files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return records


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_dataset(dataset_dir: Path) -> Dict[str, Any]:
    """Load Phase 42 dataset folder. Read-only; never modifies source."""
    result: Dict[str, Any] = {
        "dataset_dir": dataset_dir,
        "manifest": {},
        "sources": [],
        "windows": [],
        "quality_report": {},
        "records_by_window": {
            "train": [],
            "validation": [],
            "test": [],
            "replay": [],
            "holdout": [],
        },
    }
    if not dataset_dir or not dataset_dir.exists():
        return result

    manifest_path = dataset_dir / "dataset_manifest.json"
    if manifest_path.exists():
        result["manifest"] = _load_json(manifest_path)

    sources_path = dataset_dir / "dataset_sources.jsonl"
    if sources_path.exists():
        result["sources"] = _load_jsonl(sources_path)

    windows_path = dataset_dir / "backtest_windows.jsonl"
    if windows_path.exists():
        result["windows"] = _load_jsonl(windows_path)

    quality_path = dataset_dir / "dataset_quality_report.json"
    if quality_path.exists():
        result["quality_report"] = _load_json(quality_path)

    for wtype in ("train", "validation", "test", "replay", "holdout"):
        rpath = dataset_dir / f"{wtype}_records.jsonl"
        if rpath.exists():
            result["records_by_window"][wtype] = _load_jsonl(rpath)

    return result


def load_tournament(tournament_dir: Optional[Path]) -> Optional[Dict[str, Any]]:
    """Load Phase 43 tournament folder outputs. Returns None if not present.

    Searches for the most recent timestamped sub-directory inside tournament_dir,
    or reads directly from tournament_dir if it contains the expected files.
    """
    if not tournament_dir or not tournament_dir.exists():
        return None

    result: Dict[str, Any] = {
        "tournament_dir": tournament_dir,
        "summary": {},
        "tournament_results": [],
        "strategy_window_evaluations": [],
        "generalization_scores": [],
    }

    # Walk to find the most recent sub-directory (timestamped output from Phase 43).
    candidate_dirs = [tournament_dir]
    sub_dirs = sorted(
        [d for d in tournament_dir.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    if sub_dirs:
        candidate_dirs = sub_dirs + [tournament_dir]

    loaded = False
    for candidate in candidate_dirs:
        summary_path = candidate / "dataset_strategy_tournament_summary.json"
        if summary_path.exists():
            result["summary"] = _load_json(summary_path)
            loaded = True

            results_path = candidate / "dataset_strategy_tournament_results.jsonl"
            if results_path.exists():
                result["tournament_results"] = _load_jsonl(results_path)

            evals_path = candidate / "strategy_window_evaluations.jsonl"
            if evals_path.exists():
                result["strategy_window_evaluations"] = _load_jsonl(evals_path)

            gen_path = candidate / "strategy_generalization_scores.jsonl"
            if gen_path.exists():
                result["generalization_scores"] = _load_jsonl(gen_path)

            break

    return result if loaded else None
