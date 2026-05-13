# Migration-Safe Control Checks Policy

## Phase 58C policy status

- Phase 58C implements migration-safe control checks only.
- Phase 58C does not perform runtime migration.
- Phase 58C does not change runtime ownership.
- Phase 58C does not authorize live trading.

## Runtime surface ownership (unchanged)

| Surface | Role | Status |
|---|---|---|
| `app/` | Current runnable legacy API/paper runtime | Unchanged; not migrated here |
| `src/sonic_xrpl/` | Canonical future runtime target | Unchanged; not activated as entrypoint here |
| `execution_prototype/` | Historical/reference-only | Unchanged |

`app/` remains the current runnable legacy API/paper runtime surface.
`src/sonic_xrpl/` remains the canonical future runtime target; it is not the active runtime entrypoint after Phase 58C.
`execution_prototype/` remains historical/reference-only.

## Migration blocking rule

Any future app-to-V2 migration requires:

1. Explicit future phase approval — migration may not be performed in policy/docs/check phases.
2. Migration must be blocked if any of the following capabilities is added prematurely:
   - live transaction signing
   - live transaction submission
   - transaction autofill
   - wallet seed/private-key handling
   - Xaman payload creation
   - FirstLedger live ingestion
3. Migration requires all five gate categories satisfied:
   - **parity gates** — every runtime capability of `app/` is replicated in `src/sonic_xrpl/`
   - **safety gates** — all existing safety/audit/scan checks pass on the new surface
   - **rollback gates** — a documented rollback plan for runtime cutover exists
   - **docs gates** — policy docs updated and peer-reviewed
   - **audit gates** — independent audit of live-execution boundary before cutover

## Runtime cutover vs. migration readiness

Runtime cutover is separate from migration readiness.
Migration readiness means gates have been satisfied; runtime cutover still requires an explicit additional approval step.

## Live enablement vs. runtime migration

Live enablement is separate from runtime migration.
Runtime migration between `app/` and `src/sonic_xrpl/` does not itself authorize live execution.
Live execution remains blocked until a dedicated future live-enablement phase is approved.

## Migration-safe invariants enforced by script

`scripts/migration_safe_check.py` checks the following invariants deterministically:

1. `docs/MIGRATION_SAFE_CONTROL_CHECKS.md` (this file) exists.
2. `docs/MIGRATION_READINESS_MATRIX.md` exists.
3. `docs/LIVE_READINESS_POLICY.md` exists.
4. `docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md` exists.
5. `app/main.py` is present (app/ runtime not deleted).
6. `src/sonic_xrpl/cli/main.py` is present (V2 CLI not deleted).
7. `execution_prototype/README.md` is present (prototype not deleted).
8. `src/sonic_xrpl/execution/live_guard.py` is present (live guard not deleted).
9. `app/execution/execution_guard.py` is present (execution guard not deleted).
10. Required migration-safety phrases are present in key docs.
11. Prohibited live-authorization phrases are absent from key docs.

## Safety continuity statement

Phase 58C introduces no runtime behavior changes.
All existing fail-closed safety boundaries remain authoritative.
Live trading remains blocked after Phase 58C.

## Phase 58C summary

- migration-safe control policy exists: ✓ (this file)
- migration readiness matrix exists: `docs/MIGRATION_READINESS_MATRIX.md`
- migration-safe check script exists: `scripts/migration_safe_check.py`
- migration-safe check tests exist: `tests/safety/test_migration_safe_check.py`
- CI/safety integration: `.github/workflows/safety-gate.yml`
- docs-check registration: `src/sonic_xrpl/audit/docs_check.py`
- guard-critical registration: `scripts/guard_critical_changes.py`
- still no live execution: confirmed
