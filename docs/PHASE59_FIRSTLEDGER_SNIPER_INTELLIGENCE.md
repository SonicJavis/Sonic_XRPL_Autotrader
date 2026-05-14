# Phase 59 - FirstLedger Source-Backed Sniper Intelligence Expansion

## Scope

Phase 59 expands deterministic FirstLedger intelligence under
`src/sonic_xrpl/firstledger_intelligence/` using fixture-backed inputs only.

This phase is intelligence-only, paper-only, and non-executing.

## Implemented evidence

- `src/sonic_xrpl/firstledger_intelligence/models.py`
- `src/sonic_xrpl/firstledger_intelligence/scoring.py`
- `src/sonic_xrpl/firstledger_intelligence/rules.py`
- `src/sonic_xrpl/firstledger_intelligence/loader.py`
- `src/sonic_xrpl/firstledger_intelligence/reporting.py`
- `tests/fixtures/firstledger_intelligence/`
- `tests/unit/test_phase59_firstledger_intelligence.py`
- `tests/safety/test_phase59_firstledger_safety.py`
- CLI commands in `src/sonic_xrpl/cli/main.py`:
  - `firstledger-intelligence`
  - `firstledger-intelligence-report`

## What Phase 59 adds

- Source-provenance-aware candidate intelligence records.
- Deterministic risk-feature extraction for fixture-backed candidate evidence.
- Conservative confidence scoring and confidence bands.
- Fail-closed classification for malformed/missing/conflicting evidence.
- Non-executing verdict labels:
  - `WATCH`
  - `AVOID`
  - `INSUFFICIENT_EVIDENCE`
  - `REVIEW_REQUIRED`
  - `PAPER_ONLY_CANDIDATE`
- Deterministic JSON/Markdown report renderers.

## What Phase 59 does not authorize

- No live FirstLedger ingestion.
- No live network calls.
- No runtime collectors or background workers.
- No strategy execution coupling.
- No buy/sell order creation.
- No signing, submission, or autofill.
- No wallet seed/private key handling.
- No Xaman payload creation or signing/submission workflows.
- No runtime mutation and no threshold auto-apply.

## Safety interpretation

- `BUY_CANDIDATE` from Phase 49 remains a signal/review label only.
- `PAPER_ONLY_CANDIDATE` is not a buy order and not execution authorization.
- Missing evidence remains missing and cannot be inferred into qualification.
- Synthetic-only evidence cannot produce positive candidate qualification.
- Same-symbol/different-issuer records remain distinct.

## Validation expectations

Phase 59 validation requires passing:

- Phase 59 unit/safety tests
- repository safety checks (`safety_grep`, `audit_validator`, dependency audit)
- CLI safety scan and runtime-profile conformance checks
- full pytest baseline

Live execution remains blocked.
