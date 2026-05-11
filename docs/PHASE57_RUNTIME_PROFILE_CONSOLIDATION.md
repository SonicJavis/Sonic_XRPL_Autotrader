# Phase 57: Runtime Profile Consolidation + App/V2 Drift Reduction

## Objective
Phase 57 adds a deterministic runtime-profile and conformance layer to reduce drift between:
- `app/` legacy FastAPI runtime surface, and
- canonical V2 modules under `src/sonic_xrpl/`.

This phase is architecture hardening only.

## Scope
- Add consolidated runtime profile models and profile mapping.
- Add conformance checks for fail-closed safety invariants.
- Add Phase 57 CLI commands:
  - `runtime-profile`
  - `runtime-profile-conformance`
  - `runtime-profile-report`
- Add deterministic Phase 57 reports under `reports/phase57/`.
- Add tests and fixtures for PASS/REVIEW/FAIL profile scenarios.

## Safety posture
Phase 57 does **not** add:
- live trading,
- signing,
- transaction submission,
- wallet-material handling,
- runtime mutation,
- dashboard mutation.

Phase 57 keeps:
- `paper_only=True`,
- `live_execution_allowed=False`,
- `runtime_mutation_allowed=False`,
- non-mutating conformance/report behavior.

## Runtime profile semantics
Canonical profile names:
- `offline`
- `paper`
- `shadow`
- `research`
- `unknown`

Conformance statuses:
- `PASS` for explicit safe evidence
- `REVIEW` for missing/inconclusive evidence
- `FAIL` for explicit unsafe evidence

## Outputs
Generated report files:
- `reports/phase57/latest_runtime_profile.json`
- `reports/phase57/latest_runtime_profile.md`
- `reports/phase57/latest_runtime_profile_conformance.json`
- `reports/phase57/latest_runtime_profile_conformance.md`

## Non-goals
Phase 57 does not unify runtime stacks into one executable path.
It provides a conformance contract and drift visibility to support later migration phases.
