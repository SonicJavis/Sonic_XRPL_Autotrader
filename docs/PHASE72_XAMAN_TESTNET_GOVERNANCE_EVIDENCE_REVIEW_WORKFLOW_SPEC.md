# Phase 72 - Xaman Testnet Governance Evidence Review Workflow Spec

## Summary

Phase 72 adds a deterministic, fixture-backed governance evidence review
workflow specification under
`src/sonic_xrpl/xaman_governance_evidence_review_workflow_spec/`.

This phase is review-workflow-spec-only and non-executing.

## Scope

- Defines workflow stage/role/status contracts for governance evidence review.
- Defines deterministic handoff and escalation records.
- Defines conservative transition behavior and fail-closed blocker handling.
- Defines traceability output from workflow stages to evidence, attestations,
  domains, and blockers.
- Adds fixture-backed JSON/Markdown reporting.
- Adds offline fixture-only CLI commands:
  - `xaman-governance-evidence-review-workflow-spec`
  - `xaman-governance-evidence-review-workflow-spec-report`

## Explicit Safety Boundary

Phase 72 does not implement:

- runtime workflow engine
- callback/webhook runtime
- API routes or dashboard/UI screens
- persistence/database writes
- export/download features beyond deterministic report writing
- Xaman payload creation
- Xaman API calls or SDK integration
- signing/submission/autofill
- wallet seed/private-key handling
- testnet execution
- live execution

Required safety flags remain hard-blocked:

- `spec_only=True`
- `workflow_spec_only=True`
- `runtime_workflow_allowed=False`
- `testnet_execution_allowed=False`
- `xaman_payload_creation_allowed=False`
- `xaman_api_calls_allowed=False`
- `xaman_sdk_dependency_allowed=False`
- `signing_allowed=False`
- `submission_allowed=False`
- `autofill_allowed=False`
- `wallet_material_allowed=False`
- `live_execution_allowed=False`
- `runtime_mutation_allowed=False`

## Deterministic Inputs and Outputs

- Fixtures:
  `tests/fixtures/xaman_governance_evidence_review_workflow_spec/`
- Unit tests:
  `tests/unit/test_phase72_xaman_governance_evidence_review_workflow_spec.py`
- Safety tests:
  `tests/safety/test_phase72_xaman_governance_evidence_review_workflow_safety.py`
- Reports:
  - `reports/phase72/latest_xaman_governance_evidence_review_workflow_spec.json`
  - `reports/phase72/latest_xaman_governance_evidence_review_workflow_spec.md`

## Final Confirmation

- Still no live execution.
- Still no testnet execution.
- Still no Xaman payload creation.
- Still no runtime workflow engine.
