# Phase 61 Research Notes - Xaman Manual Approval Design Spec

## Official sources reviewed

- Xaman payload concepts and lifecycle docs
- XRPL transaction common fields and transaction-type docs
- XRPL reliable transaction submission guidance (future-risk context)
- GitHub security docs: dependency review, code scanning/CodeQL, secret scanning push protection

## Risk-driven findings

1. Xaman payload workflows are approval/signing surfaces and must be isolated from current paper runtime.
2. Replay protection needs explicit TTL/expiry and unique identifiers in any future implementation.
3. Consent UX requires explicit approve/reject/cancel and risk disclosure; no implicit approval.
4. Submission verification must be treated as a separate concern from submission initiation.
5. CI safety gates should continue enforcing docs/safety/dependency checks before merge.

## Unsafe patterns explicitly rejected

- private-key/seed capture
- hidden signing or submission helpers
- auto-approval callbacks
- discovery-to-execution coupling
- websocket listeners that mutate state without human review
- runtime mutation from design/policy outputs

## Why this Phase 61 approach is safe

- Spec models are pure data and deterministic.
- No payload/API/SDK calls are implemented.
- Explicit fail-closed markers block payload/sign/submit/wallet/live attempts.
- Future testnet/mainnet gates remain blocked in outputs.
