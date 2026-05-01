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
