# Phase 44: Walk-Forward Backtest Replay Engine + Strategy Stability Tracking

## Overview

Phase 44 introduces a walk-forward backtest replay engine that evaluates strategy stability across rolling temporal windows derived from Phase 42 backtest datasets. It optionally integrates Phase 43 strategy tournament scores to compute per-window evaluation metrics, then aggregates them into stability profiles and lifecycle recommendations.

**Paper-only. No wallet. No signing. No submission. No live trading. 0/100 live readiness.**

---

## Module: `execution_prototype/walk_forward_replay/`

| File | Purpose |
|------|---------|
| `__init__.py` | Package exports |
| `models.py` | Immutable frozen dataclasses for all data structures |
| `loaders.py` | Read-only loaders for Phase 42 datasets and Phase 43 tournament output |
| `window_scheduler.py` | Builds chronological rolling walk-forward windows |
| `replay_engine.py` | Computes training/evaluation scores per strategy per window |
| `stability.py` | Aggregates per-window evaluations into stability profiles |
| `degradation.py` | Generates degradation and risk warnings |
| `lifecycle.py` | Maps profiles + warnings to paper lifecycle recommendations |
| `report_writer.py` | Writes all outputs to `reports/phase44/<timestamp>/` |
| `cli.py` | CLI entry point |

---

## Data Models

### `WalkForwardWindow`
Describes one rolling train/eval window pair built from Phase 42 backtest windows.
- `walk_window_id`: sha256-based deterministic ID
- `training_window_ids`: IDs of Phase 42 windows used for training
- `evaluation_window_id`: ID of Phase 42 window used for evaluation
- `training_ledger_range`, `evaluation_ledger_range`: `[min, max]`
- `chronological_order`: position in the rolling sequence

### `WalkForwardEvaluation`
Per-strategy evaluation on one walk-forward window.
- `training_score`: mean of prior evaluation scores (or dataset quality fallback)
- `evaluation_score`: Phase 43 tournament score for eval window (or dataset quality fallback)
- `score_delta`: `evaluation_score - training_score`
- Rates stored as strings: `unknown_outcome_rate`, `metadata_backed_rate`, `liquidity_backed_rate`

### `StrategyStabilityProfile`
Aggregated stability metrics across all walk-forward windows for a strategy.
- `stability_score`: 0–100, with caps:
  - `≤ 40` if future leakage detected
  - `≤ 50` if dataset quality < 50
  - `≤ 60` if unsupported Batch or Xahau/Hook context
- `stability_band`: `stable` (≥75) | `watch` (50–74) | `unstable` (<50) | `insufficient_data`
- `confidence_band`: `low` (<3 windows) | `medium` (3–5) | `high` (≥6)

### `StrategyDegradationWarning`
Warning types detected:
1. `rolling_score_decay` — score declining over time
2. `evaluation_collapse` — score drops below critical threshold
3. `volatility_spike` — high score variance
4. `metadata_dependency` — low metadata-backed rate
5. `liquidity_dependency` — low liquidity-backed rate
6. `unknown_outcome_dependency` — high unknown outcome rate
7. `sample_size_fragility` — small evaluation samples
8. `dataset_quality_dependency` — low dataset quality score
9. `regime_shift_sensitive` — large first/second-half score spread
10. `phase43_overfit_dependency` — high Phase 43 overfitting score
11. `future_leakage_dependency` — future leakage in dataset (critical)
12. `unsupported_protocol_context` — Batch/Xahau/Hook context detected (critical)

### `PaperStrategyLifecycleRecommendation`
Lifecycle statuses:
- `continue_paper_testing` — stable, low warnings
- `increase_paper_scrutiny` — watch band or degradation warnings
- `pause_paper_testing` — unstable or multiple critical warnings
- `retire_from_current_paper_pool` — future leakage or unsupported Batch context
- `insufficient_data` — fewer than 2 evaluated windows

**Always includes `required_human_action` and `prohibited_live_action`.**

### `WalkForwardReplaySummary`
Top-level summary with `live_trading_readiness: "0/100"` always.

---

## CLI Usage

```bash
python -m execution_prototype.walk_forward_replay.cli \
  --dataset /path/to/phase42/dataset \
  --phase43-report /path/to/phase43/report \
  --output-dir ./reports \
  --min-training-windows 1 \
  --evaluation-window-size 1 \
  --step-size 1 \
  --min-sample-size 5 \
  --max-score-drop-warning -15 \
  --max-score-drop-critical -30
```

Options:
- `--dry-run`: compute without writing output files
- `--strict`: exit code 1 if any critical warnings
- `--help`: show all options

---

## Output Files

Written to `reports/phase44/<timestamp>/`:

| File | Description |
|------|-------------|
| `walk_forward_windows.jsonl` | All walk-forward windows |
| `walk_forward_evaluations.jsonl` | Per-strategy per-window evaluations |
| `strategy_stability_profiles.jsonl` | Aggregated stability profiles |
| `strategy_degradation_warnings.jsonl` | All degradation warnings |
| `paper_strategy_lifecycle_recommendations.jsonl` | Lifecycle recommendations |
| `walk_forward_replay_summary.json` | Top-level summary |
| `walk_forward_replay_report.md` | Human-readable markdown report |

---

## Deterministic IDs

All IDs use `sha256(json.dumps(data, sort_keys=True))[:16]` for reproducibility.

---

## Safety Posture

- No network calls
- No wallet handling, seed handling, signing, or transaction submission
- No Xaman payload creation
- No XRPL transaction submission
- No autofill or submitAndWait
- No live buy/sell or order placement
- No auto-calibration or model mutation
- No Batch transaction support
- No Hooks/Xahau execution support
- `live_trading_readiness` is always `"0/100"`
- All lifecycle statuses are paper-only

---

## Integration with Prior Phases

- **Requires**: Phase 42 Backtest Dataset Builder output (`backtest_windows.jsonl`, `dataset_manifest.json`)
- **Optional**: Phase 43 Dataset-Driven Strategy Tournament output for per-strategy per-window scores
- **Adds to**: Phase 39 Campaign Dashboard (optional panel if `reports/phase44/` exists)

---

## Testing

```bash
python -m pytest execution_prototype/tests/test_walk_forward_replay.py -v
```

28 tests covering:
- Deterministic ID generation
- Source file immutability
- Append-only output
- Chronological window ordering
- No future leakage into training
- Evaluation score drop warnings
- Rolling decay detection
- Unknown outcome dependency
- Confidence band caps
- Stability caps (leakage, batch, Xahau)
- Paper-only lifecycle statuses
- Live readiness = 0/100
- CLI dry run and help
