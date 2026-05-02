# Paper Autonomy Test Plan

## Objective
To validate the 7-day autonomous paper trading integration from Phase 36.

## Pre-Requisites
- Mock price feeds available.
- `discovery` module populated with mock fixture candidates.
- `safety_grep.py` passing on `execution_prototype`.

## Execution
1. Run `python -m execution_prototype.pipeline.cli --discovery-report data/discovery_mock --output-dir out/paper_test --duration-days 7 --run-review`
2. Verify `out/paper_test/paper_decisions.jsonl` contains deterministic output hashes.
3. Verify `out/paper_test/paper_ledger_state.json` reflects PnL.
4. Verify `out/paper_test/paper_trade_history.jsonl` contains exited trades.
5. Review the generated `paper_lessons_learned.md` in the output timestamp folder.

## Constraints
- The test must not trigger live API connections.
- The output files must be append-only.

## Phase 37, 38 & 39 Extensions
- Run strategy performance tournaments on offline mock fixtures.
- Evaluate the Operator Trust Score deterministically.
- Verify `allow_paper` or `halt_paper` conditions mathematically.
- Aggregate all state to `campaign_dashboard_data.json`.
- Visualize via Phase 39 Streamlit operator dashboard.
- Enrich paper positions with Phase 40 Historical Market Fixtures (Mark-to-Market).
- Collect and normalize historical fixtures via Phase 41 Read-Only Adapters.
- Run Phase 43 Dataset Strategy Tournament on Phase 42 dataset output.
- Verify all 6 strategy families are evaluated across train/validation/test windows.
- Confirm overfitting warnings are generated for degraded strategies.
- Confirm live_trading_readiness remains "0/100" in all tournament summaries.
- Verify promotion decisions require human approval and are paper-only.

## Phase 44 Walk-Forward Replay Extensions
- Run walk-forward replay on Phase 42 dataset output with Phase 43 scores as input.
- Verify rolling windows are strictly chronological (no future leakage into training).
- Confirm degradation warnings are generated for score drops below threshold.
- Verify stability caps: future leakage ≤40, low quality ≤50, Batch/Xahau ≤60.
- Confirm all lifecycle statuses are paper-only and live_trading_readiness remains 0/100.
