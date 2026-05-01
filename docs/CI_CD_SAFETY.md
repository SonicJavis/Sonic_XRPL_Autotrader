# CI/CD Safety & Hardening Guidelines

## Workflow Purpose
The **XRPL Safety CI** workflow (`.github/workflows/ci.yml`) is the primary defense mechanism ensuring the XRPL Autotrader prototype remains safe, deterministic, and non-executing. 

Since this system handles XRPL intents and simulated trading scenarios, the risk of quietly evolving into a live trading bot is high. The CI pipeline fails closed to prevent unsafe code from ever merging into `main`.

## Safety Grep Explanation
The `scripts/safety_grep.py` script automatically scans the codebase on every push and pull request for forbidden execution and state mutation patterns. 

**Forbidden Patterns include:**
`autofill`, `submitAndWait`, `wallet`, `seed`, `private_key`, `secret`, `sign`, `submit`, `background`, `polling`, `auto_calibrate`, `mutate_model`

**Allowed vs. Forbidden Matches:**
- **Allowed**: References in `docs/`, `tests/`, strings used in status flags (e.g., `"signed"`), and comments explicitly warning about prohibited behavior.
- **Forbidden**: Any active Python code in the core engine (e.g., `execution_prototype/`) that triggers these strings as functions, variable names, or module imports.

## How to Run Tests Locally
To verify the system before pushing:
```powershell
# Run the test suite
.venv\Scripts\python.exe -m pytest execution_prototype\

# Run the safety grep
python scripts/safety_grep.py
```

## Branch / PR Workflow
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Implement your changes.
3. Run tests and the safety grep locally.
4. Commit only if both pass.
5. Push the branch and open a PR against `main`.
6. GitHub Actions will run the XRPL Safety CI. The PR **cannot** be merged if the CI fails.

## Rollback Guidance
If unsafe execution logic ever accidentally merges into `main` (e.g., bypasses CI), the immediate action is to:
1. Revert the offending commit: `git revert <commit-hash>`
2. Push the revert.
3. Update `safety_grep.py` to catch the pattern that slipped through.

## Why CI Must Block Execution Logic
The mandate of this project is to build an advisory XRPL intelligence platform, not a trading bot. Blocking auto-calibration, background polling, and transaction submission at the CI level guarantees that human review remains an absolute requirement for any real-world ledger action.
