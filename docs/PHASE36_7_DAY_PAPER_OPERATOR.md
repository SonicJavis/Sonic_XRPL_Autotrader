# Phase 36: Integrated 7-Day Autonomous Paper Operator

## Objective
To provide a cohesive, deterministic state machine that consumes Discovery candidates, makes Paper Entry/Exit decisions according to strict safety rules, and generates performance history for the Phase 35 Paper Review system.

## Components
- **decision_policy.py**: Deterministic gating for paper_enter, paper_hold, paper_exit, paper_reject.
- **portfolio.py**: State machine tracking `PaperLedgerState` and `PaperPosition`.
- **paper_executor.py**: Evaluates a list of candidates against the current ledger state.
- **pipeline/cli.py**: End-to-end runner mapping discovery reports to output review.

## Safety Rules Enforced
- No live execution.
- No seeds or wallets.
- All decisions hash-based.
- Rejection on missing metadata or unvalidated ledger evidence.
