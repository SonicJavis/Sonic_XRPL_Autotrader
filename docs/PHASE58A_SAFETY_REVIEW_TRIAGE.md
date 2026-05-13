# Phase 58A Safety-Scan REVIEW Triage Policy

## Purpose

This policy defines how `REQUIRES_REVIEW` findings from `src/sonic_xrpl/audit/safety_scan.py` are triaged during Phase 58A.

It does not authorize live trading, signing, submission, autofill, wallet material handling, Xaman payload creation, runtime mutation, or threshold auto-apply.

## Scope

Applies to:

- Local runs of `python -m sonic_xrpl.cli.main safety-scan`
- CI runs that execute safety scan jobs
- Manual security review of findings in:
  - `app/`
  - `src/sonic_xrpl/`
  - `scripts/`
  - `.github/workflows/`
  - `dashboard/`
  - `execution_prototype/`

## Classification Semantics

`safety_scan` classifications are interpreted as:

- `ALLOWED_DOCUMENTATION`: expected in docs/comments.
- `ALLOWED_TEST_FIXTURE`: expected in tests/fixtures.
- `ALLOWED_INTERFACE_ONLY`: expected in blocked interfaces/guards.
- `REQUIRES_REVIEW`: pattern appears in runtime-context code and must be manually triaged.
- `BLOCKED`: explicit unsafe implementation path; must fail.

## Triage Rules

For each `REQUIRES_REVIEW` finding:

1. Confirm file role
- Determine whether the file is runtime, test-only, docs-only, or historical/prototype reference.
- Treat `app/` and `src/sonic_xrpl/` as runtime-sensitive.

2. Confirm behavior
- Verify the line does not create or enable:
  - signing
  - submission
  - autofill
  - wallet creation/seed/private-key handling
  - background execution loops
  - live execution enablement

3. Confirm guard posture
- Verify fail-closed controls remain intact:
  - `app/execution/execution_guard.py`
  - `src/sonic_xrpl/execution/live_guard.py`
  - runtime profile conformance and safety/audit checks

4. Classify triage outcome
- `TRIAGE_OK_CONTEXT`: non-executable mention in safe context.
- `TRIAGE_NEEDS_PATCH`: ambiguous or risky code that requires follow-up patching.
- `TRIAGE_BLOCKER`: active unsafe behavior or bypass path.

5. Record evidence
- Include file path, line, reason, and reviewer decision in the phase report.

## CI Interpretation

- Any `BLOCKED` finding is a hard fail.
- `REQUIRES_REVIEW` findings are not auto-promoted to pass; they require explicit human review notes.
- Missing evidence should stay conservative (`REVIEW`), never assumed `PASS`.

## Guard-Critical Change Detection Link

Phase 58A adds explicit guard-critical changed-file detection through:

- `scripts/guard_critical_changes.py`

This check surfaces edits to critical safety boundaries so they receive explicit security review attention before merge.

## Out of Scope

This phase does not implement:

- live order placement
- XRPL transaction signing/submission/autofill
- wallet seed/private key handling
- Xaman payload creation
- automated sniper execution

All such capabilities remain blocked unless a later explicitly approved phase changes policy and passes security gates.
