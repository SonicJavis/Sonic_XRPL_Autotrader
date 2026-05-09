# Phase 53 - Calibration Readiness Review

## Objective

Phase 53 adds an offline, deterministic, non-mutating calibration readiness
review layer under `src/sonic_xrpl/calibration_review/`.

It consumes paper-only evidence snapshots from Phase 49 signal contracts,
Phase 50 paper review records, Phase 51 outcome attribution records, and Phase
52 outcome corpus reports or fixtures. It decides whether the project has
enough source-backed paper evidence for a future human calibration review.

## Safety Scope

Phase 53 is paper-only and offline.

It does not:

- change signal thresholds
- change strategy settings
- change risk settings
- change runtime mode settings
- enable live trading
- fetch live FirstLedger, XRPL, Clio, or rippled data
- use Xaman
- construct transactions
- sign transactions
- submit transactions
- create execution approval

Recommendations are advisory only and do not mutate runtime configuration.
Every Phase 53 model keeps `paper_only=True` and
`live_execution_allowed=False`.

## Readiness Statuses

- `NOT_READY`: blockers show the evidence is not ready.
- `NEEDS_MORE_EVIDENCE`: a critical issue exists, but the evidence set is not empty.
- `REVIEW_WITH_CAUTION`: no blocker exists, but warnings require caution.
- `READY_FOR_HUMAN_REVIEW`: rules passed and a future human review packet may be considered.

Readiness is not a profitability claim and is not execution approval.

## Readiness Rules

Phase 53 evaluates:

- minimum corpus size
- source-backed ratio
- missing observation ratio
- invalid numeric observations
- attributed outcome coverage
- signal classification coverage
- paper-only and live-execution invariants
- synthetic fixture exclusion
- non-mutating behavior
- human-review requirement
- provenance consistency
- report reproducibility

Rule thresholds are function inputs with conservative defaults. They are not
stored globally and are not applied to runtime scoring.

## Recommendations

Recommendations use non-mutating directions:

- `KEEP`
- `REVIEW_INCREASE`
- `REVIEW_DECREASE`
- `INSUFFICIENT_EVIDENCE`

They are human-review-only and never say to apply a setting automatically.
Synthetic data can test code paths but cannot support calibration readiness.
Fixture outcomes are not executable fill claims.

## CLI

```powershell
PYTHONPATH=src python -m sonic_xrpl.cli.main calibration-readiness --fixture tests/fixtures/calibration_review/sufficient_source_backed_evidence.json
PYTHONPATH=src python -m sonic_xrpl.cli.main calibration-recommendations --fixture tests/fixtures/calibration_review/sufficient_source_backed_evidence.json
PYTHONPATH=src python -m sonic_xrpl.cli.main calibration-readiness-report --fixture tests/fixtures/calibration_review/sufficient_source_backed_evidence.json --output-dir reports/phase53
```

All commands are deterministic and offline.

## Reports

The report writer produces:

- `reports/phase53/calibration_readiness.json`
- `reports/phase53/calibration_readiness.md`
- `reports/phase53/calibration_recommendations.json`

Reports include readiness status, blockers, warnings, evidence summary,
recommendations, safety statement, accuracy statement, provenance references,
and rollback notes.

## Rollback

Rollback is a normal revert of the Phase 53 merge commit. No database migration,
external service setup, live config, or secrets are introduced.

## Next Step

If Phase 53 remains non-mutating and validated, the next phase should be Phase
54 - Human-Reviewed Calibration Proposal Pack. Phase 54 may draft exact proposed
changes for manual approval, but still must not apply them automatically.
