# Migration Readiness Matrix

## Purpose

This matrix provides a deterministic, surface-by-surface view of migration
readiness for the eventual app-to-V2 ownership migration.

**No runtime cutover is performed here.**
**Live execution is not authorized here.**
**Migration status is blocked/not-started for all surfaces unless explicitly
stated otherwise by a named future phase.**

All rows use the following status vocabulary:

- **current owner** — which runtime surface owns this capability today
- **future owner** — which surface is the declared future canonical target
- **current status** — what exists and is runnable today
- **migration status** — whether migration work has started; default is BLOCKED/NOT-STARTED
- **cutover status** — whether runtime cutover has happened; always NOT-CUTOVER unless stated
- **blocker status** — whether a known blocker prevents this row from migrating

---

## Matrix

| Surface | Current Owner | Future Owner | Current Status | Migration Status | Required Parity Evidence | Required Safety Evidence | Required Tests | Cutover Status | Blocker Status | Rollback Requirement |
|---|---|---|---|---|---|---|---|---|---|---|
| config | `app/` | `src/sonic_xrpl/` | `app/core/config.py` + env-based config runnable | BLOCKED/NOT-STARTED | V2 config module with equivalent fields | safety scan passes; no secrets in config | config tests pass in V2 | NOT-CUTOVER | missing V2 config parity | revert merge commit; no DB migration needed |
| API entrypoint | `app/` | `src/sonic_xrpl/` | `app/main.py` — FastAPI app running | BLOCKED/NOT-STARTED | V2 equivalent entrypoint with same route contracts | execution guard; live guard; no submission path | V2 API contract tests pass | NOT-CUTOVER | no V2 FastAPI entrypoint exists | revert merge commit; restore app/main.py |
| paper execution | `app/` | `src/sonic_xrpl/` | `app/execution/pipeline.py` — paper-only execution pipeline | BLOCKED/NOT-STARTED | V2 paper execution module with equivalent trade-gate logic | execution guard present and fail-closed; no signing/submission | paper execution tests pass in V2 | NOT-CUTOVER | no V2 paper execution module | revert merge commit; restore app execution pipeline |
| execution guards | `app/` + `src/sonic_xrpl/` | `src/sonic_xrpl/` | `app/execution/execution_guard.py` and `src/sonic_xrpl/execution/live_guard.py` both present | BLOCKED/NOT-STARTED | V2 live_guard covers all app guard capabilities | both guards must remain present and pass tests | guard tests pass (test_execution_guard.py, unit/test_live_guard.py) | NOT-CUTOVER | parity evidence required before any guard migration | never remove either guard until parity verified and approved |
| runtime profile | `src/sonic_xrpl/` | `src/sonic_xrpl/` | `src/sonic_xrpl/runtime_profile/` — conformance/reporting layer only | N/A (already in V2 surface) | runtime profile must reflect app surface faithfully | conformance report passes; no live flags | runtime profile tests pass (test_phase57_*) | NOT-CUTOVER | runtime profile is conformance-only; no cutover needed | N/A |
| audit/safety checks | `scripts/` + `src/sonic_xrpl/audit/` | `src/sonic_xrpl/audit/` | `scripts/safety_grep.py`, `scripts/audit_validator.py`, `src/sonic_xrpl/audit/safety_scan.py`, `src/sonic_xrpl/audit/docs_check.py` | BLOCKED/NOT-STARTED | V2 audit module covers all script audit capabilities | all safety checks pass | audit/safety tests pass | NOT-CUTOVER | script layer must not be removed until V2 audit parity verified | restore scripts; revert merge commit |
| dashboard | `dashboard/` | TBD | `dashboard/streamlit_app.py` — operator dashboard | BLOCKED/NOT-STARTED | V2 equivalent dashboard or explicit deprecation decision | no live execution triggers in dashboard | dashboard import tests pass | NOT-CUTOVER | no V2 dashboard defined | revert merge commit; restore dashboard/ |
| FirstLedger signal contracts | `src/sonic_xrpl/signals/` | `src/sonic_xrpl/signals/` | fixture/source-backed signal models only; no live adapter | N/A (already in V2 surface) | future live adapter requires explicit phase approval | `live_execution_allowed=False` enforced; no live FirstLedger adapter | signal safety tests pass | NOT-CUTOVER | live adapter blocked by FirstLedger ingestion policy | revert any live-adapter addition; restore fixture-only constraint |
| Xaman future policy | None (future only) | `src/sonic_xrpl/` (future) | no Xaman payload implementation exists | BLOCKED/NOT-STARTED | design spec required before any implementation; see XAMAN_FUTURE_INTEGRATION_POLICY.md | no signing/submission/autofill in any Xaman code path | N/A until implementation starts | NOT-CUTOVER | Xaman integration is future/manual-approval-only | N/A |
| dependency audit | `scripts/` | `scripts/` | `scripts/dependency_audit.py` — pip check + pip-audit + xrpl.js detection | N/A (scripts layer, not runtime surface) | N/A | dependency audit passes clean | dependency audit tests pass | NOT-CUTOVER | N/A | N/A |
| telemetry/logging | `app/` | `src/sonic_xrpl/` (future) | basic app logging; no structured telemetry layer | BLOCKED/NOT-STARTED | V2 telemetry module with equivalent observable fields | no PII; no credential leak in logs | telemetry tests pass in V2 | NOT-CUTOVER | no V2 telemetry module defined | revert merge commit; restore app logging |
| storage/database | `app/` | TBD | SQLModel/SQLite paper trade storage in app | BLOCKED/NOT-STARTED | V2 equivalent storage contracts or explicit migration plan | no live trade records stored without operator review | storage tests pass | NOT-CUTOVER | no V2 storage module defined | revert merge commit; restore app storage |
| CLI | `src/sonic_xrpl/cli/` | `src/sonic_xrpl/cli/` | `src/sonic_xrpl/cli/main.py` — V2 CLI (offline/paper commands) | N/A (already canonical) | CLI must cover all required V2 command surfaces | CLI cannot expose live execution commands without safety gates | CLI smoke tests pass | NOT-CUTOVER | CLI is already in canonical surface; no cutover needed | N/A |
| docs/checks | `docs/` + `src/sonic_xrpl/audit/docs_check.py` | `src/sonic_xrpl/audit/docs_check.py` | docs check enforces required doc list | N/A (already in V2 surface) | docs check must cover all migration-safety docs | docs check fails CI if required docs missing | docs check tests pass | NOT-CUTOVER | N/A | N/A |
| CI workflows | `.github/workflows/` | `.github/workflows/` | ci.yml, safety-gate.yml, audit-gate.yml, test-gate.yml | N/A (already canonical; shared) | all migration-safety checks integrated into CI | all safety/audit/migration-check steps pass | CI passes end-to-end | NOT-CUTOVER | N/A | restore workflow files from git history |

---

## Summary

- **No row has cutover status other than NOT-CUTOVER.**
- **No row has migration status other than BLOCKED/NOT-STARTED or N/A (already canonical).**
- **Live execution is not authorized by any row.**
- **`execution_prototype/` remains historical/reference-only; no row grants it runtime authority.**
- **Migration requires all five gate categories: parity, safety, rollback, docs, audit.**
- **This matrix is reviewed and updated by each future migration phase.**
