# Phase 48 — Dependency Audit and Supply-Chain Guardrails

**Phase**: 48  
**Type**: Security/tooling/documentation  
**Status**: Complete  
**Date**: 2026-05-03

---

## What Changed

Phase 48 adds a **read-only dependency and supply-chain audit layer** to the Sonic XRPL Autotrader.

### New Files
| File | Purpose |
|------|---------|
| `scripts/dependency_audit.py` | Standalone dependency audit script |
| `tests/safety/test_dependency_audit.py` | Tests for dependency audit logic |
| `docs/research/PHASE48_DEPENDENCY_AUDIT_RESEARCH.md` | Research baseline |
| `docs/PHASE48_DEPENDENCY_AUDIT.md` | This document |

### Updated Files
| File | Change |
|------|--------|
| `pyproject.toml` | Added `pip-audit>=2.7.0` to `[project.optional-dependencies].dev` |
| `.github/workflows/ci.yml` | Added `dependency-audit` CI job |
| `docs/PHASE_LEDGER.md` | Phase 48 entry added |
| `docs/ROADMAP.md` | Phase 48 updated to Dependency Audit |
| `docs/AUDIT_VALIDATOR.md` | Dependency audit command added |
| `docs/SAFETY_MODEL.md` | Supply-chain policy section added |

### No Runtime Changes
No trading logic, provider code, or live execution paths were modified.

---

## Why Phase 48 Exists

The April 2025 supply-chain attack on the `xrpl` npm package ([XRPL disclosure](https://xrpl.org/blog/2025/vulnerabilitydisclosurereport-bug-apr2025)) demonstrated that even widely-used blockchain libraries can be compromised to exfiltrate private keys. Phase 48 adds proactive detection and auditability so that:

1. Compromised `xrpl.js` versions are **immediately detected** if they appear in any Node dependency file.
2. Python dependencies are checked for known vulnerabilities via `pip-audit`.
3. Dependency audit results are **visible in CI** as artifacts.
4. The audit is reproducible locally on Windows.

---

## How to Run Locally (Windows)

Install dev dependencies first (includes `pip-audit`):

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run the audit with report writing:

```powershell
.venv\Scripts\python.exe scripts\dependency_audit.py --write-report
```

Run with strict mode (warnings become failures — useful as a pre-commit gate):

```powershell
.venv\Scripts\python.exe scripts\dependency_audit.py --write-report --strict
```

Run without pip-audit (offline/restricted environment):

```powershell
.venv\Scripts\python.exe scripts\dependency_audit.py --write-report --skip-pip-audit
```

Print full JSON to stdout:

```powershell
.venv\Scripts\python.exe scripts\dependency_audit.py --json
```

Reports are written to:
- `docs/audit/latest_dependency_audit.json`
- `docs/audit/latest_dependency_audit.md`

---

## How CI Runs It

The `.github/workflows/ci.yml` workflow includes a new `dependency-audit` job:

```yaml
dependency-audit:
  name: Dependency Audit (Phase 48)
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    - run: |
        python -m pip install --upgrade pip
        python -m pip install -e ".[dev]"
    - run: python -m pip check
    - run: python scripts/dependency_audit.py --write-report --strict
    - uses: actions/upload-artifact@v4
      with:
        name: dependency-audit-report
        path: |
          docs/audit/latest_dependency_audit.json
          docs/audit/latest_dependency_audit.md
```

The job uploads both report files as CI artifacts for inspection.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Pass — no issues found |
| `1` | Fail — compromised package, broken dependency, or known vulnerability |
| `2` | Warning-only — pip-audit unavailable/network down, no bad package detected |

With `--strict`, exit code 2 is promoted to 1.

---

## What Counts as Failure vs Warning

### Hard Failure (exit 1)
- `pip check` reports broken requirements
- `pip-audit` positively identifies known vulnerability(ies)
- Any Node dependency file contains a compromised `xrpl.js` version

### Warning (exit 2)
- `pip-audit` is not installed
- `pip-audit` times out or cannot reach vulnerability DB
- Node lockfile parse error

### Not Applicable (pass)
- No `package.json`, `package-lock.json`, or `pnpm-lock.yaml` found → Node audit returns `not_applicable`, not a failure

---

## Node / xrpl.js Compromised Version Policy

The following `xrpl` npm package versions are **unconditionally blocked** (they exfiltrate private key material):

| Version | Status |
|---------|--------|
| `4.2.1` | ❌ COMPROMISED |
| `4.2.2` | ❌ COMPROMISED |
| `4.2.3` | ❌ COMPROMISED |
| `4.2.4` | ❌ COMPROMISED |
| `2.14.2` | ❌ COMPROMISED |

The audit detects these in:
- `package.json` (all dependency sections)
- `package-lock.json`
- `pnpm-lock.yaml`

**Safe versions** (patched, key exfiltration removed):
- `4.2.5` or any higher `4.x`
- `2.14.3` or any higher `2.x`

**Source**: [XRPL Vulnerability Disclosure — April 2025](https://xrpl.org/blog/2025/vulnerabilitydisclosurereport-bug-apr2025)

---

## pip-audit Policy

- `pip-audit>=2.7.0` is a **dev dependency** (not a runtime dependency).
- It is installed via `pip install -e ".[dev]"`.
- It requires network access to query the OSV/PyPI Advisory database during a scan.
- If pip-audit is unavailable or the network is down, the audit returns a **warning** (not a hard fail).
- A **hard fail** is only generated if pip-audit positively identifies known vulnerabilities.

To install pip-audit manually if not using the dev extras:
```bash
pip install pip-audit
```

---

## Why No Live XRPL Calls Are Needed

This audit is a **static dependency inspection** only:
- It reads local file system: `package.json`, lockfiles, `pyproject.toml`
- It runs `pip check` and `pip-audit` locally against the installed package set
- It queries the OSV/PyPI Advisory DB (pip-audit handles this — not our code)
- It does **not** connect to any XRPL node, rippled server, Clio server, WebSocket, or RPC endpoint

No XRPL network calls are needed because we are auditing software supply chain, not ledger state.

---

## Safety Statement

This phase:

- ❌ Does **NOT** add wallet handling
- ❌ Does **NOT** add seed or private key handling
- ❌ Does **NOT** add transaction signing
- ❌ Does **NOT** add transaction submission
- ❌ Does **NOT** add autofill
- ❌ Does **NOT** add live XRPL RPC calls
- ❌ Does **NOT** add testnet or live trading
- ❌ Does **NOT** add hidden background loops, daemons, or schedulers
- ❌ Does **NOT** weaken `scripts/safety_grep.py`, `scripts/audit_validator.py`, or `live_guard.py`
- ❌ Does **NOT** modify `.ecc-source/`
- ✅ Is **read-only** except for writing report files to `docs/audit/`
- ✅ Live trading remains **blocked** by `live_guard.py`

---

## Related Files

| File | Role |
|------|------|
| `scripts/dependency_audit.py` | Main audit script |
| `src/sonic_xrpl/audit/dependency_check.py` | V2 dependency check module (xrpl.js detection) |
| `tests/safety/test_dependency_audit.py` | Test coverage |
| `docs/research/PHASE48_DEPENDENCY_AUDIT_RESEARCH.md` | Research baseline with sources |
| `docs/audit/latest_dependency_audit.json` | Generated JSON report |
| `docs/audit/latest_dependency_audit.md` | Generated Markdown report |
| `pyproject.toml` | `pip-audit>=2.7.0` in dev dependencies |
| `.github/workflows/ci.yml` | `dependency-audit` CI job |
