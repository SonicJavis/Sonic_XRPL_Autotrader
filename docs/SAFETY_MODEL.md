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

1. Phase 56 — Live Readiness Checklist (structural verification only)
2. Phase 57 — Security Review (external or internal security audit)
3. Explicit user grant of permission
4. Dedicated live execution module created under new safety gates
5. Full re-run of audit validator and safety scan with live context

This path is not implemented and is not planned until Phase 57 minimum.
