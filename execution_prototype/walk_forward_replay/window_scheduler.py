"""Phase 44: Walk-Forward Window Scheduler.

Builds rolling train/evaluate windows from Phase 42 backtest windows.
Strictly chronological — no future data leaks into training.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .models import WalkForwardWindow, _stable_id


def _window_sort_key(window: Dict[str, Any]):
    """Sort key: (min_ledger_index, observed_at, window_id fallback)."""
    ledger = window.get("min_ledger_index") or window.get("ledger_index_start") or 0
    try:
        ledger = int(ledger)
    except (TypeError, ValueError):
        ledger = 0

    observed_at = window.get("observed_at") or window.get("timestamp") or ""
    window_id = window.get("window_id") or window.get("id") or ""
    return (ledger, str(observed_at), str(window_id))


def _ledger_range(windows: List[Dict[str, Any]]) -> List[int]:
    """Return [min_ledger, max_ledger] across a list of Phase 42 windows."""
    ledgers: List[int] = []
    for w in windows:
        for key in ("min_ledger_index", "ledger_index_start", "ledger_index"):
            val = w.get(key)
            if val is not None:
                try:
                    ledgers.append(int(val))
                except (TypeError, ValueError):
                    pass
                break
        for key in ("max_ledger_index", "ledger_index_end"):
            val = w.get(key)
            if val is not None:
                try:
                    ledgers.append(int(val))
                except (TypeError, ValueError):
                    pass
                break
    if not ledgers:
        return [0, 0]
    return [min(ledgers), max(ledgers)]


def _record_count(windows: List[Dict[str, Any]]) -> int:
    total = 0
    for w in windows:
        cnt = w.get("record_count") or w.get("records") or 0
        try:
            total += int(cnt)
        except (TypeError, ValueError):
            pass
    return total


def build_walk_forward_windows(
    dataset: Dict[str, Any],
    min_training_windows: int = 1,
    eval_window_size: int = 1,
    step_size: int = 1,
) -> List[WalkForwardWindow]:
    """Build rolling walk-forward train/eval windows from Phase 42 dataset.

    Sorts windows chronologically, then builds rolling slices:
      - training = windows[0:i]
      - evaluation = windows[i:i+eval_window_size]

    Returns empty list if insufficient windows.
    """
    raw_windows: List[Dict[str, Any]] = dataset.get("windows", [])

    if not raw_windows:
        return []

    sorted_windows = sorted(raw_windows, key=_window_sort_key)

    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")

    result: List[WalkForwardWindow] = []
    n = len(sorted_windows)
    chronological_order = 0

    i = min_training_windows
    while i + eval_window_size <= n:
        train_slice = sorted_windows[:i]
        eval_slice = sorted_windows[i: i + eval_window_size]

        train_ids = [
            w.get("window_id") or w.get("id") or str(idx)
            for idx, w in enumerate(train_slice)
        ]
        eval_ids = [
            w.get("window_id") or w.get("id") or str(idx + i)
            for idx, w in enumerate(eval_slice)
        ]
        eval_id = eval_ids[0] if len(eval_ids) == 1 else json.dumps(sorted(eval_ids))

        ww_id = _stable_id({
            "dataset_id": dataset_id,
            "training_window_ids": sorted(train_ids),
            "evaluation_window_id": eval_id,
            "chronological_order": chronological_order,
        })

        train_ledger_range = _ledger_range(train_slice)
        eval_ledger_range = _ledger_range(eval_slice)

        # Verify strict chronological ordering (no future leakage).
        limitations: List[str] = []
        if train_ledger_range[1] >= eval_ledger_range[0] and eval_ledger_range[0] > 0:
            limitations.append("potential_ledger_overlap_detected")

        walk_window = WalkForwardWindow(
            walk_window_id=ww_id,
            dataset_id=dataset_id,
            training_window_ids=train_ids,
            evaluation_window_id=eval_id,
            training_ledger_range=train_ledger_range,
            evaluation_ledger_range=eval_ledger_range,
            training_record_count=_record_count(train_slice),
            evaluation_record_count=_record_count(eval_slice),
            chronological_order=chronological_order,
            limitations=limitations,
        )
        result.append(walk_window)
        chronological_order += 1
        i += step_size

    return result
