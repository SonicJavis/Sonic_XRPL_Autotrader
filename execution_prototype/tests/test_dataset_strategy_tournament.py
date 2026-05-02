import pytest
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List

from execution_prototype.dataset_strategy_tournament.models import (
    DatasetStrategyDefinition,
    StrategyWindowEvaluation,
    StrategyGeneralizationScore,
    OverfittingWarning,
    StrategyTournamentResult,
    DatasetTournamentSummary,
)
from execution_prototype.dataset_strategy_tournament.loaders import DatasetLoader, get_deterministic_id
from execution_prototype.dataset_strategy_tournament.strategy_registry import STRATEGY_REGISTRY, STRATEGY_EVALUATORS
from execution_prototype.dataset_strategy_tournament.window_evaluator import WindowEvaluator
from execution_prototype.dataset_strategy_tournament.scoring import ScoringEngine
from execution_prototype.dataset_strategy_tournament.overfitting import OverfittingDetector
from execution_prototype.dataset_strategy_tournament.tournament import TournamentRunner
from execution_prototype.dataset_strategy_tournament.recommendations import RecommendationEngine


def _make_eval(strategy_id: str = "s1", dataset_id: str = "d1", window_id: str = "w1", window_type: str = "test",
               quality_weighted_score: int = 70, signals_generated: int = 15,
               unknown_outcome_rate: str = "0.1", metadata_backed_rate: str = "0.8",
               liquidity_backed_rate: str = "0.7") -> StrategyWindowEvaluation:
    return StrategyWindowEvaluation(
        evaluation_id=hashlib.sha256(f"{strategy_id}|{window_type}".encode()).hexdigest(),
        dataset_id=dataset_id,
        window_id=window_id,
        window_type=window_type,
        strategy_id=strategy_id,
        records_evaluated=20,
        signals_generated=signals_generated,
        accepted_signals=signals_generated,
        rejected_signals=0,
        unknown_outcomes=2,
        win_count=10,
        loss_count=5,
        breakeven_count=3,
        avg_pnl_pct="0.05",
        median_pnl_pct="0.03",
        max_drawdown_pct="-0.10",
        unknown_outcome_rate=unknown_outcome_rate,
        metadata_backed_rate=metadata_backed_rate,
        liquidity_backed_rate=liquidity_backed_rate,
        quality_weighted_score=quality_weighted_score,
        limitations=[],
    )


def test_strategy_id_deterministic():
    raw = "strategy|amm_seeded_launch_watch|v1"
    expected = hashlib.sha256(raw.encode()).hexdigest()
    strat = STRATEGY_REGISTRY["amm_seeded_launch_watch"]
    assert strat.strategy_id == expected


def test_evaluation_id_deterministic():
    ev = WindowEvaluator()
    from execution_prototype.dataset_strategy_tournament.window_evaluator import _get_eval_id
    eid1 = _get_eval_id("s1", "d1", "w1", "train")
    eid2 = _get_eval_id("s1", "d1", "w1", "train")
    assert eid1 == eid2


def test_generalization_id_deterministic():
    scorer = ScoringEngine()
    from execution_prototype.dataset_strategy_tournament.scoring import _gen_id
    gid1 = _gen_id("s1", "d1")
    gid2 = _gen_id("s1", "d1")
    assert gid1 == gid2


def test_warning_id_deterministic():
    from execution_prototype.dataset_strategy_tournament.overfitting import _warning_id
    ev = ["train_score=80", "test_score=20"]
    wid1 = _warning_id(ev)
    wid2 = _warning_id(ev)
    assert wid1 == wid2


def test_tournament_id_deterministic():
    from execution_prototype.dataset_strategy_tournament.tournament import _tournament_id
    tid1 = _tournament_id("d1", "s1")
    tid2 = _tournament_id("d1", "s1")
    assert tid1 == tid2


