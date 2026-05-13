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
