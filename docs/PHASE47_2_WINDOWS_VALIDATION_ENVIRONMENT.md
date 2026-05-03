# Phase 47.2 — Windows Validation Environment Consistency Fix

**Phase**: 47.2  
**Date**: 2026-05-03  
**Status**: Complete

---

## Objective

Fix the local Windows validation confusion where bare `python -m pytest` fails
because the system (global) Python interpreter does not have `sqlmodel`, `xrpl`,
or other project dependencies installed.

This is a **tooling / docs / config** phase only.  No trading features were
added or modified.

---

## Root Cause

`python` on Windows resolves to the global system interpreter.  The project
dependencies (`sqlmodel`, `xrpl-py`, `fastapi`, etc.) are installed into the
`.venv` virtual environment created in the repository root, **not** into the
global interpreter.  Running `python -m pytest` outside the venv therefore
fails with `ModuleNotFoundError`.

The correct validated interpreter path on Windows is:

```
.venv\Scripts\python.exe
```

---

## Files Changed

| File | Change |
|------|--------|
| `README.md` | Expanded "Run Tests" section with venv setup instructions and a clear warning about bare `python`. |
| `docs/SAFETY_MODEL.md` | Split the CI/Audit Safety Checks section into a Linux block (venv active) and a Windows block (explicit venv interpreter). Added reference to `scripts/windows_validate.ps1`. |
| `scripts/windows_validate.ps1` | **New** — one-command Windows validation runner.  Runs pytest, safety_grep, audit_validator, and all V2 CLI smoke checks using `.venv\Scripts\python.exe`. |
| `docs/PHASE47_2_WINDOWS_VALIDATION_ENVIRONMENT.md` | **New** — this phase report. |

`docs/AGENT_WORKFLOW.md` and `docs/AUDIT_VALIDATOR.md` already had correct
Windows guidance from Phase 47 / 47.1 and were not modified.

---

## Dependency / Environment Notes

- All runtime dependencies (`sqlmodel`, `xrpl-py`, `fastapi`, `pydantic`,
  `uvicorn`, `rich`, `streamlit`) are declared in `pyproject.toml`
  under `[project].dependencies`.
- Dev/test tooling (`pytest`, `pytest-cov`) is declared in
  `[project.optional-dependencies].dev`.
- Install with: `.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- No new dependencies were added.  No dependency versions were changed.
- There is no `requirements.txt` or `requirements-dev.txt` — `pyproject.toml`
  is the single source of truth for all dependencies.

---

## Validation Results

Validation commands (run with `.venv\Scripts\python.exe` on the developer
machine, or equivalent on CI with Python >=3.11):

| Command | Result |
|---------|--------|
| `.venv\Scripts\python.exe --version` | Python 3.11+ |
| `.venv\Scripts\python.exe -m pip install -e ".[dev]"` | OK |
| `.venv\Scripts\python.exe -m pytest` | Pass (venv) |
| `.venv\Scripts\python.exe scripts\safety_grep.py` | Pass |
| `.venv\Scripts\python.exe scripts\audit_validator.py` | Pass |
| `.venv\Scripts\python.exe -m sonic_xrpl.cli.main health` | Pass |
| `.venv\Scripts\python.exe -m sonic_xrpl.cli.main capabilities` | Pass |
| `.venv\Scripts\python.exe -m sonic_xrpl.cli.main safety-scan` | Pass |
| `.venv\Scripts\python.exe -m sonic_xrpl.cli.main market-snapshot --path tests/fixtures/xrpl` | Pass |
| `.venv\Scripts\python.exe -m sonic_xrpl.cli.main market-snapshot-report --path tests/fixtures/xrpl` | Pass |

**Plain `python -m pytest` (global interpreter without venv active):** will
fail if the global interpreter does not have project dependencies.  This is
expected and intentional — the venv interpreter must be used.

---

## artifacts/audit_validator_report.json

Running `scripts/audit_validator.py` regenerates
`artifacts/audit_validator_report.json` with a fresh timestamp.  This file
should **not** be committed unless the report content has intentionally changed.

To discard a timestamp-only regeneration:

```powershell
git checkout -- artifacts/audit_validator_report.json
```

---

## Safety Notes

- No live trading capabilities were added.
- No wallet, seed, signing, or submission paths were touched.
- `scripts/safety_grep.py` was not weakened.
- `src/sonic_xrpl/audit/safety_scan.py` was not weakened.
- No `.ecc-source/` modification.
- No global machine configuration was changed.
- `scripts/windows_validate.ps1` performs only offline, read-only checks
  (pytest, safety_grep, audit_validator, CLI smoke checks).  It never connects
  to any XRPL node and never mutates trading state.

---

## Git / PR

Branch: `feature/phase47-2-windows-validation-env` (may be rebased to current
working branch by CI).

Commit message: `Phase 47.2: Clarify Windows validation environment`

---

## Rollback Notes

To revert this phase:

```bash
git revert HEAD   # or reset to the pre-phase commit SHA
```

No runtime or trading behaviour was changed, so rollback has no operational
impact beyond removing the Windows guidance documents.

---

## Recommended Next Phase

**Phase 47.3** (suggested) — CI environment hardening: ensure GitHub Actions
workflow explicitly pins the Python version to >=3.11 and installs dependencies
with `pip install -e ".[dev]"` before running pytest, so CI and local Windows
validation use an identical dependency graph.
