# Phase 65 - Xaman Testnet Approval State Machine Design Spec

## Scope

Phase 65 is a non-executing design specification layer for a future Xaman
approval state machine.

- state_machine_spec_only=True
- runtime_state_machine_allowed=False
- persistence_implementation_allowed=False
- database_writes_allowed=False
- callback_handler_allowed=False
- webhook_runtime_allowed=False
- payload_creation_allowed=False
- xaman_api_calls_allowed=False
- signing_allowed=False
- submission_allowed=False
- wallet_material_allowed=False
- testnet_execution_allowed=False
- live_execution_allowed=False

## Implemented evidence

- `src/sonic_xrpl/xaman_approval_state_machine_spec/models.py`
- `src/sonic_xrpl/xaman_approval_state_machine_spec/states.py`
- `src/sonic_xrpl/xaman_approval_state_machine_spec/transitions.py`
- `src/sonic_xrpl/xaman_approval_state_machine_spec/validation.py`
- `src/sonic_xrpl/xaman_approval_state_machine_spec/reporting.py`
- `src/sonic_xrpl/xaman_approval_state_machine_spec/loader.py`
- `tests/fixtures/xaman_approval_state_machine_spec/`
- `tests/unit/test_phase65_xaman_approval_state_machine_spec.py`
- `tests/safety/test_phase65_xaman_approval_state_machine_safety.py`
- CLI commands:
  - `xaman-approval-state-machine-spec`
  - `xaman-approval-state-machine-spec-report`

## Design outputs

- Allowed design-only states for review/callback-verification/audit/final-spec
  outcomes.
- Transition contracts with required evidence, audit/idempotency/replay/TTL,
  and human approval requirements.
- Explicit invalid transition rules for payload/API/signing/submission/wallet/
  testnet/live/runtime paths.
- Deterministic outcome classification:
  `SPEC_VALID`, `SPEC_REVIEW_REQUIRED`, `SPEC_INVALID`,
  `TRANSITION_BLOCKED`, `INSUFFICIENT_EVIDENCE`.

## Not authorized by Phase 65

- No runtime state machine implementation.
- No persistence implementation or DB writes.
- No callback handler or webhook runtime implementation.
- No API routes.
- No Xaman API/SDK integration.
- No payload creation, signing, submission, autofill, or wallet handling.
- No testnet/live execution.
- No runtime mutation or execution-path changes.

Still no live execution.
