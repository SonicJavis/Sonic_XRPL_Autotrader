# Safety Model

**Phase**: 45  
**Status**: Active

---

## Runtime Modes

| Mode | Description | Can Create Intent | Can Simulate | Can Paper | Can Submit |
|------|-------------|-------------------|--------------|-----------|------------|
| `intelligence_only` | Read/analyse only (default) | ❌ | ❌ | ❌ | ❌ |
| `research` | Offline/online research snapshots | ❌ | ❌ | ❌ | ❌ |
| `simulation` | Simulated intent/plan (no network) | ✅ | ✅ | ❌ | ❌ |
| `paper` | Paper execution recording | ✅ | ❌ | ✅ | ❌ |
| `live_readiness` | Readiness checks only | ❌ | ❌ | ❌ | ❌ |
| `live` | **BLOCKED in Phase 45** | N/A | N/A | N/A | ❌ |

**Default mode**: `intelligence_only`  
Set via `SONIC_RUNTIME_MODE` environment variable (defaults to `intelligence_only` on failure).

---

## Live Guard

**Location**: `src/sonic_xrpl/execution/live_guard.py`

The live guard is the **primary safety gate** for all execution paths.

### Blocked in Phase 45 (ALL MODES)

| Operation | Guard Function | Error Raised |
|-----------|---------------|--------------|
| Transaction submission | `assert_can_submit(mode)` | `LiveTradingDisabledError` |
| Transaction signing | `block_signing()` | `LiveTradingDisabledError` |
| Transaction autofill | `block_autofill()` | `LiveTradingDisabledError` |
| Wallet from seed | `block_wallet_construction()` | `LiveTradingDisabledError` |

`assert_can_submit(mode)` raises `LiveTradingDisabledError` for **ALL** runtime modes.

### ExecutionPlan Safety Field

`ExecutionPlan.live_submission_allowed` is **hardcoded `False`**. It is set to `False` in `__post_init__` and cannot be overridden in Phase 45.

---

## Prohibited Behaviours

The following are **unconditionally prohibited** in Phase 45:

1. Signing any transaction
2. Calling `autofill()` on any transaction
3. Calling `submit()` or `submitAndWait()` on any network connection
4. Constructing a wallet from a seed or private key
5. Reading `XRPL_WALLET_SEED` or any secret from environment variables for trading
6. Starting background execution loops (`while True`, daemons, schedulers)
7. Marking `ExecutionPlan.live_submission_allowed = True`
8. Bypassing the live guard via any code path

---

## Signing / Wallet Policy

- **No signing modules** exist in V2.
- **No wallet construction** from seeds or private keys.
- `MockSubmissionProvider` exists as an interface stub only — it always raises `LiveTradingDisabledError`.
- `SubmissionProvider` abstract class exists as a contract for future phases — all implementations must check live_guard before any network call.

---

## Dependency Safety

- **xrpl-py**: Current version 4.5.0. Minimum safe: 2.6.0. No known compromises.
- **xrpl.js**: Not a dependency. Audit checks for compromised versions 4.2.1–4.2.4, 2.14.2.
- **Dependencies**: All dependencies are standard Python packages. No crypto libraries added in Phase 45.

---

## Supply-Chain Policy (Phase 48)

Phase 48 establishes explicit supply-chain guardrails:

1. **Dev dependencies are audited on every CI run** via `pip-audit` in the `dependency-audit` CI job.
2. **Compromised xrpl.js versions are blocked**: Versions 4.2.1, 4.2.2, 4.2.3, 4.2.4, and 2.14.2 of the `xrpl` npm package are detected and flagged as failures by `scripts/dependency_audit.py` and `src/sonic_xrpl/audit/dependency_check.py`.
3. **No key-material libraries should be introduced casually**: Any new dependency that handles private keys, mnemonics, or wallet seeds must be reviewed explicitly and will be caught by `scripts/safety_grep.py`.
4. **Runtime live submission remains permanently blocked** by `src/sonic_xrpl/execution/live_guard.py` regardless of dependency changes.
5. **pip-audit warning policy**: If pip-audit cannot reach the vulnerability DB (network issue), the audit records a warning but does not produce a false pass. A positive vulnerability identification always fails.
6. **Audit reports are CI artifacts**: `docs/audit/latest_dependency_audit.json` and `docs/audit/latest_dependency_audit.md` are uploaded as artifacts on every CI run.

