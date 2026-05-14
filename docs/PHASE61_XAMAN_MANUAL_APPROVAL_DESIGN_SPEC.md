# Phase 61 Xaman Manual Approval Design Spec

## Scope

Phase 61 is a design-spec-only phase for a future Xaman manual approval flow.

- design_spec_only=True
- manual_approval_required=True
- payload_creation_allowed=False
- signing_allowed=False
- submission_allowed=False
- autofill_allowed=False
- wallet_material_allowed=False
- live_execution_allowed=False
- runtime_mutation_allowed=False

## What Phase 61 adds

- Deterministic spec-only models under `src/sonic_xrpl/xaman_manual_approval_spec/`.
- Deterministic approval lifecycle contracts for manual human review.
- Deterministic threat-model and blocker-register outputs.
- Deterministic fixtures and tests for blocked unsafe markers.
- Offline CLI commands for spec/report rendering only.

## Explicit non-goals

Phase 61 does not:

- create Xaman payloads
- call Xaman APIs
- add Xaman SDK dependencies
- implement signing
- implement submission
- implement autofill
- use wallets or wallet seed/private-key material
- implement testnet execution
- implement mainnet execution
- authorize live execution

## Approval lifecycle contract (design only)

1. Candidate is selected from Phase 59/60 paper-only outputs.
2. Operator reviews evidence, limitations, and risk disclosures.
3. System produces a future-intent summary only.
4. Human explicitly approves, rejects, or cancels in future design.
5. No payload is created in Phase 61.
6. No signing/submission is possible in Phase 61.
7. Future payload creation requires a separate explicit phase.
8. Future testnet implementation requires a separate explicit phase.
9. Future mainnet live execution requires separate explicit approval.

## Future safety gates

Any future Xaman implementation phase must preserve:

- audit logs (append-only + decision actor/timestamp)
- replay protection (nonce + TTL/expiry + idempotency)
- explicit cancellation paths
- risk disclosures and non-investment-advice messaging
- testnet-only gating before any mainnet consideration

## Canonical-path and safety alignment

- Canonical future runtime remains `src/sonic_xrpl/`.
- `execution_prototype/` Xaman helpers remain historical/reference-only.
- Live execution remains fail-closed and blocked.
