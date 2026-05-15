# Phase 68 - Xaman Testnet Preflight Safety Checklist Spec

## Scope

Phase 68 adds a deterministic, fixture-backed, non-executing preflight safety
checklist contract layer under:

- `src/sonic_xrpl/xaman_preflight_safety_checklist_spec/`

This phase is spec-only and checklist-contract-only.

## What Phase 68 Defines

- preflight checklist envelope and checklist ID contracts
- required gate contracts for:
  - evidence-pack
  - payload schema
  - callback verification
  - audit/idempotency
  - approval state machine
  - operator consent UX
  - dependency/safety/audit/migration/guard-critical checks
- no-secrets, no-wallet-material, no-Xaman-API, no-payload-created,
  no-signing/submission, no-testnet-execution, and no-live-execution gates
- rollback-plan and kill-switch-design requirements
- deterministic report/checklist output contracts

## Explicit Non-Authorization

Phase 68 does **not** authorize:

- runtime checklist runner implementation
- UI implementation or dashboard changes
- API routes or runtime services
- export/download/file-write implementation
- persistence or database writes
- callback handlers or webhook runtime
- Xaman SDK/API integration
- payload creation
- signing/submission/autofill
- wallet seed/private-key handling
- testnet execution
- live execution

## Safety Flags

Phase 68 safety flags remain fail-closed and include:

- `preflight_spec_only=True`
- `runtime_checklist_runner_allowed=False`
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

## Outcome Contract

Phase 68 returns non-executing outcomes only:

- `PREFLIGHT_SPEC_VALID`
- `PREFLIGHT_SPEC_REVIEW_REQUIRED`
- `PREFLIGHT_SPEC_INVALID`
- `PREFLIGHT_BLOCKED`
- `INSUFFICIENT_EVIDENCE`

Still no live execution.
