# Canonical Runtime Ownership Policy

## Authoritative runtime ownership

- `src/sonic_xrpl/` is the canonical future runtime target.
- `app/` is the current runnable legacy API/paper runtime surface.
- `execution_prototype/` is historical/reference-only unless named tests or bridge adapters explicitly use it.

## Runtime authority restrictions

- No future feature may assign new runtime authority to `execution_prototype/`.
- `app/` must not receive new trading/execution authority.
- Historical prototype code is not canonical runtime authorization.

## Migration boundary

Migration/cutover work is separate from Phase 58B and is not implemented here.
Any future runtime cutover must pass parity gates and safety gates before runtime ownership changes.

## Safety continuity statement

This policy clarifies ownership boundaries only.
It does not authorize signing, submission, autofill, wallet material handling, Xaman payloads, or FirstLedger live ingestion.
