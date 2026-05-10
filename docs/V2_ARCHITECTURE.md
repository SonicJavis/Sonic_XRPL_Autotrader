# V2 Architecture

**Version**: 2.0.0-alpha  
**Phase**: 45

---

## Canonical Path Decision: Pending

The repository has not resolved which surface is the future canonical runtime
path. No runtime migration or sniper/live work until this decision is resolved +
PR 4 safety tests pass.

### Runtime Surface Options

| Option | Description | Current status |
|--------|-------------|----------------|
| Option A | Keep `app/` as canonical runtime | Unresolved |
| Option B | Promote `src/sonic_xrpl/` to future canonical runtime | Unresolved |
| Option C | Adapter hybrid (`app/` API shell + V2 domain logic) | Unresolved |

### Facts vs Inference

| Type | Statement | Evidence |
|------|-----------|----------|
| Fact | `app/main.py` is current runnable API. | `README.md` documents `python -m app.main`; `ARCHITECTURE.md` documents the `app/` API and paper pipeline. |
| Fact | `src/sonic_xrpl/` is V2 governance/offline stack. | This document and `docs/PROJECT_BLUEPRINT.md` describe V2 modules, offline audit, calibration, proposal, approval, and implementation-planning layers under `src/sonic_xrpl/`. |
| Inference | `src/sonic_xrpl/` is likely the future target because it contains the Phase 45+ governance/offline architecture. | This is not yet a runtime-canonical decision and must not be treated as implementation authority until the decision is resolved. |

The safety references remain authoritative while this decision is pending:
`app/execution/execution_guard.py`, `src/sonic_xrpl/execution/live_guard.py`,
`scripts/safety_grep.py`, and `src/sonic_xrpl/audit/safety_scan.py`.

### Legacy Surface Freeze (Pending Decision)

- `app/` is the current runnable legacy API/paper runtime surface.
- `execution_prototype/` is historical/reference-only unless used by named
  tests or bridge adapters.
- No new features may be added to `app/` or `execution_prototype/` until the
  canonical-path decision is resolved and required safety conformance tests pass.

---

## Package Tree

