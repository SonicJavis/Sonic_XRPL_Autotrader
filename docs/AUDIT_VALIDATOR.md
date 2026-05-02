# Phase 42.2 – Audit Validator

## Purpose

`scripts/audit_validator.py` is a repo-wide integrity and safety check tool.
It verifies that:

1. The repository's git state is inspectable (branch hygiene).
2. No live execution primitives (wallet seeds, signing, submission) have crept
   into runtime code (`safety_grep.py` gate).
3. All `execution_prototype` sub-packages are importable without errors.
4. Every CLI entry-point responds correctly to `--help`.
5. Key safety disclosures are present in `docs/SYSTEM_STATE.md` and `README.md`.

The script is **read-only** – it never modifies source files and performs no
network calls.  It only writes to the `artifacts/` directory.

---

## Checks Performed

| # | Check | Pass Condition |
|---|-------|---------------|
| 1 | **Branch hygiene** | `git status` and `git log` run without error; uncommitted file count is reported (informational only – does **not** fail the audit). |
| 2 | **Safety grep** | `scripts/safety_grep.py` exits 0 (no forbidden live-execution patterns found). |
| 3 | **Import smoke test** | `importlib.import_module` succeeds for every sub-package listed in `PROTOTYPE_PACKAGES`. |
| 4 | **CLI help test** | `python -m <module> -h` exits 0 for every `cli.py` entry-point in `execution_prototype`. |
| 5 | **Documentation disclosures** | `docs/SYSTEM_STATE.md` contains `"paper-only"`, `"0/100"`, and `"Fail-Closed"`; `README.md` contains `"paper"` and `"No wallet"`. |

---

## How to Run Locally

```bash
# From the repository root (virtual-env active or project installed with pip install -e .[dev]):
python scripts/audit_validator.py
```

The script adds the repository root to `sys.path` automatically, so it works
regardless of which directory you invoke it from.

---

## Report Paths

| Artifact | Description |
|----------|-------------|
| `artifacts/audit_validator_report.json` | Machine-readable JSON report consumed by CI. |

The `artifacts/` directory is created automatically on first run.

### JSON Report Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO-8601 UTC timestamp>",
  "phase": "42.2",
  "overall_passed": true,
  "checks": {
    "branch_hygiene":   { "passed": true,  "details": { ... } },
    "safety_grep":      { "passed": true,  "details": { "exit_code": 0, ... } },
    "import_smoke":     { "passed": true,  "details": { "total": 16, ... } },
    "cli_help":         { "passed": true,  "details": { "total": 13, ... } },
    "doc_disclosures":  { "passed": true,  "details": { "checked": [...] } }
  }
}
```

---

## Exit Code Behaviour

| Code | Meaning |
|------|---------|
| `0`  | All checks passed – `overall_passed: true` in the report. |
| `1`  | One or more checks failed – `overall_passed: false` in the report. |

The GitHub Actions workflow (`.github/workflows/audit-validator.yml`) treats
a non-zero exit code as a failing CI step.

---

## Safety Limitations

- **No live XRPL interaction.** The script never connects to any XRPL node,
  ledger, or RPC endpoint.
- **No wallet.** No wallet address, seed, mnemonic, or private key is used or
  generated.
- **No signing.** No transaction signing of any kind is performed.
- **No submission.** No transactions or payloads are submitted to the ledger.
- **No live trading.** The entire codebase is paper-only. Live trading readiness
  is permanently `0/100` until explicit human governance gates are passed.
- **No auto-calibration or model mutation.** The validator is a passive
  read-only reporter; it cannot change trading parameters or strategy weights.

---

## Related Files

| File | Role |
|------|------|
| `scripts/safety_grep.py` | Gatekeeper – scans source for forbidden live-execution patterns. |
| `docs/SYSTEM_STATE.md` | Single source of truth for project phase and readiness. |
| `docs/LIVE_TRADING_READINESS_GATES.md` | Roadmap to live trading (currently 0/100). |
| `.github/workflows/audit-validator.yml` | CI workflow that runs the validator on every PR and push to `main`. |
| `artifacts/audit_validator_report.json` | Generated report – useful for CI artifact archiving. |
| `execution_prototype.dataset_strategy_tournament` | Phase 43 – Dataset-Driven Strategy Tournament; evaluates strategies across train/validation/test windows with overfitting detection. |

| `execution_prototype.walk_forward_replay` | Phase 44 – Walk-Forward Replay Engine; evaluates strategy stability across rolling temporal windows from Phase 42 datasets. |
