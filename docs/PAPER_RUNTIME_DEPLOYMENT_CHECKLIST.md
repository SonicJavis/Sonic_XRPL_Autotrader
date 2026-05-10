# Paper Runtime Deployment Checklist

## Scope

This checklist deploys the canonical `src/sonic_xrpl/` paper runtime only.
Live/sniper execution remains blocked.

## Pre-Deploy Requirements

- [ ] Merge baseline complete on `main`.
- [ ] `LIVE_TRADING_ENABLED=false` default confirmed.
- [ ] `EXECUTION_ENABLED=false` default confirmed.
- [ ] `tests/test_execution_guard.py` passing.
- [ ] `tests/unit/test_live_guard.py` passing.
- [ ] `tests/safety/test_safety_scan.py` passing.

## Build and Start

```bash
docker compose build --no-cache paper-runtime
docker compose up -d paper-runtime
```

## Required Environment

Source: `deploy/paper-runtime.env`

- `SONIC_RUNTIME_MODE=paper`
- `SONIC_DRY_RUN=true`
- `SONIC_STORAGE_PATH=/data/v2.db`
- `EXECUTION_ENABLED=false`
- `LIVE_TRADING_ENABLED=false`

## Port and Service Profile

- No public trading API is exposed by this compose profile.
- Container health is validated via:
  - `python -m sonic_xrpl.cli.main health --json`

## Post-Deploy Verification

```bash
docker compose ps
docker compose logs --tail=100 paper-runtime
docker compose exec paper-runtime python -m sonic_xrpl.cli.main health --json
docker compose exec paper-runtime python -m sonic_xrpl.cli.main safety-scan
docker compose exec paper-runtime python scripts/audit_validator.py
```

## XRPL Production Hardening Checklist (Paper-Only Context)

- [ ] Hot/warm/cold wallet architecture documented only; not implemented.
- [ ] Reliable transaction submission flow documented only; not implemented.
- [ ] API rate-limiting and retry policy documented for future live phase.
- [ ] Dependency audit job passing (`scripts/dependency_audit.py --write-report --strict`).
- [ ] Validator/node operations guidance documented for future live phase.

## Blockers

Deployment must stop if any of the following occur:

- Any safety guard test fails.
- `safety_grep.py` fails.
- `audit_validator.py` fails.
- `safety-scan` reports blocked findings.
- Any change attempts to enable signing, submission, autofill, wallet
  construction, or sniper/live execution.