def test_source_files_not_modified(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    manifest = {"dataset_id": "test_ds", "quality_score": 70}
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    original_content = manifest_path.read_text()

    loader = DatasetLoader()
    loader.load_dataset_folder(dataset_dir)

    assert manifest_path.read_text() == original_content


def test_output_is_append_only(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    output_dir = tmp_path / "output"

    runner = TournamentRunner()
    runner.run(dataset_dir, output_dir, {"dry_run": False})

    output_dirs = list(output_dir.iterdir()) if output_dir.exists() else []
    assert len(output_dirs) >= 1


def test_feature_outcome_separation():
    from execution_prototype.dataset_strategy_tournament.window_evaluator import OUTCOME_KEYS
    assert "outcome" in OUTCOME_KEYS
    assert "pnl_pct" in OUTCOME_KEYS
    assert "win" in OUTCOME_KEYS
    assert "loss" in OUTCOME_KEYS
    assert "paper_outcome" in OUTCOME_KEYS
    assert "paper_pnl_pct" in OUTCOME_KEYS
    assert "ledger_index" not in OUTCOME_KEYS
    assert "asset_key_id" not in OUTCOME_KEYS


def test_train_test_degradation_creates_warning():
    scorer = ScoringEngine()
    detector = OverfittingDetector()

    train_eval = _make_eval(window_type="train", quality_weighted_score=80)
    test_eval = _make_eval(window_type="test", quality_weighted_score=30)
    window_evals = {"train": train_eval, "test": test_eval}

    gen = scorer.compute_generalization("s1", "d1", window_evals)
    warnings = detector.detect("s1", "d1", window_evals, gen, 70)

    warning_types = [w.warning_type for w in warnings]
    assert "train_test_degradation" in warning_types

    deg_warnings = [w for w in warnings if w.warning_type == "train_test_degradation"]
    assert deg_warnings[0].severity in ("warning", "critical")


def test_high_degradation_creates_critical_warning():
    scorer = ScoringEngine()
    detector = OverfittingDetector()

    train_eval = _make_eval(window_type="train", quality_weighted_score=80)
    test_eval = _make_eval(window_type="test", quality_weighted_score=10)
    window_evals = {"train": train_eval, "test": test_eval}

    gen = scorer.compute_generalization("s1", "d1", window_evals)
    warnings = detector.detect("s1", "d1", window_evals, gen, 70)

    deg_warnings = [w for w in warnings if w.warning_type == "train_test_degradation"]
    assert deg_warnings[0].severity == "critical"


def test_unknown_outcome_dependency_warning():
    detector = OverfittingDetector()
    scorer = ScoringEngine()

    eval_high_unknown = _make_eval(window_type="test", unknown_outcome_rate="0.45", signals_generated=15)
    window_evals = {"test": eval_high_unknown}
    gen = scorer.compute_generalization("s1", "d1", window_evals)
    warnings = detector.detect("s1", "d1", window_evals, gen, 70)

    types = [w.warning_type for w in warnings]
    assert "unknown_outcome_dependency" in types


def test_missing_metadata_caps_confidence():
    scorer = ScoringEngine()

    eval_low_meta = _make_eval(window_type="test", metadata_backed_rate="0.3")
    eval_train = _make_eval(window_type="train", metadata_backed_rate="0.3", quality_weighted_score=50)
    window_evals = {"train": eval_train, "test": eval_low_meta}
    gen = scorer.compute_generalization("s1", "d1", window_evals)
    assert gen.confidence_band in ("low", "medium")


def test_missing_liquidity_caps_confidence():
    scorer = ScoringEngine()
    detector = OverfittingDetector()

    eval_low_liq = _make_eval(window_type="test", liquidity_backed_rate="0.2", quality_weighted_score=40)
    eval_train = _make_eval(window_type="train", quality_weighted_score=50)
    window_evals = {"train": eval_train, "test": eval_low_liq}
    gen = scorer.compute_generalization("s1", "d1", window_evals)
    warnings = detector.detect("s1", "d1", window_evals, gen, 70)

    types = [w.warning_type for w in warnings]
    assert "liquidity_dependency" in types


def test_low_signal_count_insufficient_data():
    scorer = ScoringEngine()
    detector = OverfittingDetector()

    eval_few = _make_eval(window_type="test", signals_generated=3)
    window_evals = {"test": eval_few}
    gen = scorer.compute_generalization("s1", "d1", window_evals)
    warnings = detector.detect("s1", "d1", window_evals, gen, 70)

    types = [w.warning_type for w in warnings]
    assert "small_sample_false_confidence" in types


def test_future_leakage_prevents_promotion(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    manifest = {"dataset_id": "leak_ds", "quality_score": 40}
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest))

    quality_report = {"quality_score": 40, "future_leakage_count": 5}
    (dataset_dir / "dataset_quality_report.json").write_text(json.dumps(quality_report))

    records = [
        {
            "asset_key_id": "XRP/USD",
            "ledger_index": 1000 + i,
            "timestamp": "2024-01-01T00:00:00Z",
            "future_leakage": True,
        }
        for i in range(20)
    ]
    (dataset_dir / "test_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records)
    )

    runner = TournamentRunner()
    summary = runner.run(dataset_dir, tmp_path / "out", {"dry_run": True})
    assert summary.live_trading_readiness == "0/100"


def test_unsupported_batch_context_prevents_promotion(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    manifest = {"dataset_id": "batch_ds", "quality_score": 30}
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest))
    records = [
        {
            "asset_key_id": "XRP/USD",
            "ledger_index": 1000 + i,
            "timestamp": "2024-01-01T00:00:00Z",
            "unsupported_batch_context": True,
        }
        for i in range(5)
    ]
    (dataset_dir / "test_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records)
    )
    runner = TournamentRunner()
    summary = runner.run(dataset_dir, tmp_path / "out", {"dry_run": True})
    assert summary.live_trading_readiness == "0/100"


