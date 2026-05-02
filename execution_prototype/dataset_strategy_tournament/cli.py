from __future__ import annotations
import argparse
import sys
from pathlib import Path

from .tournament import TournamentRunner


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m execution_prototype.dataset_strategy_tournament.cli",
        description="Phase 43: Dataset-Driven Strategy Tournament. Paper-only, read-only, no network.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to Phase 42 dataset folder",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./reports/phase43"),
        help="Output directory for tournament reports",
    )
    parser.add_argument(
        "--strategy-report",
        type=Path,
        default=None,
        help="Optional path to Phase 37 strategy report",
    )
    parser.add_argument(
        "--market-fixtures-report",
        type=Path,
        default=None,
        help="Optional path to Phase 40 market fixtures report",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with exit code 1 on critical issues",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run evaluation without writing output files",
    )
    parser.add_argument(
        "--min-signal-count",
        type=int,
        default=10,
        help="Minimum signal count for promotion consideration (default: 10)",
    )
    parser.add_argument(
        "--max-train-test-degradation",
        type=float,
        default=0.35,
        help="Maximum train-to-test degradation fraction for promotion (default: 0.35)",
    )
    parser.add_argument(
        "--include-holdout",
        action="store_true",
        help="Include holdout window in evaluation",
    )

    args = parser.parse_args()

    options = {
        "strategy_report": args.strategy_report,
        "market_fixtures_report": args.market_fixtures_report,
        "strict": args.strict,
        "dry_run": args.dry_run,
        "min_signal_count": args.min_signal_count,
        "max_train_test_degradation": args.max_train_test_degradation,
        "include_holdout": args.include_holdout,
    }

    print("--- Phase 43: Dataset Strategy Tournament ---")
    print(f"Dataset: {args.dataset}")
    print(f"Output:  {args.output_dir}")
    print(f"Dry run: {args.dry_run}")
    print("READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.")

    runner = TournamentRunner()
    summary = runner.run(
        dataset_folder=args.dataset,
        output_dir=args.output_dir,
        options=options,
    )

    print(f"Tournament complete. Strategies evaluated: {summary.strategies_evaluated}")
    print(f"Critical warnings: {summary.critical_warning_count}")
    print(f"Live trading readiness: {summary.live_trading_readiness}")

    if args.strict and summary.critical_warning_count > 0:
        print("STRICT MODE: Critical warnings found. Exiting with code 1.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
