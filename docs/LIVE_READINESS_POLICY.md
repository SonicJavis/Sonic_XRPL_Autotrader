# Live Readiness Policy

## Phase 58B policy status

- Live trading remains blocked after Phase 58, Phase 58A, and Phase 58B.
- Phase 58B is policy/spec hardening only and does not authorize live trading.
- A future dedicated live-enablement phase is required before any live execution work.

## Explicit blocked capabilities

The following remain blocked in this repository:

- transaction signing
- transaction submission
- transaction autofill
- wallet seed/private-key handling
- Xaman payload creation
- FirstLedger live ingestion
- runtime mutation from policy/review outputs
- FULL_AUTO or autonomous execution loops

## Human approval requirement

Live execution cannot be enabled by default, CI success, or agent assumption.
It requires explicit human approval in a dedicated future live-enablement phase.

## Mandatory future live-readiness gates

Any future live-readiness phase must provide and pass all of the following:

1. blocker register with unresolved blocker handling
2. threat model for wallet/signing/submission surfaces
3. dependency audit and supply-chain verification
4. secrets-management and key-material handling plan
5. rollback and incident-response plan
6. kill-switch design and verification
7. append-only audit logging requirements
8. manual approval gates with named approvers and recorded decisions

## Safety continuity statement

Phase 58B introduces no runtime behavior changes.
All existing fail-closed safety boundaries remain authoritative.
