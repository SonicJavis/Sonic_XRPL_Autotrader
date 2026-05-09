# Phase 54 - Human-Reviewed Calibration Proposal Pack

Phase 54 adds an offline proposal-pack layer that consumes Phase 53 readiness
and recommendation outputs, then creates deterministic before/after calibration
proposal records for human review.

This phase does not apply calibration. It does not change runtime settings,
signal thresholds, risk settings, provider settings, mode settings, safety gates,
or execution settings.

## Scope

- New package: `src/sonic_xrpl/calibration_proposal/`
- CLI commands:
  - `calibration-proposals`
  - `calibration-proposal-report`
  - `calibration-proposal-diff`
- Fixtures: `tests/fixtures/calibration_proposal/`
- Reports: `reports/phase54/calibration_proposal_pack.json` and `.md`
- Tests: Phase 54 unit, smoke, and safety tests

## Proposal Rules

Exact proposals are generated only when Phase 53 readiness supports human
review and the source recommendation requests a directional review. The
deterministic movement is deliberately small:

- `REVIEW_INCREASE`: current value plus `0.02`
- `REVIEW_DECREASE`: current value minus `0.02`
- values are clamped to the parameter's allowed range

`KEEP` and `INSUFFICIENT_EVIDENCE` recommendations become blocked proposal
records instead of exact changes.

Exact proposals are blocked when:

- readiness is not `READY_FOR_HUMAN_REVIEW` or `REVIEW_WITH_CAUTION`
- readiness blockers remain
- synthetic evidence is present
- invalid numeric observations are present
- sparse signal classes limit confidence
- source recommendation safety flags are not human-review-only

## Safety Boundary

Phase 54 is paper-only, offline-only, non-mutating, and human-review-only.

It does not:

- enable live trading
- fetch live FirstLedger, XRPL, Clio, or rippled data
- use Xaman
- create transactions
- sign or submit anything
- start polling, streaming, daemon, or background execution
- alter calibration thresholds automatically
- claim profitability or execution readiness

All proposal packs keep:

- `paper_only=True`
- `auto_apply_allowed=False`
- `live_execution_allowed=False`
- proposal `human_review_required=True`

## Reports

The report writer creates:

- `calibration_proposal_pack.json`
- `calibration_proposal_pack.md`

Reports include pack ID, source input summary, exact proposal table, blocked
proposal table, before/after diff, evidence references, risk notes, human review
checklist, approval requirements, rollback notes, explicit statement that no
settings were changed, and explicit statement that live execution remains
blocked.

## Rollback

Rollback is a normal revert of the Phase 54 merge commit. No database migration,
external service setup, live configuration, or secret material is introduced.

## Next Step

Phase 55 should continue with offline reconciliation or simulation-quality
review work. Any future exact calibration change must be a separate reviewed
implementation phase and must still avoid live execution unless a later named
phase explicitly authorizes it after safety review.
