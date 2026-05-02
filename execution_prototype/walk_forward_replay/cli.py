"""Phase 44: Walk-Forward Replay CLI.

Paper-only, read-only, no network, no wallet, no signing, no submission.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .degradation import generate_degradation_warnings
from .lifecycle import generate_lifecycle_recommendations
from .loaders import load_dataset, load_tournament
from .models import WalkForwardReplaySummary, _stable_id
from .replay_engine import run_replay
from .report_writer import write_report
from .stability import compute_stability_profiles
from .window_scheduler import build_walk_forward_windows


def _build_summary(
    dataset: Dict[str, Any],
    windows,
    evaluations,
    profiles,
    warnings,
    recommendations,
) -> WalkForwardReplaySummary:
    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")
    dataset_quality = dataset.get("quality_report", {}).get("quality_score", 50)

    band_counts: Dict[str, int] = {}
    for p in profiles:
        band_counts[p.stability_band] = band_counts.get(p.stability_band, 0) + 1

    rec_counts: Dict[str, int] = {}
    for r in recommendations:
        rec_counts[r.lifecycle_status] = rec_counts.get(r.lifecycle_status, 0) + 1

    critical_count = sum(1 for w in warnings if w.severity == "critical")

    ts = datetime.now(timezone.utc).isoformat()
    summary_id = _stable_id({
        "dataset_id": dataset_id,
        "ts": ts,
        "windows": len(windows),
        "evaluations": len(evaluations),
    })

    return WalkForwardReplaySummary(
        summary_id=summary_id,
        dataset_id=dataset_id,
        dataset_quality_score=dataset_quality,
        strategies_evaluated=len({e.strategy_id for e in evaluations}),
        walk_forward_windows=len(windows),
        total_evaluations=len(evaluations),
        stable_strategy_count=band_counts.get("stable", 0),
        watch_strategy_count=band_counts.get("watch", 0),
        unstable_strategy_count=band_counts.get("unstable", 0),
        insufficient_data_count=band_counts.get("insufficient_data", 0),
        critical_warning_count=critical_count,
        lifecycle_recommendation_counts=rec_counts,
        live_trading_readiness="0/100",
        prohibited_live_action="READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. LIVE TRADING FORBIDDEN.",
        limitations=["paper_only_evaluation", "no_live_data_used"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m execution_prototype.walk_forward_replay.cli",
        description=(
            "Phase 44: Walk-Forward Backtest Replay Engine + Strategy Stability Tracking."
            " Paper-only, read-only, no network."
        ),
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to Phase 42 dataset folder",
    )
    parser.add_argument(
        "--phase43-report",
        type=Path,
        default=None,
        help="Optional path to Phase 43 tournament report folder",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Base output directory (reports/phase44/<timestamp>/ will be created inside)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with exit code 1 on critical warnings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run evaluation without writing output files",
    )
    parser.add_argument(
        "--min-training-windows",
        type=int,
        default=1,
        help="Minimum number of training windows before evaluation (default: 1)",
    )
    parser.add_argument(
        "--evaluation-window-size",
        type=int,
        default=1,
        help="Number of windows in each evaluation slice (default: 1)",
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=1,
        help="Step size for rolling walk-forward (default: 1)",
    )
    parser.add_argument(
        "--min-sample-size",
        type=int,
        default=5,
        help="Minimum sample size for confidence (default: 5)",
    )
    parser.add_argument(
        "--max-score-drop-warning",
        type=int,
        default=-15,
        help="Score delta threshold for degradation warning (default: -15)",
    )
    parser.add_argument(
        "--max-score-drop-critical",
        type=int,
        default=-30,
        help="Score delta threshold for critical degradation warning (default: -30)",
    )

    args = parser.parse_args()

    config: Dict[str, Any] = {
        "min_training_windows": args.min_training_windows,
        "evaluation_window_size": args.evaluation_window_size,
        "step_size": args.step_size,
        "min_sample_size": args.min_sample_size,
        "max_score_drop_warning": args.max_score_drop_warning,
        "max_score_drop_critical": args.max_score_drop_critical,
        "strict": args.strict,
        "dry_run": args.dry_run,
    }

    print("--- Phase 44: Walk-Forward Backtest Replay ---")
    print(f"Dataset: {args.dataset}")
    print(f"Phase43 report: {args.phase43_report}")
    print(f"Output:  {args.output_dir}")
    print(f"Dry run: {args.dry_run}")
    print("READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.")

    dataset = load_dataset(args.dataset)
    tournament = load_tournament(args.phase43_report)

    windows = build_walk_forward_windows(
        dataset,
        min_training_windows=args.min_training_windows,
        eval_window_size=args.evaluation_window_size,
        step_size=args.step_size,
    )

    if not windows:
        print("WARNING: Insufficient Phase 42 windows for walk-forward replay (insufficient_data).")

    evaluations = run_replay(dataset, tournament, windows, config)

    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")
    profiles = compute_stability_profiles(evaluations, dataset_id, config, dataset)
    warnings_list = generate_degradation_warnings(evaluations, profiles, dataset, tournament, config)
    recommendations = generate_lifecycle_recommendations(profiles, warnings_list, dataset, config)

    summary = _build_summary(dataset, windows, evaluations, profiles, warnings_list, recommendations)

    print(f"Walk-forward windows: {summary.walk_forward_windows}")
    print(f"Strategies evaluated: {summary.strategies_evaluated}")
    print(f"Stable: {summary.stable_strategy_count} | Watch: {summary.watch_strategy_count}"
          f" | Unstable: {summary.unstable_strategy_count}")
    print(f"Critical warnings: {summary.critical_warning_count}")
    print(f"Live trading readiness: {summary.live_trading_readiness}")

    if not args.dry_run:
        out_path = write_report(
            output_dir=args.output_dir,
            windows=windows,
            evaluations=evaluations,
            profiles=profiles,
            warnings=warnings_list,
            recommendations=recommendations,
            summary=summary,
            dataset=dataset,
            config=config,
        )
        print(f"Report written to: {out_path}")

    if args.strict and summary.critical_warning_count > 0:
        print("STRICT MODE: Critical warnings found. Exiting with code 1.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
