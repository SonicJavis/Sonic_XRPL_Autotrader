# Phase 67 Research - Xaman Consent Evidence Pack Spec

## Official-source-first references

- Xaman developer docs (payload/status lifecycle context)
- XRPL docs (transaction/common-field risk framing context)
- GitHub security docs (review traceability and governance context)
- Secure SDLC references for evidence bundles and human-in-the-loop controls

## Key findings applied

1. Consent decisions need explicit, complete evidence bundles.
2. Cross-artifact traceability should be explicit, not implicit.
3. Missing evidence must remain visible and fail closed.
4. Blocker status must remain explicit for testnet/live boundaries.
5. Evidence-pack design must not imply payload creation or execution readiness.

## Rejected unsafe patterns

- executable approval packages
- payload generation from evidence packs
- wallet/secret inclusion in evidence contracts
- export/download and runtime service implementation in this phase
- UI/API integration in this phase

## Phase 67 implementation posture

Phase 67 remains non-executing and contract-only:

- no UI/API/runtime implementation
- no export/download/file-write implementation
- no persistence/database implementation
- no payload/API/signing/submission/wallet handling
- no testnet/live execution

Still no live execution.