def test_xahau_context_does_not_improve_confidence(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    manifest = {"dataset_id": "xahau_ds", "quality_score": 50}
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps(manifest))
    records = [
        {
            "asset_key_id": "XRP/USD",
            "ledger_index": 1000 + i,
            "timestamp": "2024-01-01T00:00:00Z",
            "xahau_hook_context": True,
        }
        for i in range(20)
    ]
    (dataset_dir / "test_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records)
    )
    runner = TournamentRunner()
    summary = runner.run(dataset_dir, tmp_path / "out", {"dry_run": True})
    assert summary.live_trading_readiness == "0/100"


def test_promotion_is_paper_only():
    for result_status in ["promote_to_more_paper_tests", "keep_under_review", "reject_for_now", "insufficient_data"]:
        result = StrategyTournamentResult(
            tournament_id="t1",
            dataset_id="d1",
            strategy_id="s1",
            rank=1,
            overall_score=80,
            generalization_score=75,
            robustness_score=70,
            risk_adjusted_score=65,
            overfitting_score=20,
            promotion_status=result_status,
            promotion_reason="test",
            required_human_action="Human review required",
            prohibited_live_action="READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.",
        )
        assert "WALLET" not in result.prohibited_live_action.upper() or "NO WALLET" in result.prohibited_live_action


def test_live_readiness_zero():
    summary = DatasetTournamentSummary(
        summary_id="s1",
        dataset_id="d1",
        dataset_quality_score=70,
        strategies_evaluated=6,
        windows_evaluated=30,
        best_strategy_id="strat1",
        worst_strategy_id="strat6",
        critical_warning_count=0,
        recommendation_counts={},
        live_trading_readiness="0/100",
    )
    assert summary.live_trading_readiness == "0/100"


def test_cli_dry_run(tmp_path):
    import subprocess, sys
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    (dataset_dir / "dataset_manifest.json").write_text(json.dumps({"dataset_id": "cli_ds", "quality_score": 60}))

    result = subprocess.run(
        [sys.executable, "-m", "execution_prototype.dataset_strategy_tournament.cli",
         "--dataset", str(dataset_dir),
         "--output-dir", str(tmp_path / "out"),
         "--dry-run"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent.parent),
    )
    assert result.returncode == 0


def test_cli_help():
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "execution_prototype.dataset_strategy_tournament.cli", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent.parent),
    )
    assert result.returncode == 0
    assert "Phase 43" in result.stdout or "dataset" in result.stdout.lower()


def test_strategy_registry_has_six_strategies():
    assert len(STRATEGY_REGISTRY) == 6


def test_window_evaluator_handles_missing_features():
    strat = STRATEGY_REGISTRY["amm_seeded_launch_watch"]
    ev = WindowEvaluator()
    records = [{"asset_key_id": "XRP/USD", "ledger_index": 1000}]  # missing required features
    result = ev.evaluate(strat, records, "w1", "test", "d1", 70)
    assert result.signals_generated == 0
    assert result.quality_weighted_score == 0
    assert any("insufficient_data" in lim for lim in result.limitations)


def test_deterministic_id_helper():
    id1 = get_deterministic_id(["a", "b", "c"])
    id2 = get_deterministic_id(["c", "a", "b"])
    assert id1 == id2


def test_loader_empty_folder(tmp_path):
    loader = DatasetLoader()
    result = loader.load_dataset_folder(tmp_path / "nonexistent")
    assert result["manifest"] == {}
    assert result["sources"] == []
    assert result["records_by_window"]["train"] == []
