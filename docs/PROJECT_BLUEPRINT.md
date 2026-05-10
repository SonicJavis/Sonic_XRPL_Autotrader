# Project Blueprint — Sonic XRPL Autotrader V2

**Version**: 2.0.0-alpha  
**Phase**: 45 — V2 Foundation Architecture Rebuild  
**Date**: 2026-05-02

---

## Purpose

The Sonic XRPL Autotrader is a research, simulation, and eventual paper-trading system
for XRPL-native assets (XRP, issued currencies, AMM pools, MPTs).

**What it is**:
- A protocol-aware market analysis tool
- A deterministic simulation engine for XRPL trading strategies
- A paper trading sandbox for offline strategy validation
- A safety-first research platform with explicit runtime mode controls

**What it is NOT** (in Phase 45 and until Phase 57 security review):
- A live trading system
- A wallet management system
- A transaction signing or submission system

---

## V2 Architecture Summary

V2 introduces a clean layered architecture under `src/sonic_xrpl/`:

```
src/sonic_xrpl/
  core/           — Configuration, modes, errors, IDs, events
  protocol/       — XRPL protocol model (amendments, XLS, capabilities, assets)
  providers/      — Abstract provider interfaces (rippled, Clio, mocks)
  ingestion/      — Fixture loading and data ingestion
  intelligence/   — Token profiling, confidence scoring (read-only)
  strategy/       — Signal generation (no execution)
  outcomes/       — Paper outcome attribution and advisory feedback
  outcome_corpus/ — Paper observation replay corpus and quality reports
  calibration_review/ — Non-mutating calibration readiness review
  calibration_proposal/ — Human-reviewed proposal packs only
  risk/           — Risk policy, pre-trade checks, circuit breakers
  simulation/     — Fill models, slippage, fees, latency (deterministic)
  execution/      — Intent, plan, lifecycle, live_guard, paper_executor
  reconciliation/ — V2 reconciliation + Phase 30 bridge adapter
  telemetry/      — Metrics, health, audit log
  storage/        — SQLite-backed storage
  cli/            — Offline CLI (health, audit, capabilities, safety-scan, simulate)
  audit/          — V2 audit validator, safety scanner, docs/module/test checks
  compatibility/  — Legacy import wrappers and execution_prototype bridge
```

---

## Legacy-to-V2 Mapping

| Legacy | V2 Equivalent | Treatment |
|--------|--------------|-----------|
| `execution_prototype/reconciliation/` | `src/sonic_xrpl/reconciliation/legacy_phase30_adapter.py` | Bridge adapter — legacy preserved |
| `execution_prototype/walk_forward_replay/` | Untouched | Phase 44 CLI works unchanged |
| `scripts/safety_grep.py` | `src/sonic_xrpl/audit/safety_scan.py` | Both coexist — V2 adds classification |
| `scripts/audit_validator.py` | Extended with V2 checks | Narrowly extended |
| `app/` | Not migrated in Phase 45 | Legacy preserved |
| `dashboard/` | Not migrated in Phase 45 | Legacy preserved |

---

## Runtime Modes

| Mode | Intent | Simulate | Paper | Submit |
|------|--------|----------|-------|--------|
| intelligence_only | ❌ | ❌ | ❌ | ❌ |
| research | ❌ | ❌ | ❌ | ❌ |
| simulation | ✅ | ✅ | ❌ | ❌ |
| paper | ✅ | ❌ | ✅ | ❌ |
| live_readiness | ❌ | ❌ | ❌ | ❌ |
| live | N/A | N/A | N/A | BLOCKED |

**Default mode**: `intelligence_only`

---

## Safety Model

1. `execution/live_guard.py` — Primary safety gate. All submission paths raise `LiveTradingDisabledError`.
2. `ExecutionPlan.live_submission_allowed` — Hardcoded `False`. Cannot be set to `True` in Phase 45.
3. `ModeContext.can_submit()` — Always returns `False`.
4. `MockSubmissionProvider.submit()` — Always raises `LiveTradingDisabledError`.
5. `scripts/safety_grep.py` — Scans runtime code for forbidden patterns.
6. `src/sonic_xrpl/audit/safety_scan.py` — V2 scanner with classification.

