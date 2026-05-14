# Phase 66 Research - Xaman Operator Consent UX Contract Spec

## Official-source-first references

- Xaman developer documentation (approval flow and payload lifecycle context)
- XRPL documentation (transaction lifecycle and approval-risk context)
- GitHub security guidance (human-in-the-loop and review controls)
- Secure SDLC guidance for consent UX and high-risk confirmation flows

## Key findings applied

1. High-risk actions require explicit operator acknowledgement and clear
   disclosure copy.
2. Consent surfaces must make uncertainty visible (stale/missing evidence).
3. Rejection/cancellation must remain explicit and first-class.
4. Identity and audit binding requirements should be part of contract design.
5. Auto-approval and one-click execution patterns are unsafe for this repo.

## Rejected unsafe patterns

- auto-approval flows
- one-click execution flows
- hidden or omitted risk disclosures
- wallet material collection in consent UX
- coupling consent copy to immediate signing/submission

## Phase 66 implementation posture

Phase 66 remains non-executing and contract-only:

- no UI implementation
- no API/runtime implementation
- no persistence implementation
- no payload/API/signing/submission/wallet handling
- no testnet/live execution

Still no live execution.
