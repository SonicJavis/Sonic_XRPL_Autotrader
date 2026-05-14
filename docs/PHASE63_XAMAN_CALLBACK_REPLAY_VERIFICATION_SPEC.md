# Phase 63 - Xaman Callback Authenticity + Replay Verification Spec

## Scope

Phase 63 is a non-executing callback authenticity and replay-verification
specification layer for future Xaman testnet workflows.

- callback_spec_only=True
- verification_design_only=True
- runtime_callback_handler_allowed=False
- webhook_runtime_allowed=False
- payload_creation_allowed=False
- xaman_api_calls_allowed=False
- signing_allowed=False
- submission_allowed=False
- autofill_allowed=False
- wallet_material_allowed=False
- testnet_execution_allowed=False
- live_execution_allowed=False
- manual_approval_required=True

## Implemented evidence

- `src/sonic_xrpl/xaman_callback_verification_spec/models.py`
- `src/sonic_xrpl/xaman_callback_verification_spec/loader.py`
- `src/sonic_xrpl/xaman_callback_verification_spec/verification.py`
- `src/sonic_xrpl/xaman_callback_verification_spec/threat_model.py`
- `src/sonic_xrpl/xaman_callback_verification_spec/reporting.py`
- `tests/fixtures/xaman_callback_verification_spec/`
- `tests/unit/test_phase63_xaman_callback_verification_spec.py`
- `tests/safety/test_phase63_xaman_callback_verification_safety.py`
- CLI commands:
  - `xaman-callback-verification-spec`
  - `xaman-callback-verification-spec-report`

## Design-review outputs

- Callback authenticity checklist requirements.
- Required callback/prohibited field requirements.
- Correlation ID and payload UUID binding requirements.
- Candidate + paper-simulation + operator-consent linkage requirements.
- Nonce, TTL, replay window, idempotency, duplicate handling, and callback
  ordering requirements.
- Cancellation/rejection and audit-trail checklist requirements.
- Future testnet gate checklist and live-readiness blocker register outputs.

## Not authorized by Phase 63

- No callback handler implementation.
- No webhook runtime verification implementation.
- No API routes or FastAPI handlers.
- No Xaman payload creation.
- No Xaman API calls or SDK integration.
- No signing/submission/autofill/wallet handling.
- No testnet execution implementation.
- No live/mainnet execution implementation.
- No runtime mutation or execution-path changes.

Still no live execution.