---

## Provider Model

```
LedgerProvider (read-only current state)
  → MockLedgerProvider (offline testing)
  → FixtureLedgerProvider (fixture-backed testing)
  → Future: XRPLRippledProvider (Phase 46)

HistoricalProvider (Clio-backed read-only history)
  → MockHistoricalProvider (offline testing)
  → Future: ClioProvider (Phase 46)

SubmissionProvider (BLOCKED — interface only)
  → MockSubmissionProvider (always raises LiveTradingDisabledError)
```

---

## Protocol Capability Model

Capabilities are tracked in `src/sonic_xrpl/protocol/`:

- `amendments.py` — Known amendments with status (ENABLED/FEATURE_GATED/OBSOLETE/RESEARCH_ONLY)
- `xls_registry.py` — XLS standard metadata
- `feature_gates.py` — `require_feature()` and `is_feature_enabled()` checks
- `capability_matrix.py` — Central matrix derived from amendments registry

**Architecture Rule #1**: No module may use an amendment-dependent feature without checking `capability_matrix.py`.

---

## Test Model

- `tests/unit/` — Unit tests for all V2 modules (offline, deterministic)
- `tests/safety/` — Safety scan and classification tests
- `tests/smoke/` — CLI smoke tests and import smoke tests
- `execution_prototype/tests/` — Legacy Phase 30+ tests (preserved)

All tests run offline. No network access required.

---

## Audit Model

- `src/sonic_xrpl/audit/validator.py` — Full V2 audit with 15 check categories
- `src/sonic_xrpl/audit/safety_scan.py` — Pattern classification scanner
- `src/sonic_xrpl/audit/docs_check.py` — Required docs verification
- `src/sonic_xrpl/audit/dependency_check.py` — Compromised xrpl.js version check
- `src/sonic_xrpl/audit/phase_check.py` — Phase evidence verification
- `src/sonic_xrpl/audit/architecture_check.py` — Package structure verification

Output: `docs/audit/latest_audit_report.{md,json}`

---

## Roadmap

See `docs/ROADMAP.md` for full phase roadmap.

## Phase 49 blueprint addendum

The project now includes a Phase 49 signal/evidence layer for FirstLedger candidate risk review. This layer prepares future simulation and paper-review workflows by producing deterministic, explainable, non-executing signals. It preserves source provenance, missing-data limitations, and the live execution boundary.

## Phase 51 blueprint addendum

Phase 51 adds an offline paper outcome attribution layer under `src/sonic_xrpl/outcomes/`. It links local paper observations back to Phase 49 signal records, emits explicit `NO_OBSERVATION` outcomes when evidence is missing, and aggregates advisory feedback without changing strategy scoring automatically.

## Phase 52 blueprint addendum

Phase 52 adds an offline outcome replay corpus layer under `src/sonic_xrpl/outcome_corpus/`. It expands deterministic paper observation fixtures, models missing windows and missing fields explicitly, labels synthetic evidence, scores corpus quality conservatively, and writes replay corpus reports. It prepares Phase 53 calibration review but does not perform calibration or enable live execution.

## Phase 53 blueprint addendum

Phase 53 adds an offline calibration readiness layer under `src/sonic_xrpl/calibration_review/`. It reviews paper-only Phase 49-52 evidence, applies conservative readiness rules, and emits non-mutating human-review-only recommendations. It does not apply calibration, does not alter thresholds, and does not enable live execution.

## Phase 54 blueprint addendum

Phase 54 adds an offline calibration proposal layer under `src/sonic_xrpl/calibration_proposal/`. It packages Phase 53 recommendations into deterministic before/after proposal records or blocked recommendation records for human review. It does not apply proposals, does not change runtime settings, and does not enable live execution.

## Phase 55 blueprint addendum

Phase 55 adds an offline human-review approval layer under `src/sonic_xrpl/calibration_approval/`. It consumes Phase 54 proposal packs plus review fixtures, then writes deterministic approval-ledger and change-request records for governance. It does not apply approved values, does not change runtime settings, and does not enable live execution.
