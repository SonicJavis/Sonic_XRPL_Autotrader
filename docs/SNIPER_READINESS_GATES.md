# Sniper-Style Readiness Gates

## Scope

This document defines mandatory readiness gates before any signing or submission
code may exist in the canonical future runtime (`src/sonic_xrpl/`).

Live/sniper execution remains blocked by default.

## Status Key

- `[ ]` blocked / not yet satisfied
- `[x]` ready / satisfied

## Pre-Requisites (MUST Exist First)

- [ ] Hot wallet architecture defined with explicit spending limits and key
      custody boundaries.
- [ ] Deterministic replay harness exists for sniper decision paths
      (intent inputs, decision outputs, and replay invariants).
- [ ] Transaction lifecycle implementation exists for:
      sequence management, `LastLedgerSequence`, result-code handling, and
      deterministic retry policy.
- [ ] Reconciliation layer exists from intent to validated ledger metadata
      (`tx`, `meta`, final outcome classification).

## Safety Gates (MUST Pass)

- [ ] Max position size per token enforced pre-submit.
- [ ] Max daily loss limit enforced.
- [ ] Max total loss limit enforced.
- [ ] Emergency stop exists and persists across restarts.
- [ ] Slippage and liquidity validation enforced before submit.

## Test Suite Requirements

- [ ] 100% coverage of signing and submission code paths.
- [ ] Partial fill simulation tests pass.
- [ ] Stale quote rejection tests pass.
- [ ] Sequence collision handling tests pass.

## BLOCKED UNTIL Criteria

Live/sniper branch creation is blocked until all checklist items below are
ready:

- [ ] All Pre-Requisites are `[x]`.
- [ ] All Safety Gates are `[x]`.
- [ ] All Test Suite Requirements are `[x]`.
- [ ] `tests/test_execution_guard.py` passes.
- [ ] `tests/unit/test_live_guard.py` passes.
- [ ] `tests/safety/test_safety_scan.py` passes.
- [ ] `python scripts/safety_grep.py` passes.
- [ ] `python scripts/audit_validator.py` passes.
- [ ] `PYTHONPATH=src python -m sonic_xrpl.cli.main safety-scan` passes.
- [ ] `PYTHONPATH=src python -m sonic_xrpl.cli.main audit` passes.

Until every item is `[x]`, signing/submission code creation is out of scope.
