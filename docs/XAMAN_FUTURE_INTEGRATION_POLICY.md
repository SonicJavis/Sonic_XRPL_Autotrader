# Xaman Future Integration Policy

## Current status

- Xaman is future/manual-approval-only.
- No V2 Xaman payload creation implementation exists today.
- Historical `execution_prototype` Xaman helpers are non-canonical reference material.

## Design-spec-first requirement

Any future Xaman work must begin with a design spec before implementation.
The design spec must define:

1. payload lifecycle states and transitions
2. explicit user-consent UX and confirmation semantics
3. append-only audit trail requirements
4. replay-protection rules
5. secrets/key-material handling boundaries
6. failure modes, rejection handling, and rollback behavior

## Explicitly blocked in Phase 58B

- no Xaman payload creation code
- no signing implementation
- no transaction submission implementation
- no transaction autofill implementation
- no wallet seed/private-key handling implementation

## Approval boundary

No Xaman signing/submission path may be implemented without explicit future human approval in a dedicated live-enablement phase.

## Phase 61 continuity note

Phase 61 adds design-spec-only contracts under
`src/sonic_xrpl/xaman_manual_approval_spec/`.

Phase 61 does not create payloads, call Xaman APIs, add Xaman SDK
dependencies, implement signing/submission/autofill, use wallet material, or
authorize testnet/mainnet execution.

## Phase 62 continuity note

Phase 62 adds testnet payload schema and verification design-review contracts
only under `src/sonic_xrpl/xaman_testnet_payload_spec/`.

Phase 62 does not create payloads, call Xaman APIs, add Xaman SDK
dependencies, implement signing/submission/autofill, or authorize testnet or
mainnet execution.

## Phase 63 continuity note

Phase 63 adds callback authenticity and replay-verification design contracts
only under `src/sonic_xrpl/xaman_callback_verification_spec/`.

Phase 63 does not add callback handlers, webhook runtime verification, API
routes, payload creation, Xaman API calls, SDK dependencies, signing,
submission, autofill, wallet material handling, testnet execution, or mainnet
execution.
