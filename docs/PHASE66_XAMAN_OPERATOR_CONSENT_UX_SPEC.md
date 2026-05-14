# Phase 66 - Xaman Testnet Operator Consent UX Contract Spec

## Scope

Phase 66 adds a non-executing operator consent UX contract layer under
`src/sonic_xrpl/xaman_operator_consent_ux_spec/`.

This phase is spec-only and fixture-backed. It defines:

- required operator disclosures
- acknowledgement and confirmation phrase requirements
- rejection/cancellation requirements
- operator identity and audit-binding requirements
- fail-closed marker handling for unsafe consent patterns

## Explicit non-goals

Phase 66 does not implement:

- UI screens, dashboard views, or frontend routes
- API routes or runtime consent services
- callback handlers or webhook runtime verification
- persistence implementation, database writes, or migrations
- Xaman SDK/API calls or payload creation
- signing, submission, or autofill
- wallet seed/private-key handling
- testnet or live execution

## Safety contract flags

Phase 66 safety flags are enforced in models and tests:

- `ux_contract_spec_only=True`
- `ui_implementation_allowed=False`
- `api_route_allowed=False`
- `runtime_consent_service_allowed=False`
- `persistence_implementation_allowed=False`
- `database_writes_allowed=False`
- `callback_handler_allowed=False`
- `webhook_runtime_allowed=False`
- `payload_creation_allowed=False`
- `xaman_api_calls_allowed=False`
- `signing_allowed=False`
- `submission_allowed=False`
- `wallet_material_allowed=False`
- `testnet_execution_allowed=False`
- `live_execution_allowed=False`

## Outcome semantics

Phase 66 outputs non-executing outcomes only:

- `CONSENT_SPEC_VALID`
- `CONSENT_SPEC_REVIEW_REQUIRED`
- `CONSENT_SPEC_INVALID`
- `CONSENT_BLOCKED`
- `INSUFFICIENT_EVIDENCE`

No output implies execution authorization.
