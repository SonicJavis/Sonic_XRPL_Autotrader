# Agent Operating Rules

**Applies to**: All future agents working on this repository  
**Minimum version**: Phase 45  
**Last updated**: 2026-05-13

---

## MANDATORY: Read Before Coding

Every agent MUST read the following before making any code changes:

1. **`docs/PROJECT_BLUEPRINT.md`** — Purpose, V2 architecture, safety model summary
2. **`docs/V2_ARCHITECTURE.md`** — Package tree, module responsibilities, allowed/forbidden imports
3. **`docs/PHASE_LEDGER.md`** — Verified phases, evidence, status
4. **`docs/SAFETY_MODEL.md`** — Runtime modes, live guard, prohibited behaviours

Failure to read these documents before coding may result in:
- Breaking existing safety guards
- Creating circular imports
- Accidentally enabling live trading paths
- Introducing security vulnerabilities

---

## Core Rules

### 1. No Live Trading Without Dedicated Live-Enablement Approval
Do NOT enable live trading, signing, transaction submission, autofill, wallet
construction, Xaman payload implementation, or FirstLedger live ingestion.
Phase 58B is policy/spec hardening only; live execution remains blocked until a
future dedicated live-enablement phase with explicit human approval.

### 2. Preserve `execution/live_guard.py`
This file is the primary safety gate. Do NOT modify it to weaken any guard.
`assert_can_submit(mode)` MUST always raise `LiveTradingDisabledError` until Phase 57.

### 3. Architecture Rules Apply
Follow the 13 architecture rules in `docs/V2_ARCHITECTURE.md`:
- Intelligence does not execute (Rule 6)
- Strategy does not execute (Rule 7)
- Risk approves or rejects (Rule 8)
- Execution consumes only risk-approved intent (Rule 9)
- Simulation must not assume guaranteed fills (Rule 10)
- Lifecycle is append-only (Rule 11)
- Tests must run offline (Rule 13)

### 4. Protocol Capabilities Must Be Explicit
No code may assume an XRPL amendment is available without checking
`src/sonic_xrpl/protocol/capability_matrix.py` (Architecture Rule 1).

### 5. Update PHASE_LEDGER.md
When completing a phase, update `docs/PHASE_LEDGER.md` with:
- Phase name
- Status (in progress / verified complete)
- Evidence (files, tests, docs)
- Safety impact

### 6. Run Validation Before Marking Complete
A phase is complete only when ALL of the following pass:
```bash
python -m pytest
python scripts/safety_grep.py
python scripts/audit_validator.py
python -m sonic_xrpl.cli.main --help
python -m sonic_xrpl.cli.main health
python -m sonic_xrpl.cli.main capabilities
```

### 7. No Secrets in Code
Never commit:
- Wallet seeds or private keys
- API keys or authentication tokens
- Environment variable names that access secrets

### 8. Preserve Legacy Modules
Do NOT delete or destructively modify:
- `execution_prototype/`
- `app/`
- `dashboard/`
- `scripts/`
- `docs/` (existing files)

Add new code alongside existing code using adapters.

---

## Allowed Autonomous Actions

An agent may autonomously:
- Create new files and modules
- Run pytest, safety_grep, audit_validator
- Make git commits and push
- Create PRs

An agent MUST NOT autonomously:
- Delete or force-push
- Change secrets configuration
- Enable live trading
- Add wallet/signing/submission logic
- Weaken safety gates
- Make product-level decisions when conflicts arise
