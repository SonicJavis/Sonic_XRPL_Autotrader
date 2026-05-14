# FirstLedger Future Ingestion Policy

## Current status

- Current FirstLedger capability is fixture/source-backed signal evidence only.
- No production live FirstLedger adapter is authorized.
- No FirstLedger signal can directly trigger live execution.

## Future-ingestion requirements

Any future FirstLedger ingestion design must include:

1. source provenance validation
2. source trust scoring
3. stale/missing evidence handling
4. replay-protection controls
5. rate-limit and backoff policy
6. fail-closed classification behavior
7. explicit operator-review checkpoints

## Execution coupling restrictions

- Synthetic evidence cannot become `BUY_CANDIDATE`.
- FirstLedger live ingestion must remain decoupled from live execution paths.
- Live coupling to execution remains blocked.

## Safety continuity statement

Phase 58B does not add runtime collectors, background workers, live ingestion adapters, or strategy execution triggers.

## Phase 59 continuity note

Phase 59 expands FirstLedger intelligence quality under
`src/sonic_xrpl/firstledger_intelligence/` with deterministic fixture-backed,
source-provenance-aware scoring and reporting only.

Phase 59 does not authorize live FirstLedger ingestion, live network calls,
order execution, signing, submission, autofill, wallet handling, or Xaman
payload workflows.

## Phase 60 continuity note

Phase 60 adds paper-only sniper simulation under
`src/sonic_xrpl/paper_sniper_simulation/` using deterministic fixtures and
explicit assumptions.

Phase 60 does not authorize live FirstLedger ingestion, network collectors,
order execution, signing, submission, autofill, wallet handling, or Xaman
payload workflows.
