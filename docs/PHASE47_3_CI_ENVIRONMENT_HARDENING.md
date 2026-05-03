# Phase 47.3 — CI Environment Hardening

**Phase**: 47.3  
**Date**: 2026-05-03  
**Status**: Complete

---

## Objective

Make GitHub Actions CI match the verified local Windows/dev validation flow as
closely as possible.  This is a CI tooling phase only — no trading features,
runtime logic, or application code were changed.

---

## Root Cause / Need

The existing `ci.yml` (pre-47.3) had several gaps compared to the verified
local validation baseline established in Phase 47.2:

| Gap | Before 47.3 | After 47.3 |
|-----|-------------|------------|
| Python version | 3.10 (below `requires-python = ">=3.11"`) | 3.11 and 3.12 matrix |
| Dependency install | `pip install -r requirements.txt` + ad-hoc packages | `pip install -e ".[dev]"` (pyproject.toml) |
| Test scope | Only `execution_prototype/` | Full suite (`tests/` + `execution_prototype/tests/`) |
| safety_grep | ✅ ran, but separate job | ✅ preserved |
| audit_validator | In `audit-validator.yml` only; used `pip install .` (no dev extras) | Promoted to `ci.yml`; both workflows use `pip install -e ".[dev]"` |
| V2 CLI smoke checks | ❌ missing | ✅ added as `v2-cli-smoke` job |
| `deterministic-check` job | Ran subset via ad-hoc `pip install pytest pydantic` | Covered by full `pytest` run |
| artifact upload action | `actions/upload-artifact@v3` (deprecated) | `actions/upload-artifact@v4` |

---

## Files Changed

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Full rewrite — see CI Changes below |
| `.github/workflows/audit-validator.yml` | Install updated to `pip install -e ".[dev]"`; actions bumped to v4 |
| `docs/PHASE47_3_CI_ENVIRONMENT_HARDENING.md` | **New** — this phase report |

---

## CI Changes

### `ci.yml` — Consolidated Safety CI

**Jobs:**

| Job | What it does |
|-----|-------------|
| `test` | Runs full `pytest` on Python 3.11 and 3.12 matrix; uploads JUnit XML |
| `safety-grep` | Runs `scripts/safety_grep.py` on Python 3.11 |
| `audit-validator` | Runs `scripts/audit_validator.py` on Python 3.11; uploads audit report JSON |
| `v2-cli-smoke` | Runs all V2 CLI commands with `PYTHONPATH=src` on Python 3.11 |
| `report-artifacts` | Uploads a summary text; gates on all other jobs |

**Key improvements:**
- Python version raised to 3.11/3.12 (matches `requires-python = ">=3.11"`).
- All jobs install with `python -m pip install -e ".[dev]"` so the exact
  dependency graph from `pyproject.toml` is used — same as local Windows venv.
- Full test suite runs (both `tests/` and `execution_prototype/tests/`), not
  just `execution_prototype/`.
- `deterministic-check` job removed — covered by the full `pytest` run.
- All `actions/*@v3` references replaced with `@v4` (v3 is end-of-life).

### `audit-validator.yml`

- Install changed from `pip install .` to `pip install -e ".[dev]"` so dev
  extras (pytest) are available if needed by the validator.
- Added `upload-artifact@v4` step to archive the JSON report.
- Actions versions bumped to v4/v5.

---

## PYTHONPATH Note

`src/sonic_xrpl` is mapped in `pyproject.toml` via the legacy
`[tool.setuptools.package-dir]` key.  Editable installs on current setuptools
expose the package correctly for `import sonic_xrpl`, but the CLI entry-point
`python -m sonic_xrpl.cli.main` requires the `src/` directory to be on
`sys.path`.

Both CI (`PYTHONPATH: src` env on the `v2-cli-smoke` job) and local Windows
(`$env:PYTHONPATH = "src"` in `windows_validate.ps1`) set this explicitly.
Pytest itself adds `src` via the `pythonpath = [".", "src"]` setting in
`pyproject.toml`, so tests are unaffected.

---

## Validation Results

Local validation (confirmed with project venv interpreter):

| Check | Result |
|-------|--------|
| `python -m pytest` | ✅ All tests passed |
| `python scripts/safety_grep.py` | ✅ Pass |
| `python scripts/audit_validator.py` | ✅ All 5 checks green |
| `CLI --help / health / capabilities / safety-scan / market-snapshot / market-snapshot-report` | ✅ All passed |

CI run status: workflow changes pushed to branch; CI will run on PR/merge.
Do not claim CI passed until GitHub Actions confirms green on the PR.

---

## Safety Notes

- No live trading capabilities added.
- No wallet, seed, signing, or submission paths touched.
- `scripts/safety_grep.py` not weakened.
- `src/sonic_xrpl/audit/safety_scan.py` not weakened.
- No `.ecc-source/` modification.
- No global machine configuration changed.
- No secrets or credentials added to any workflow.
- All CI jobs are offline — no XRPL node connections, no live network calls.

---

## Git / PR

Branch: `copilot/fix-windows-validation-consistency` (Phase 47.3 squashed with 47.2).  
Commit message: `Phase 47.3: Harden CI validation environment`

---

## Rollback Notes

```bash
git revert HEAD   # or reset to the pre-47.3 commit SHA
```

No runtime or trading behaviour was changed, so rollback has no operational
impact beyond reverting to the older CI configuration.

---

## Recommended Next Phase

**Phase 48** (suggested) — Dependency audit and pin: review all `pyproject.toml`
dependency lower-bounds, add an automated `pip-audit` step to CI to detect
known vulnerabilities in project dependencies as they are added.