```
src/sonic_xrpl/
├── __init__.py                         # Package root — version 2.0.0-alpha
├── core/
│   ├── config.py                       # V2Config with safe offline defaults
│   ├── modes.py                        # RuntimeMode enum, ModeContext, DEFAULT_MODE
│   ├── errors.py                       # Error hierarchy
│   ├── result.py                       # Generic Result[T] type
│   ├── events.py                       # SystemEvent, EventType, Severity
│   └── ids.py                          # new_id(), deterministic_id()
├── protocol/
│   ├── networks.py                     # XRPLNetwork enum and configs
│   ├── amendments.py                   # Amendment registry with status
│   ├── xls_registry.py                 # XLS standard metadata
│   ├── feature_gates.py                # require_feature(), is_feature_enabled()
│   ├── capability_matrix.py            # Central capability matrix
│   ├── ledger_truth.py                 # LedgerTruth, is_validated_ledger()
│   └── assets.py                       # XRPAmount, IssuedCurrency, MPToken
├── providers/
│   ├── base.py                         # LedgerProvider, HistoricalProvider, SubmissionProvider (abstract)
│   ├── health.py                       # ProviderHealth, check_provider_health()
│   ├── failover.py                     # FailoverProvider (multi-provider fallback)
│   ├── mocks.py                        # MockLedgerProvider, MockHistoricalProvider, MockSubmissionProvider
│   └── fixture_ledger.py               # FixtureLedgerProvider (JSON fixture-backed)
├── ingestion/
│   └── fixtures.py                     # load_fixture(), list_fixtures()
├── intelligence/
│   ├── token_profile.py                # TokenProfile, build_token_profile(), risk flags
│   └── confidence.py                   # ConfidenceScore, compute_confidence()
├── strategy/
│   ├── base.py                         # BaseStrategy (abstract)
│   ├── signals.py                      # Signal, SignalType
│   └── registry.py                     # StrategyRegistry, get_global_registry()
├── risk/
│   ├── policy.py                       # RiskPolicy, DEFAULT_RISK_POLICY
│   ├── pretrade_checks.py              # run_pretrade_checks(), PreTradeCheckResult
│   └── circuit_breakers.py             # CircuitBreaker, check_circuit_breakers()
├── simulation/
│   ├── fill_model.py                   # FillModelType, estimate_fill(), FillEstimate
│   ├── slippage.py                     # estimate_slippage(), SlippageEstimate
│   ├── fees.py                         # estimate_fee(), FeeEstimate, BASE_FEE_DROPS=12
│   └── latency.py                      # estimate_latency(), LatencyEstimate
├── execution/
│   ├── live_guard.py                   # THE SAFETY GATE — all submission blocked here
│   ├── intent.py                       # ExecutionIntent, IntentStatus
│   ├── plan.py                         # ExecutionPlan (live_submission_allowed always False)
│   ├── lifecycle.py                    # LifecycleLog (append-only), LifecycleEvent
│   └── paper_executor.py               # PaperExecutor, PaperExecutionRecord
├── reconciliation/
│   ├── models.py                       # V2SimulationRecord, V2OutcomeRecord, V2ReconciliationRecord
│   ├── comparator.py                   # reconcile_v2()
│   └── legacy_phase30_adapter.py       # Phase 30 bridge — LEGACY_AVAILABLE flag
├── telemetry/
│   ├── metrics.py                      # record_metric(), get_all_metrics()
│   ├── health.py                       # SystemHealth, get_system_health()
│   └── audit_log.py                    # AuditLog (append-only), AuditEntry
├── storage/
│   ├── models.py                       # StoredRecord
│   └── sqlite.py                       # SQLiteStore (stdlib sqlite3)
├── cli/
│   └── main.py                         # CLI: health, audit, capabilities, safety-scan, simulate, reconcile, market-snapshot
├── market/
│   ├── __init__.py                     # Package root
│   ├── models.py                       # Frozen dataclasses: MarketSnapshot, AssetSnapshot, AMMSnapshot, etc.
│   ├── snapshot_builder.py             # build_market_snapshot() — main orchestrator
│   ├── amm_snapshot.py                 # AMMSnapshot builder with capability check
│   ├── orderbook_snapshot.py           # OrderbookSnapshot builder
│   ├── account_context.py              # AccountContext builder
│   ├── trustline_context.py            # TrustlineContext builder (NoRipple, freeze, clawback)
│   ├── mpt_snapshot.py                 # MPTSnapshot builder with MPTokensV1 capability check
│   ├── metadata_signals.py             # MetadataSignal extraction from Phase 46 parsers
│   ├── quality.py                      # SnapshotQuality scorer (0–100) with recommendation
│   ├── manifest.py                     # SnapshotManifest with deterministic snapshot_id
│   ├── report_writer.py                # JSON + Markdown report output
│   └── errors.py                       # MarketSnapshotError, SnapshotBuildError, FixtureHealthError
├── audit/
│   ├── validator.py                    # run_full_audit(), write_reports() — 15 checks
│   ├── safety_scan.py                  # run_safety_scan(), SafetyClassification
│   ├── docs_check.py                   # check_docs_exist(), check_modules_exist()
│   ├── dependency_check.py             # check_xrpl_js(), check_xrpl_py_version()
│   ├── phase_check.py                  # check_phase_docs()
│   └── architecture_check.py          # check_package_structure()
└── compatibility/
    ├── legacy_imports.py               # try_import() safe import wrapper
    └── execution_prototype_bridge.py   # get_execution_prototype_status()
```

---

## Module Responsibilities

| Module | Responsibility | Can Execute? |
|--------|---------------|--------------|
| core | Configuration, modes, errors, IDs | N/A |
| protocol | XRPL protocol knowledge and capability checks | No — read-only |
| providers | Data access (current ledger, history) | No — read-only |
| market | Offline market snapshot engine (Phase 47) | No — snapshot/read only |
| ingestion | Load fixture data | No — data loading |
| intelligence | Token profiling, confidence scoring | No — analysis only |
| strategy | Signal generation | No — signals only |
| outcomes | Paper outcome attribution and feedback | No — paper analysis only |
| outcome_corpus | Paper observation replay corpus and quality reports | No — paper analysis only |
| calibration_review | Calibration readiness review and non-mutating recommendations | No — paper analysis only |
| calibration_proposal | Human-reviewed calibration proposal packs | No - paper analysis only |
| risk | Pre-trade checks, circuit breakers | No — approval/rejection only |
| simulation | Deterministic trade simulation | No — simulation only |
| execution | Intent/plan/lifecycle, live_guard, paper_executor | Paper mode only |
| reconciliation | Compare simulation vs outcomes | No — analysis only |
| telemetry | Metrics, health, audit log | No — observability |
| storage | Persist records | Yes — local storage |
| cli | Command-line interface | CLI only |
| audit | Audit checks and safety scanning | No — reporting |
| compatibility | Legacy bridges | No — bridges only |

---

## Allowed Imports

Each module may import from:

