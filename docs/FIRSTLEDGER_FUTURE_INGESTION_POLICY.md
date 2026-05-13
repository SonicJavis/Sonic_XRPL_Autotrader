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
