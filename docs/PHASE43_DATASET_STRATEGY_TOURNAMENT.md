# Phase 43: Dataset-Driven Strategy Tournament

## Overview

Phase 43 implements a fully offline, paper-only tournament that evaluates multiple
trading strategy definitions against Phase 42 backtest dataset splits. No live data
is used, no network calls are made, and live trading readiness remains at **0/100**.

## Safety Statement

This module is read-only. It does not contain signing logic, private keys, or submission primitives.
All operations are performed on static offline snapshots produced by Phase 41/42.

**READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.**

## Architecture

```
execution_prototype/dataset_strategy_tournament/
├── __init__.py              # Public API exports
├── models.py                # Frozen dataclasses for all tournament entities
├── loaders.py               # Phase 42 dataset folder loader (offline only)
├── strategy_registry.py     # 6 paper-only strategy definitions + evaluators
├── window_evaluator.py      # Per-window signal generation and quality scoring
├── scoring.py               # Generalization score computation
├── overfitting.py           # Overfitting detection and warning generation
├── tournament.py            # Main TournamentRunner orchestrator
├── recommendations.py       # Human-readable promotion recommendations
├── report_writer.py         # JSONL + JSON + Markdown report output
└── cli.py                   # CLI entry point
```

## Strategy Families

| Strategy Name              | Family              | Description                                           |
|----------------------------|---------------------|-------------------------------------------------------|
| `amm_seeded_launch_watch`  | `amm_seeded`        | Detects AMM seeding events with liquidity > 0         |
| `trustline_spike_watch`    | `trustline_spike`   | Detects trustline growth spikes above threshold       |
| `offer_noise_filter`       | `offer_noise_filter`| Filters high-spread/low-volume offer noise            |
| `metadata_quality_guard`   | `metadata_quality`  | Requires metadata completeness >= 0.7                 |
| `liquidity_guard`          | `liquidity_guard`   | Requires liquidity score >= 0.5 with valid bid/ask    |
| `baseline_holdout_control` | `baseline`          | Simple baseline requiring asset_key_id + ledger_index |

## Window Types

Each strategy is evaluated across up to 5 window types:
- `train` — training split
- `validation` — validation split
- `test` — out-of-sample test split
- `replay` — chronological replay
- `holdout` — reserved holdout (opt-in via `--include-holdout`)

## Scoring

### Window Quality Score (0–100)
- Starts at 100
- Deductions for: unknown outcomes, missing metadata, missing liquidity, small samples,
  low dataset quality, future leakage (caps at 0), unsupported batch context, Xahau context

### Generalization Score
- Computes train→test degradation percentage
- Robustness = mean(window scores) − variance penalty
- Overfitting score derived from degradation

### Overall Tournament Score
```
overall = test_score * 0.40
        + robustness_score * 0.25
        + avg_quality * 0.20
        + (100 - overfitting_score) * 0.15
```

## Promotion Statuses

| Status                      | Condition                                                   |
|-----------------------------|-------------------------------------------------------------|
| `promote_to_more_paper_tests` | No critical warnings, test_score > 50, overfitting < 40 |
| `keep_under_review`           | Mixed results                                             |
| `reject_for_now`              | Critical warnings or poor test/overfitting scores         |
| `insufficient_data`           | < 5 total signals or avg quality < 30                    |

**All promotions are paper-only. Human approval required.**

## Overfitting Warnings

| Warning Type                  | Severity | Trigger                                        |
|-------------------------------|----------|------------------------------------------------|
| `train_test_degradation`      | critical | Degradation > 50%                              |
| `train_test_degradation`      | warning  | Degradation > 35%                              |
| `validation_collapse`         | warning  | Validation > 60, test < 40                     |
| `holdout_failure`             | warning  | Holdout score < 40                             |
| `unknown_outcome_dependency`  | warning  | Unknown outcome rate > 30%                     |
| `metadata_dependency`         | caution  | Metadata backed rate < 70%                     |
| `liquidity_dependency`        | caution  | Liquidity backed rate < 50%                    |
| `small_sample_false_confidence`| caution | Signals generated < 10                         |
| `quality_sensitive`           | warning  | Dataset quality score < 60                     |

## CLI Usage

```bash
python -m execution_prototype.dataset_strategy_tournament.cli \
  --dataset ./reports/phase42/20240101T000000Z \
  --output-dir ./reports/phase43 \
  --dry-run

# With strict mode (exit 1 on critical warnings)
python -m execution_prototype.dataset_strategy_tournament.cli \
  --dataset ./reports/phase42/20240101T000000Z \
  --output-dir ./reports/phase43 \
  --strict \
  --min-signal-count 10 \
  --max-train-test-degradation 0.35
```

## Output Files

Each run creates a timestamped subdirectory under `--output-dir`:

```
reports/phase43/20240101T120000Z/
├── dataset_strategy_definitions.jsonl
├── strategy_window_evaluations.jsonl
├── strategy_generalization_scores.jsonl
├── overfitting_warnings.jsonl
├── dataset_strategy_tournament_results.jsonl
├── dataset_strategy_tournament_summary.json
└── dataset_strategy_tournament_report.md
```

## Integration with Other Phases

| Phase | Role                                                         |
|-------|--------------------------------------------------------------|
| 41    | Read-Only Data Adapters — source of historical records       |
| 42    | Backtest Dataset Builder — produces the dataset folder input |
| 37    | Strategy Performance — optional comparison reports           |
| 40    | Market Fixtures — optional fixture quality context           |

## Live Trading Readiness

**Current readiness: 0/100**

This will not change until:
1. All Phase 43 gates are passed (zero critical warnings, strategy promoted)
2. Dataset quality >= 70/100 sustained across multiple runs
3. Human governance approval is explicitly granted
4. All other readiness gates (Phases 30–42) remain satisfied

## Limitations

- All evaluations are paper-only; no real PnL is guaranteed
- Signal quality depends entirely on dataset completeness
- Small samples (< 10 signals) produce unreliable scores
- This system cannot predict future XRPL market behavior
- Xahau hooks context is not supported and triggers a quality penalty
- Unsupported batch context triggers a quality penalty
