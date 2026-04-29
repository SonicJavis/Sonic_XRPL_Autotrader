# Phase 20.1 Validation Hardening Audit

## Scope

Phase 20.1 hardens the XRPL shadow validation layer. It remains advisory-only, read-only, shadow-only, non-executing, and append-only where validation records are concerned.

## Formula Safety

- Validation formulas clamp score-like outputs to `[0, 1]`.
- Requested size `0`, `NaN`, `inf`, negative EV, and massive EV inputs are handled without division by zero.
- Negative EV remains allowed as an input condition, but scoring remains finite and bounded.
- Prediction and observation are both treated as uncertain inputs.

## Brier Score Bounds

- Brier score is computed from predicted probability and a binary outcome-window proxy.
- The output is clamped to `[0, 1]`.
- Tests cover overconfidence, underconfidence, no-fill windows, and malformed numeric inputs.

## Outcome-Window Uncertainty

- Validation compares prediction vs a multi-ledger outcome window.
- Duplicate ledger snapshots are handled deterministically with a pessimistic duplicate choice.
- Ledger gaps stop the window rather than fabricating continuity.
- Mixed token/issuer snapshots do not cross-contaminate windows.

## API Contract Safety

Endpoints covered:

- `GET /validation/shadow/summary`
- `GET /validation/shadow/results`

Both endpoints preserve:

- `is_shadow=true`
- `is_advisory=true`
- `is_executable=false`
- `is_truth=false`
- `xrpl_warning`

Limits are bounded to `1..5000`, responses are deterministic, and repeated GET requests do not mutate state.

## Regression Fixture

Added `data/xrpl_validation_regression_snapshots.json` with:

- fillable-looking window
- liquidity collapse
- route change
- competition pressure
- high latency
- zero-fill window
- overconfidence case
- underconfidence case
- wide spread case
- phantom liquidity case
- mixed issuer case
- duplicate and gapped ledger case

## No-Truth-Language Rule

Validation wording avoids certainty claims such as confirmed fills or guaranteed execution. Dashboard and API wording frame validation as disagreement under uncertainty.

Allowed wording retained:

- "No ground truth exists"
- "Observed outcomes are probabilistic"
- "Validation reflects disagreement, not correctness"
- `is_truth=false`

## Dry-Run Validation Safety

`scripts/xrpl_shadow_dry_run.py --validate` remains replay-only and does not start network clients. Output includes:

- `avg_disagreement_score`
- `avg_brier_score`
- `overconfidence_rate`
- `underconfidence_rate`
- `attribution_breakdown`
- `is_shadow=true`
- `is_advisory=true`
- `is_executable=false`
- `is_truth=false`

## Dashboard Safety

Dashboard imports remain safe. The validation section frames results as probabilistic disagreement and does not start ingestion or execution paths.

## No Execution Guarantee

No wallet, signing, submission, OfferCreate, Payment, autofill, live trading, or auto-apply paths were introduced.

## Validation Results

- Pytest: `380 passed in 30.66s`
- Safety grep: no new execution path found
- Safety grep false positives: `signal/signals`
- Allowed existing findings: fail-closed wallet/transaction placeholders and test-only forbidden-command checks
