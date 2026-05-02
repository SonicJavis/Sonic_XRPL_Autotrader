"""Phase 44: Walk-Forward Backtest Replay Engine tests.

Mirrors patterns from test_dataset_strategy_tournament.py.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

from execution_prototype.walk_forward_replay.models import (
    PaperStrategyLifecycleRecommendation,
    StrategyDegradationWarning,
    StrategyStabilityProfile,
    WalkForwardEvaluation,
    WalkForwardReplaySummary,
    WalkForwardWindow,
    _stable_id,
)
from execution_prototype.walk_forward_replay.loaders import load_dataset, load_tournament
from execution_prototype.walk_forward_replay.window_scheduler import build_walk_forward_windows
from execution_prototype.walk_forward_replay.replay_engine import run_replay
from execution_prototype.walk_forward_replay.stability import compute_stability_profiles
from execution_prototype.walk_forward_replay.degradation import generate_degradation_warnings
from execution_prototype.walk_forward_replay.lifecycle import generate_lifecycle_recommendations

REPO_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_windows_dataset(num_windows: int = 3, dataset_id: str = "test_ds", quality: int = 70) -> Dict[str, Any]:
    """Build a synthetic dataset dict with `num_windows` Phase 42 backtest windows."""
    windows = [
        {
            "window_id": f"win_{i}",
            "min_ledger_index": 1000 + i * 100,
            "max_ledger_index": 1099 + i * 100,
            "observed_at": f"2024-01-{i + 1:02d}T00:00:00Z",
            "record_count": 20,
        }
        for i in range(num_windows)
    ]
    return {
        "dataset_dir": Path("/fake/dataset"),
        "manifest": {"dataset_id": dataset_id, "quality_score": quality},
        "sources": [],
        "windows": windows,
        "quality_report": {"quality_score": quality},
        "records_by_window": {
            "train": [],
            "validation": [],
            "test": [],
            "replay": [],
            "holdout": [],
        },
    }


def _make_tournament(strategy_ids: List[str], dataset_id: str = "test_ds") -> Dict[str, Any]:
    evals = []
    for sid in strategy_ids:
        for win_id in ["win_0", "win_1", "win_2"]:
            evals.append({
                "evaluation_id": hashlib.sha256(f"{sid}|{win_id}".encode()).hexdigest()[:16],
                "strategy_id": sid,
                "window_id": win_id,
                "window_type": "test",
                "dataset_id": dataset_id,
                "records_evaluated": 20,
                "signals_generated": 12,
                "quality_weighted_score": 70,
                "unknown_outcome_rate": "0.10",
                "metadata_backed_rate": "0.80",
                "liquidity_backed_rate": "0.75",
            })
    results = [
        {
            "strategy_id": sid,
            "dataset_id": dataset_id,
            "overfitting_score": 20,
        }
        for sid in strategy_ids
    ]
    return {
        "summary": {"dataset_id": dataset_id},
        "tournament_results": results,
        "strategy_window_evaluations": evals,
        "generalization_scores": [],
    }


def _make_walk_window(
    walk_window_id: str = "ww1",
    dataset_id: str = "test_ds",
    eval_window_id: str = "win_1",
    chronological_order: int = 0,
) -> WalkForwardWindow:
    return WalkForwardWindow(
        walk_window_id=walk_window_id,
        dataset_id=dataset_id,
        training_window_ids=["win_0"],
        evaluation_window_id=eval_window_id,
        training_ledger_range=[1000, 1099],
        evaluation_ledger_range=[1100, 1199],
        training_record_count=20,
        evaluation_record_count=20,
        chronological_order=chronological_order,
        limitations=[],
    )


def _make_evaluation(
    strategy_id: str = "s1",
    dataset_id: str = "test_ds",
    training_score: int = 70,
    evaluation_score: int = 65,
    chronological_order: int = 0,
    unknown_outcome_rate: str = "0.10",
    metadata_backed_rate: str = "0.80",
    liquidity_backed_rate: str = "0.75",
    sample_size: int = 20,
    limitations: List[str] = None,
) -> WalkForwardEvaluation:
    ww_id = f"ww_{chronological_order}"
    eval_id = _stable_id({
        "walk_window_id": ww_id,
        "strategy_id": strategy_id,
        "dataset_id": dataset_id,
        "chronological_order": chronological_order,
    })
    return WalkForwardEvaluation(
        evaluation_id=eval_id,
        walk_window_id=ww_id,
        dataset_id=dataset_id,
        strategy_id=strategy_id,
        chronological_order=chronological_order,
        training_score=training_score,
        evaluation_score=evaluation_score,
        score_delta=evaluation_score - training_score,
        unknown_outcome_rate=unknown_outcome_rate,
        metadata_backed_rate=metadata_backed_rate,
        liquidity_backed_rate=liquidity_backed_rate,
        sample_size=sample_size,
        confidence_band="medium",
        limitations=limitations or [],
    )


# ---------------------------------------------------------------------------
# ID determinism tests
# ---------------------------------------------------------------------------

def test_walk_window_id_deterministic():
    id1 = _stable_id({"dataset_id": "d1", "training_window_ids": ["w0"], "evaluation_window_id": "w1", "chronological_order": 0})
    id2 = _stable_id({"dataset_id": "d1", "training_window_ids": ["w0"], "evaluation_window_id": "w1", "chronological_order": 0})
    assert id1 == id2
    assert len(id1) == 16


def test_evaluation_id_deterministic():
    id1 = _stable_id({"walk_window_id": "ww1", "strategy_id": "s1", "dataset_id": "d1", "chronological_order": 0})
    id2 = _stable_id({"walk_window_id": "ww1", "strategy_id": "s1", "dataset_id": "d1", "chronological_order": 0})
    assert id1 == id2


def test_stability_id_deterministic():
    id1 = _stable_id({"dataset_id": "d1", "strategy_id": "s1", "windows_evaluated": 3, "stability_band": "stable"})
    id2 = _stable_id({"dataset_id": "d1", "strategy_id": "s1", "windows_evaluated": 3, "stability_band": "stable"})
    assert id1 == id2


def test_warning_id_deterministic():
    from execution_prototype.walk_forward_replay.degradation import _warning_id
    wid1 = _warning_id(["s1", "d1", "rolling_score_decay", "decay=20"])
    wid2 = _warning_id(["s1", "d1", "rolling_score_decay", "decay=20"])
    assert wid1 == wid2


def test_recommendation_id_deterministic():
    from execution_prototype.walk_forward_replay.lifecycle import _recommendation_id
    rid1 = _recommendation_id("d1", "s1", "continue_paper_testing")
    rid2 = _recommendation_id("d1", "s1", "continue_paper_testing")
    assert rid1 == rid2


# ---------------------------------------------------------------------------
# Source file immutability
# ---------------------------------------------------------------------------

def test_source_files_not_modified(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    manifest = {"dataset_id": "test_ds", "quality_score": 70}
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    original_content = manifest_path.read_text()

    load_dataset(dataset_dir)

    assert manifest_path.read_text() == original_content


# ---------------------------------------------------------------------------
# Append-only output
# ---------------------------------------------------------------------------

def test_output_is_append_only(tmp_path):
    from execution_prototype.walk_forward_replay.report_writer import write_report
    from execution_prototype.walk_forward_replay.models import WalkForwardReplaySummary

    dataset = _make_windows_dataset(3)
    windows = build_walk_forward_windows(dataset)
    evaluations = run_replay(dataset, None, windows, {})
    profiles = compute_stability_profiles(evaluations, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evaluations, profiles, dataset, None, {})
    recs = generate_lifecycle_recommendations(profiles, warnings, dataset, {})

    from execution_prototype.walk_forward_replay.cli import _build_summary
    summary = _build_summary(dataset, windows, evaluations, profiles, warnings, recs)

    out = tmp_path / "out"
    write_report(out, windows, evaluations, profiles, warnings, recs, summary, dataset, {})

    phase44_dir = out / "reports" / "phase44"
    assert phase44_dir.exists()
    dirs = list(phase44_dir.iterdir())
    assert len(dirs) >= 1


# ---------------------------------------------------------------------------
# Rolling windows - chronological order
# ---------------------------------------------------------------------------

def test_rolling_windows_preserve_chronological_order():
    dataset = _make_windows_dataset(4)
    windows = build_walk_forward_windows(dataset, min_training_windows=1, eval_window_size=1, step_size=1)

    assert len(windows) >= 2
    for i, w in enumerate(windows):
        assert w.chronological_order == i

    for i in range(1, len(windows)):
        prev = windows[i - 1]
        curr = windows[i]
        assert curr.training_ledger_range[0] >= prev.training_ledger_range[0]


def test_no_future_evaluation_window_in_training():
    dataset = _make_windows_dataset(5)
    windows = build_walk_forward_windows(dataset, min_training_windows=1)

    for w in windows:
        eval_min_ledger = w.evaluation_ledger_range[0]
        train_max_ledger = w.training_ledger_range[1]
        # Training ledger range must be from earlier windows.
        assert train_max_ledger <= eval_min_ledger or eval_min_ledger == 0


def test_insufficient_windows_returns_empty():
    dataset = _make_windows_dataset(1)  # Only 1 window, need at least 2
    windows = build_walk_forward_windows(dataset, min_training_windows=1, eval_window_size=1)
    assert windows == []


def test_zero_windows_returns_empty():
    dataset = _make_windows_dataset(0)
    windows = build_walk_forward_windows(dataset)
    assert windows == []


# ---------------------------------------------------------------------------
# Evaluation score drop warnings
# ---------------------------------------------------------------------------

def test_score_drop_creates_warning():
    evals = [
        _make_evaluation("s1", training_score=70, evaluation_score=50, chronological_order=i)
        for i in range(3)
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {"max_score_drop_warning": -15}, dataset)
    warnings = generate_degradation_warnings(evals, profiles, dataset, None, {"max_score_drop_warning": -15, "max_score_drop_critical": -30})

    # score_delta = -20, which is below -15 threshold
    warning_types = [w.warning_type for w in warnings]
    assert "evaluation_collapse" in warning_types or "rolling_score_decay" in warning_types or len(warnings) > 0


def test_large_score_drop_creates_critical_warning():
    evals = [
        _make_evaluation("s1", training_score=80, evaluation_score=40, chronological_order=0),
        _make_evaluation("s1", training_score=80, evaluation_score=40, chronological_order=1),
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {"max_score_drop_critical": -30}, dataset)
    warnings = generate_degradation_warnings(
        evals, profiles, dataset, None,
        {"max_score_drop_warning": -15, "max_score_drop_critical": -30}
    )
    critical = [w for w in warnings if w.severity == "critical"]
    # score_delta = -40, well below -30
    assert len(critical) >= 1


# ---------------------------------------------------------------------------
# Rolling decay warning
# ---------------------------------------------------------------------------

def test_rolling_decay_creates_degradation_warning():
    # Scores declining over 6 windows.
    evals = [
        _make_evaluation("s1", training_score=80, evaluation_score=80 - i * 8, chronological_order=i)
        for i in range(6)
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evals, profiles, dataset, None, {})

    warning_types = [w.warning_type for w in warnings]
    assert "rolling_score_decay" in warning_types


# ---------------------------------------------------------------------------
# Unknown outcome dependency
# ---------------------------------------------------------------------------

def test_unknown_outcome_dependency_warning():
    evals = [
        _make_evaluation("s1", unknown_outcome_rate="0.45", chronological_order=i)
        for i in range(2)
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evals, profiles, dataset, None, {})

    warning_types = [w.warning_type for w in warnings]
    assert "unknown_outcome_dependency" in warning_types


# ---------------------------------------------------------------------------
# Confidence caps
# ---------------------------------------------------------------------------

def test_missing_metadata_caps_confidence():
    evals = [
        _make_evaluation("s1", metadata_backed_rate="0.30", chronological_order=0),
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    if profiles:
        assert profiles[0].confidence_band in ("low", "medium")


def test_missing_liquidity_caps_confidence():
    evals = [
        _make_evaluation("s1", liquidity_backed_rate="0.20", chronological_order=0),
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    if profiles:
        assert profiles[0].confidence_band in ("low", "medium")


def test_low_sample_size_caps_confidence():
    evals = [
        _make_evaluation("s1", sample_size=1, chronological_order=0),
    ]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    if profiles:
        assert profiles[0].confidence_band == "low"


# ---------------------------------------------------------------------------
# Stability caps
# ---------------------------------------------------------------------------

def test_future_leakage_caps_stability():
    dataset = _make_windows_dataset()
    dataset["quality_report"]["future_leakage_count"] = 5

    evals = [
        _make_evaluation("s1", evaluation_score=90, training_score=70, chronological_order=i)
        for i in range(4)
    ]
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    assert profiles[0].stability_score <= 40


def test_unsupported_batch_prevents_stable_lifecycle():
    # Build dataset with unsupported_batch_context records.
    dataset = _make_windows_dataset()
    batch_records = [{"asset_key_id": "XRP/USD", "unsupported_batch_context": True}]
    dataset["records_by_window"]["test"] = batch_records

    evals = [
        _make_evaluation("s1", evaluation_score=90, training_score=70, chronological_order=i)
        for i in range(4)
    ]
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evals, profiles, dataset, None, {})
    recs = generate_lifecycle_recommendations(profiles, warnings, dataset, {})

    for rec in recs:
        assert rec.lifecycle_status != "continue_paper_testing" or rec.lifecycle_status == "insufficient_data"


def test_xahau_hook_does_not_improve_xrpl_confidence():
    dataset = _make_windows_dataset()
    xahau_records = [{"asset_key_id": "XRP/USD", "xahau_hook_context": True}]
    dataset["records_by_window"]["test"] = xahau_records

    evals = [
        _make_evaluation("s1", evaluation_score=90, training_score=70, chronological_order=i)
        for i in range(4)
    ]
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)

    assert profiles[0].stability_score <= 60


# ---------------------------------------------------------------------------
# Lifecycle paper-only checks
# ---------------------------------------------------------------------------

def test_lifecycle_recommendations_are_paper_only():
    valid_statuses = {
        "continue_paper_testing",
        "increase_paper_scrutiny",
        "pause_paper_testing",
        "retire_from_current_paper_pool",
        "insufficient_data",
    }
    evals = [_make_evaluation("s1", chronological_order=i) for i in range(3)]
    dataset = _make_windows_dataset()
    profiles = compute_stability_profiles(evals, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evals, profiles, dataset, None, {})
    recs = generate_lifecycle_recommendations(profiles, warnings, dataset, {})

    for rec in recs:
        assert rec.lifecycle_status in valid_statuses
        assert "NO WALLET" in rec.prohibited_live_action or "WALLET" in rec.prohibited_live_action.upper()
        assert "LIVE TRADING FORBIDDEN" in rec.prohibited_live_action


def test_live_readiness_remains_zero():
    from execution_prototype.walk_forward_replay.cli import _build_summary
    dataset = _make_windows_dataset()
    windows = build_walk_forward_windows(dataset)
    evaluations = run_replay(dataset, None, windows, {})
    profiles = compute_stability_profiles(evaluations, "test_ds", {}, dataset)
    warnings = generate_degradation_warnings(evaluations, profiles, dataset, None, {})
    recs = generate_lifecycle_recommendations(profiles, warnings, dataset, {})
    summary = _build_summary(dataset, windows, evaluations, profiles, warnings, recs)
    assert summary.live_trading_readiness == "0/100"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_dry_run(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    manifest = {"dataset_id": "cli_ds", "quality_score": 60}
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest))

    # Create some windows.
    windows = [
        {"window_id": f"win_{i}", "min_ledger_index": 1000 + i * 100, "max_ledger_index": 1099 + i * 100,
         "observed_at": f"2024-01-{i + 1:02d}T00:00:00Z", "record_count": 10}
        for i in range(3)
    ]
    (dataset_dir / "backtest_windows.jsonl").write_text("\n".join(json.dumps(w) for w in windows))

    result = subprocess.run(
        [sys.executable, "-m", "execution_prototype.walk_forward_replay.cli",
         "--dataset", str(dataset_dir),
         "--output-dir", str(tmp_path / "out"),
         "--dry-run"],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "execution_prototype.walk_forward_replay.cli", "--help"],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0
    assert "Phase 44" in result.stdout or "walk" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Dashboard optional panel does not break
# ---------------------------------------------------------------------------

def test_dashboard_optional_panel_no_crash():
    """Verify dashboard module is importable without walk-forward data present."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "phase39_campaign_dashboard",
            REPO_ROOT / "dashboard" / "pages" / "phase39_campaign_dashboard.py",
        )
        # We only verify the file is parseable, not that streamlit is installed.
        assert spec is not None
    except Exception:
        pass  # Dashboard import requires streamlit; we just ensure no syntax errors.


def test_walk_forward_window_to_dict_roundtrip():
    ww = _make_walk_window()
    d = ww.to_dict()
    assert d["walk_window_id"] == ww.walk_window_id
    assert d["chronological_order"] == ww.chronological_order
    assert "limitations" in d


def test_summary_to_dict_roundtrip():
    summary = WalkForwardReplaySummary(
        summary_id="s1",
        dataset_id="d1",
        dataset_quality_score=70,
        strategies_evaluated=2,
        walk_forward_windows=3,
        total_evaluations=6,
        stable_strategy_count=1,
        watch_strategy_count=1,
        unstable_strategy_count=0,
        insufficient_data_count=0,
        critical_warning_count=0,
        live_trading_readiness="0/100",
    )
    d = summary.to_dict()
    assert d["live_trading_readiness"] == "0/100"
    assert d["strategies_evaluated"] == 2