---

## Provider / Network Policy

- `LedgerProvider` is read-only current state (rippled, public RPC, mocks).
- `HistoricalProvider` is read-only historical data (Clio, mocks). **Clio CANNOT submit transactions.**
- `SubmissionProvider` is blocked in Phase 45 — exists as interface/mock only.
- All provider calls in Phase 45 use `MockLedgerProvider` or `FixtureLedgerProvider` (offline).
- No live network calls are made in tests.

---

## CI / Audit Safety Checks

The following must pass before any phase is marked complete.

**CI (Linux, venv active or GitHub Actions Python):**

```bash
python -m pytest                           # All tests pass
python scripts/safety_grep.py             # No forbidden patterns in runtime code
python scripts/audit_validator.py         # Existing audit validator passes
python -m sonic_xrpl.cli.main health      # CLI works offline
python -m sonic_xrpl.cli.main capabilities # Capability matrix accessible
```

**Windows local validation (use venv interpreter explicitly):**

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\safety_grep.py
.venv\Scripts\python.exe scripts\audit_validator.py
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m sonic_xrpl.cli.main health
.venv\Scripts\python.exe -m sonic_xrpl.cli.main capabilities
.venv\Scripts\python.exe -m sonic_xrpl.cli.main safety-scan
.venv\Scripts\python.exe -m sonic_xrpl.cli.main market-snapshot --path tests/fixtures/xrpl
.venv\Scripts\python.exe -m sonic_xrpl.cli.main market-snapshot-report --path tests/fixtures/xrpl
Remove-Item Env:\PYTHONPATH
```

> **Windows note:** Do **not** use bare `python` for local validation — the
> system interpreter may not have `sqlmodel`, `xrpl`, or other project
> dependencies installed.  Use `.venv\Scripts\python.exe` or activate the
> venv first (`.\.venv\Scripts\Activate.ps1`).
> For a one-command validation block see `scripts/windows_validate.ps1`.

---

## Live Trading Enablement Path

Live trading is blocked until **all of the following** are complete:

1. Explicit live-enablement phase after Phase 57 architecture hardening
2. Security review (external or internal security audit)
3. Explicit user grant of permission
4. Dedicated live execution module created under new safety gates
5. Full re-run of audit validator and safety scan with live context

This path is not implemented and remains blocked.

## Legacy Freeze Policy (PR 3)

- `app/` is the current runnable legacy API/paper runtime surface.
- `execution_prototype/` is historical/reference-only unless used by named
  tests or bridge adapters.
- Xaman/manual submission flows documented under `execution_prototype/` are
  historical/manual prototype behavior and are not V2 runtime authorization.
- No new features may be added to `app/` or `execution_prototype/` until the
  canonical-path decision is resolved and required safety conformance tests pass.

## Phase 49 FirstLedger signal safety boundary

Phase 49 signals are advisory evidence contracts only. They do not authorize live trading, do not create Xaman payloads, do not sign, do not submit, and do not place orders. `BUY_CANDIDATE` is not a buy order; it means the offline minimum evidence contract passed. All outputs include `live_execution_allowed=False`.

The FirstLedger accuracy boundary is permanent: no fake token names, symbols, issuers, liquidity, holder counts, dev holdings, volume, socials, launch age, moonshot labels, or buy recommendations may be generated from missing data.

## Phase 51 paper outcome safety boundary

Phase 51 outcome attribution is fixture-backed and paper-only. It reads local Phase 49 signal fixtures and local Phase 51 paper observation fixtures, then writes advisory attribution and feedback reports. It does not change classifiers, does not mutate thresholds automatically, does not poll networks, and does not create an execution path. All Phase 51 output records keep `paper_only=True` and `live_execution_allowed=False`.

## Phase 52 outcome corpus safety boundary

Phase 52 outcome corpus tooling is fixture-backed and paper-only. It loads local observation fixtures, records missing evidence explicitly, builds replay cases, scores dataset quality, and writes JSON/Markdown reports.

It does not fetch live FirstLedger data, call XRPL network APIs, use Xaman, construct transactions, sign transactions, submit transactions, calibrate strategy thresholds, or start background replay loops. Corpus and replay case objects keep `paper_only=True` and `live_execution_allowed=False`.

## Phase 53 calibration readiness safety boundary

Phase 53 calibration readiness review is fixture/report-backed and paper-only. It reads local evidence snapshots and writes advisory readiness reports.

It does not mutate thresholds, runtime configuration, strategy settings, risk settings, provider settings, mode settings, or safety gates. Recommendations are human-review-only and are not execution approval. Synthetic data can test code paths but cannot support readiness. Fixture outcomes are not executable fill claims.

## Phase 54 calibration proposal safety boundary

Phase 54 calibration proposal packs are fixture/report-backed and paper-only. They read local Phase 53 readiness/recommendation outputs and write JSON/Markdown proposal packs for human review.

They do not change runtime settings, write proposed values into production configuration, alter thresholds automatically, unlock execution, fetch live data, or add any transaction workflow. Every proposal keeps `human_review_required=True`, `auto_apply_allowed=False`, and `live_execution_allowed=False`.

## Phase 55 approval ledger safety boundary

Phase 55 calibration approval ledger workflows are fixture/report-backed and paper-only. They read local Phase 54 proposal packs plus local human review fixtures and write approval-ledger and change-request outputs.

They do not change runtime settings, write approved values into production configuration, alter thresholds automatically, unlock execution, fetch live data, or add any transaction workflow. Every approval-ledger output keeps `human_review_required=True`, `auto_apply_allowed=False`, and `live_execution_allowed=False`.

## Phase 56 implementation planning safety boundary

Phase 56 calibration implementation planning workflows are fixture/report-backed,
paper-only, offline-only, and dry-run-only. They read local Phase 55
approval-ledger/change-request outputs and write implementation-plan and dry-run
preview artifacts.

They do not change runtime settings, write values into production configuration,
alter thresholds automatically, unlock execution, fetch live data, or add any
transaction workflow. Every Phase 56 plan output keeps
`dry_run_only=True`, `auto_apply_allowed=False`,
`runtime_mutation_allowed=False`, and `live_execution_allowed=False`.

## Phase 57 runtime profile consolidation safety boundary

Phase 57 runtime profile consolidation is read-only and deterministic. It reads
environment/config snapshots and writes advisory runtime-profile and conformance
reports.

It does not mutate runtime settings, does not change thresholds, does not
unlock execution, and does not add signing/submission/wallet paths. Conformance
checks treat explicit unsafe evidence as `FAIL`, missing evidence as `REVIEW`,
and explicit safe evidence as `PASS`.

## Phase 58B policy/spec hardening safety boundary

Phase 58B is documentation, policy, and specification hardening only.

It does not authorize live execution and does not add signing, submission,
autofill, wallet-material handling, Xaman payload creation, FirstLedger live
ingestion, runtime mutation, or autonomous execution.

Authoritative policy documents for this boundary:

- `docs/LIVE_READINESS_POLICY.md`
- `docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md`
- `docs/XAMAN_FUTURE_INTEGRATION_POLICY.md`
- `docs/FIRSTLEDGER_FUTURE_INGESTION_POLICY.md`
- `docs/POLICY_INDEX.md`


## Phase 74 governance exception waiver register safety boundary

Phase 74 waiver-register tooling is fixture-backed and spec-only. It records bounded waiver
contracts, expiry/revocation rules, and unsafe-waiver blockers without creating a runtime waiver
service or any safety bypass path. All outputs keep payload/API/signing/submission/autofill/wallet,
testnet, live, and runtime-mutation surfaces blocked.


## Phase 75 governance final readiness bundle safety boundary

Phase 75 final-bundle tooling is fixture-backed and spec-only. It composes prior governance
artifacts, preserves unresolved limitations, and reports conservative final readiness without
creating a runtime readiness service or any safety bypass path. All outputs keep payload/API/
signing/submission/autofill/wallet, testnet, live, and runtime-mutation surfaces blocked.

## Phase 76 review export safety boundary

Phase 76 remains a synthetic review-packaging specification only. It does not create a runtime export service, downloadable archives, API/UI export routes, transaction surface, or safety bypass path.

## Phase 77 manifest audit safety boundary

Phase 77 remains a synthetic manifest-audit specification only. It does not create a runtime manifest audit service, downloadable archives, API/UI audit routes, transaction surface, or safety bypass path.
