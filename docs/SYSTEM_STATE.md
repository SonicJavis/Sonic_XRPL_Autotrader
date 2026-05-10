# System State

## Migration Surface Classification

This repository currently has three meaningful surfaces. This classification is
for docs-first migration planning only and does not resolve the future canonical
runtime path.

| Surface | Evidence | Current classification | Canonical-path status |
|---|---|---|---|
| `app/` | `app/main.py`, `app/execution/pipeline.py`, `app/execution/execution_guard.py` | Current runnable FastAPI/paper-runtime surface | Not declared future canonical in this document |
| `execution_prototype/` | `execution_prototype/README.md`, `execution_prototype/reconciliation/`, `execution_prototype/walk_forward_replay/` | Historical/prototype/offline workflow surface | Reference-only unless a named bridge or test uses it |
| `src/sonic_xrpl/` | `docs/PROJECT_BLUEPRINT.md`, `docs/V2_ARCHITECTURE.md`, `src/sonic_xrpl/` | V2 governance/offline architecture surface introduced in Phase 45+ | Not declared runnable API replacement in this document |

The canonical-path decision remains intentionally unresolved. Runtime behavior,
live execution, sniper-style execution, and safety guards must not be changed by
this classification.

## Active Phases

- **Phase 56**: Approved Calibration Change Implementation Plan + Dry-Run Patch Pack (repo evidence exists; outside the requested Phase 1-55 migration timeline).
- **Phase 55**: Human Review Approval Ledger + Calibration Change Request Workflow.
- **Phase 54**: Human-Reviewed Calibration Proposal Pack.
- **Phase 53**: Calibration Readiness Review + Non-Mutating Threshold Recommendation Layer.
- **Phase 52**: Source-Backed Paper Observation Dataset Expansion + Outcome Replay Corpus.
- **Phase 51**: Paper Outcome Attribution + Signal Feedback Loop.
- **Phase 50**: Signal Review Workflow.
- **Phase 49**: Evidence-Backed FirstLedger Candidate Risk + Strategy Signal Contracts.
- **Phase 48**: Accurate FirstLedger Discovery Boundary + Dependency Audit / Supply-Chain Guardrails.
- **Phase 45**: V2 Foundation Architecture Rebuild.
- **Phase 44**: Walk-Forward Backtest Replay Engine + Strategy Stability Tracking.
- **Phase 43**: Dataset-Driven Strategy Tournament.
- **Phase 42**: Historical Backtest Dataset Builder.
- **Phase 41**: Read-Only Historical Data Collection Adapter.
- **Phase 40**: Historical Market Fixture Engine + Paper Mark-to-Market Enrichment.
- **Phase 39**: Operator Trust Dashboard + 7-Day Paper Campaign Runner.
- **Phase 38**: Risk Governor and Operator Trust Layer.
- **Phase 37**: Strategy Performance Engine + Backtest Tournament.
- **Phase 36**: Integrated 7-Day Autonomous PAPER Trading Operator.
- **Phase 35**: Paper Review Layer.
- **Phase 34**: XRPL Meme Discovery Engine.
- **Phase 33**: Drift Intelligence and Early Warning.
- **Phase 32**: CI/CD Safety Hardening.
- **Phase 31**: Human-Guided Calibration Recommendations.
- **Phase 30**: Simulation vs Reality Reconciliation.
- **Phase 1-29**: Core Read-Only Abstractions, with several missing or partial phase artifacts listed below.

## Phase Evidence Status

The docs-first migration inventory classifies Phase evidence as follows:

- **Verified**: Phases 3-10, 18, and 30-55 have direct docs, code, tests,
  reports, or scripts in the repository.
- **Partial**: Phase 19 is test-evidenced only; Phase 20 is represented by
  `PHASE_20_1_VALIDATION_HARDENING_AUDIT.md`; Phase 23 is fixture/test-evidenced;
  Phase 26 is test-evidenced only.
- **Missing/unclear**: Phases 1-2, 11-17, 21-22, 24-25, and 27-29 have no direct
  phase artifact found in the repository.

Phase 56 artifacts exist in the repository, including
`docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md` and
`src/sonic_xrpl/calibration_implementation_plan/`. They are treated as existing
repo evidence and a continuation after Phase 55, but outside the requested
Phase 1-55 migration timeline.

## Capability Summary

The repository contains consolidated legacy/prototype code for Phases 30 through
44 and V2 governance/offline code for Phases 45 through 55. The system is
strictly **paper-only**. Live trading readiness remains at **0/100**, and live
trading is completely forbidden. The dashboard is entirely read-only. The
campaign runner is manual-cycle only; there is no hidden offline daemon or
continuous interval_scan loop in the documented migration scope.

Phase 44 adds walk-forward backtest replay: rolling train/eval windows from
Phase 42 datasets, per-strategy evaluation scores, stability profiles,
degradation warnings, and paper lifecycle recommendations. It never produces
live trading authorization.

Phase 55 adds the offline human review approval ledger under
`src/sonic_xrpl/calibration_approval/`. It creates governance artifacts only and
does not apply calibration changes, mutate runtime thresholds, or enable live
execution.

## Safety Posture

- **Fail-Closed Execution**: The documented safety posture remains fail-closed.
  The safety references for this migration are `app/execution/execution_guard.py`,
  `src/sonic_xrpl/execution/live_guard.py`, `scripts/safety_grep.py`, and
  `src/sonic_xrpl/audit/safety_scan.py`.
- **Paper-only and non-mutating governance**: Phase 53-55 governance artifacts
  are offline, paper-only, and non-mutating.
- **Canonical path unresolved**: This document does not authorize runtime
  migration, live execution, sniper-style execution, wallet handling, signing,
  transaction submission, or safety scanner weakening.

## Current Readiness

- Live Trading: 0/100
- Paper Trading Autonomy: Available through historical/prototype and paper-only
  workflows; future canonical runtime path is unresolved.

## Legacy Branch Warning

The legacy scaffold branch `copilot/create-project-scaffold` is historical only
and contains unsafe wallet/signing code; do not merge it.
