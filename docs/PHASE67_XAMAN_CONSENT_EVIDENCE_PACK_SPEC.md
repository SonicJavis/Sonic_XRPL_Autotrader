# Phase 67 - Xaman Testnet Operator Consent Evidence Pack Spec

## Scope

Phase 67 adds a non-executing evidence-pack contract layer under
`src/sonic_xrpl/xaman_consent_evidence_pack_spec/`.

This phase is spec-only and fixture-backed. It defines:

- evidence-pack envelope requirements
- required cross-phase references and traceability matrix requirements
- evidence completeness requirements
- fail-closed blocked marker handling for prohibited capabilities

## Explicit non-goals

Phase 67 does not implement:

- UI/dashboard views or frontend routes
- API routes or runtime evidence services
- export/download/file-write implementations
- persistence/database writes/migrations
- callback/webhook runtime handlers
- Xaman SDK/API calls or payload creation
- signing/submission/autofill
- wallet seed/private-key handling
- testnet/live execution

## Safety contract flags

Phase 67 safety flags are enforced in models and tests:

- `evidence_pack_spec_only=True`
- `export_implementation_allowed=False`
- `file_write_allowed=False`
- `ui_implementation_allowed=False`
- `api_route_allowed=False`
- `runtime_service_allowed=False`
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

Phase 67 outputs non-executing outcomes only:

- `EVIDENCE_PACK_VALID`
- `EVIDENCE_PACK_REVIEW_REQUIRED`
- `EVIDENCE_PACK_INVALID`
- `EVIDENCE_PACK_BLOCKED`
- `INSUFFICIENT_EVIDENCE`

No output implies execution authorization.
