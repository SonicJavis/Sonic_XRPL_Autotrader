# Phase 74 - Xaman Testnet Governance Exception Waiver Register Spec

## Summary

Phase 74 adds a deterministic, fixture-backed governance exception waiver register specification under
`src/sonic_xrpl/xaman_governance_exception_waiver_register_spec/`.

This phase is exception-waiver-register-spec-only and non-executing.

## Scope

- Defines waiver roles, domains, severities, statuses, expiry/revocation rules, and unsafe waiver blockers.
- Defines deterministic waiver request records linked to Phase 70-73 governance artifacts.
- Defines conservative readiness classifications: `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_REVIEW_READY`, `EXPIRED`, `REVOKED`, `BLOCKED`.
- Defines traceability from waiver records to prior governance artifacts and blocker categories.
- Adds fixture-backed JSON/Markdown reporting.
- Adds offline fixture-only CLI commands:
  - `xaman-governance-exception-waiver-register-spec`
  - `xaman-governance-exception-waiver-register-spec-report`

## Explicit Safety Boundary

Phase 74 does not implement:

- runtime waiver service
- safety bypass
- Xaman payload creation
- Xaman API calls or SDK integration
- signing/submission/autofill
- wallet seed/private-key handling
- testnet execution
- live execution
- runtime mutation
- callbacks/webhooks, persistence, API routes, or dashboard/UI screens

Required safety flags remain hard-blocked:

- `spec_only=True`
- `waiver_register_spec_only=True`
- `runtime_waiver_service_allowed=False`
- `safety_bypass_allowed=False`
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

Phase 74 is a prerequisite waiver-control layer for future consideration only.

## Deterministic Inputs and Outputs

- Fixtures: `tests/fixtures/xaman_governance_exception_waiver_register_spec/`
- Unit tests: `tests/unit/test_phase74_xaman_governance_exception_waiver_register_spec.py`
- Safety tests: `tests/safety/test_phase74_xaman_governance_exception_waiver_register_safety.py`
- Reports:
  - `reports/phase74/latest_xaman_governance_exception_waiver_register_spec.json`
  - `reports/phase74/latest_xaman_governance_exception_waiver_register_spec.md`

## Final Confirmation

- Still no live execution.
- Still no testnet execution.
- Still no Xaman payload creation.
- Still no runtime waiver service.
- Still no safety bypass.