| Module | May import from |
|--------|----------------|
| core | stdlib only |
| protocol | core |
| providers | core, protocol |
| market | core, protocol, providers |
| ingestion | core |
| intelligence | core, protocol |
| strategy | core |
| outcomes | signals |
| risk | core, strategy |
| simulation | core |
| execution | core, risk, simulation |
| reconciliation | core, execution |
| telemetry | core, protocol |
| storage | core |
| cli | core, protocol, simulation, execution, reconciliation, telemetry, audit, market, outcomes, outcome_corpus, calibration_review, calibration_proposal |
| audit | core, protocol |
| compatibility | core |

## Forbidden Imports

- `core` MUST NOT import from any other V2 module
- `intelligence` MUST NOT import from `execution`
- `strategy` MUST NOT import from `execution`
- `simulation` MUST NOT import from `execution`
- No V2 module may import `xrpl.wallet`, `xrpl.core.keypairs`, or any signing/key module

---

## Event Flow

```
Market Data
    → LedgerProvider (read-only)
    → intelligence/ (token profile, confidence)
    → strategy/ (signals)
    → risk/ (pre-trade checks)
    → execution/intent.py (ExecutionIntent, mode=SIMULATION or PAPER)
    → execution/plan.py (ExecutionPlan, live_submission_allowed=False)
    → simulation/ or paper_executor/ (depending on mode)
    → reconciliation/ (compare vs expected)
    → telemetry/ (record metrics)
    → storage/ (persist)
```

---

## Execution Flow (Simulation Mode)

```
assert_can_simulate(mode)
→ ExecutionIntent(mode=SIMULATION)
→ run_pretrade_checks(intent)
→ estimate_fill(), estimate_slippage(), estimate_fee()
→ ExecutionPlan(risk_approved=True, live_submission_allowed=False)
→ LifecycleLog.add(SIMULATED)
→ reconcile_v2(sim, expected)
```

---

## Reconciliation Flow

```
V2: reconcile_v2(V2SimulationRecord, V2OutcomeRecord) → V2ReconciliationRecord

Legacy bridge:
  if LEGACY_AVAILABLE:
    legacy_reconcile(SimulationRecord, LifecycleRecord)  # Phase 30
  else:
    raise ReconciliationError("Phase 30 not available")
```

## Phase 49 signal contract layer

`src/sonic_xrpl/signals/` sits between FirstLedger discovery evidence, Phase 47 market snapshots, protocol capability evidence, and future simulation/paper strategy review. It is intentionally non-executing. It produces deterministic advisory `CandidateRiskSignal` records with `live_execution_allowed=False` and explicit reasons/limitations.

The layer must not import wallet, signing, submission, Xaman, or live order placement functionality. Unknown evidence remains unknown, and synthetic fixtures are labelled synthetic.

## Phase 51 outcome attribution layer

`src/sonic_xrpl/outcomes/` sits after Phase 49 signal generation and Phase 50 paper review. It consumes deterministic signal records plus local paper observation fixtures, produces attribution records, and aggregates advisory feedback by signal type. It is analysis-only and keeps `live_execution_allowed=False` on generated records.

## Phase 52 outcome corpus layer

`src/sonic_xrpl/outcome_corpus/` sits after the paper outcome layer as an offline replay corpus foundation. It loads local paper observation fixture sets, validates source/provenance and missing fields, builds deterministic replay cases over canonical windows, scores corpus quality, and writes JSON/Markdown reports. It does not calibrate scoring thresholds, fetch live data, or enable live execution.

## Phase 53 calibration readiness layer

`src/sonic_xrpl/calibration_review/` sits after the outcome corpus layer. It consumes offline Phase 49-52 evidence snapshots, evaluates conservative readiness rules, and produces human-review-only threshold recommendations. It does not edit signal scoring, review policy, outcome attribution, corpus quality scoring, runtime configuration, or safety gates.

## Phase 54 calibration proposal layer

`src/sonic_xrpl/calibration_proposal/` sits after the calibration readiness layer. It consumes Phase 53 recommendation reports and creates deterministic proposal packs with before/after values, blocked recommendations, risk notes, review checklists, and rollback notes. It does not write proposed values into runtime configuration and keeps live execution blocked.

## Phase 55 approval ledger layer

`src/sonic_xrpl/calibration_approval/` sits after the calibration proposal layer. It consumes Phase 54 proposal packs and local review fixtures, then creates deterministic approval-ledger entries and calibration change-request entries for human governance. It does not apply changes to runtime configuration and keeps live execution blocked.

## Phase 56 implementation planning layer

`src/sonic_xrpl/calibration_implementation_plan/` sits after the approval ledger
layer. It consumes Phase 55 approval-ledger and change-request artifacts, then
creates deterministic implementation planning records plus dry-run preview
artifacts for a future manual phase. It does not apply changes to runtime
configuration and keeps live execution blocked.
