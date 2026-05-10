# Phase 55 - Human Review Approval Ledger

Phase 55 adds an offline approval-ledger layer that consumes Phase 54
calibration proposal packs and human review fixtures, then produces deterministic
approval records and change-request records for manual governance.

This phase does not apply calibration. It does not change runtime settings,
signal thresholds, risk settings, provider settings, mode settings, safety gates,
or execution settings.

## Scope

- New package: `src/sonic_xrpl/calibration_approval/`
- CLI commands:
  - `calibration-approval-ledger`
  - `calibration-change-requests`
  - `calibration-approval-report`
- Fixtures: `tests/fixtures/calibration_approval/`
- Reports: `reports/phase55/calibration_approval_ledger.json` and `.md`
- Tests: Phase 55 unit, smoke, and safety tests

## Approval Rules

Approval records are generated only for proposals that are explicitly marked
approved in the review fixture and retain human-review-only safety flags.

Records are blocked when:

- proposal safety flags are missing or invalid
- review status is rejected, deferred, or incomplete
- evidence references are missing
- requested changes exceed conservative review limits

Approved records remain paper-only and non-mutating. They are governance output
for a later manual implementation phase, not direct runtime updates.

## Change Request Rules

Change-request records are produced for rejected, deferred, or modified reviews.
They preserve:

- proposal identifiers and parameter keys
- reviewer rationale
- explicit requested edits
- risk notes and rollback notes

These records are deterministic and append-only in report output.

## Safety Boundary

Phase 55 is paper-only, offline-only, non-mutating, and human-review-only.

It does not:

- enable live trading
- fetch live FirstLedger, XRPL, Clio, or rippled data
- use Xaman
- create transactions
- sign or submit anything
- start polling, streaming, daemon, or background execution
- alter calibration thresholds automatically
- claim profitability or execution readiness

All approval-ledger outputs keep:

- `paper_only=True`
- `human_review_required=True`
- `auto_apply_allowed=False`
- `live_execution_allowed=False`

## Reports

The report writer creates:

- `calibration_approval_ledger.json`
- `calibration_approval_ledger.md`

Reports include proposal input summary, approval table, blocked table, change
request table, reviewer notes, risk notes, rollback notes, and explicit
statements that no settings were changed and live execution remains blocked.

## Rollback

Rollback is a normal revert of the Phase 55 merge commit. No database migration,
external service setup, live configuration, or secret material is introduced.

## Next Step

Phase 56 should continue with offline implementation planning for manually
approved calibration changes, with strict change-control and revalidation.
