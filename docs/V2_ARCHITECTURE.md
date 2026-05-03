# V2 Architecture

**Version**: 2.0.0-alpha  
**Phase**: 45

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
│   └── main.py                         # CLI: health, audit, capabilities, safety-scan, simulate, reconcile
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
| ingestion | Load fixture data | No — data loading |
| intelligence | Token profiling, confidence scoring | No — analysis only |
| strategy | Signal generation | No — signals only |
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
| ingestion | core |
| intelligence | core, protocol |
| strategy | core |
| risk | core, strategy |
| simulation | core |
| execution | core, risk, simulation |
| reconciliation | core, execution |
| telemetry | core, protocol |
| storage | core |
| cli | core, protocol, simulation, execution, reconciliation, telemetry, audit |
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
