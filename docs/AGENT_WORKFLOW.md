# Sonic XRPL Autotrader Agent Workflow

## What Agents Should Help With

- repo audits
- phase reconstruction
- reconciliation validation
- simulation-only execution checks
- test creation and test repair
- safety review
- documentation updates
- CLI smoke checks
- report generation

## What Needs Explicit Approval

- live execution changes
- wallet/signing changes
- dependency changes
- CI/CD changes
- enabling hooks/MCPs
- external installers
- changes to generated artifacts

## Forbidden By Default

- real wallet seed/private key handling
- auto-signing
- live trading
- global config changes
- ECC hook/MCP adoption
- destructive git operations
- hidden autonomous loops

## Standard Phase Prompt Template

```text
Phase:
Objective:
Scope:
Allowed files:
Forbidden files/actions:
Allowed commands:
Required validation:
Required report:
```

## Pre-Commit Checklist

- git status checked
- no `.ecc-source/` staged
- no secrets
- targeted tests passed
- security grep reviewed
- rollback notes included
- final summary written

## ECC Usage

- ECC remains ignored in `.ecc-source/`.
- ECC is reference-only.
- Do not install/enable/copy hooks/MCPs.
- Adapt only small project-local ideas that directly improve Sonic XRPL Autotrader.

## Local Validation on Windows

Use the virtual-environment interpreter for all local validation commands:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\safety_grep.py
.venv\Scripts\python.exe scripts\audit_validator.py
```

Do **not** use bare `python` — the system interpreter will not have `sqlmodel`,
`xrpl`, or other project dependencies installed.

## .ecc-source Exclusion From Safety Scans

`.ecc-source/` is explicitly excluded from `scripts/safety_grep.py` and
`src/sonic_xrpl/audit/safety_scan.py`.

Rationale — excluding `.ecc-source/` does **not** weaken runtime safety because:

- It is ignored by Git (listed in `.gitignore`).
- It is never committed to the repository.
- It is never installed or imported by any Sonic XRPL Autotrader code path.
- It is an external reference clone only; its strings (e.g. `background=`,
  widget styling) have no bearing on this project's execution safety.
- Any ECC-sourced pattern that does appear in project runtime code would still
  be caught by the scan because only `.ecc-source/` itself is excluded, not the
  patterns.
