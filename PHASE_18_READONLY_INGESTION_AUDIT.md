# Phase 18 Read-Only XRPL Ingestion Audit

## Scope

Phase 18 adds read-only XRPL ingestion plumbing behind the existing `ShadowSnapshotSource` abstraction. It does not enable trading, does not start a background network loop, and does not connect to XRPL on import.

## Read-Only Guarantee

- The WebSocket adapter only permits ledger observation subscription commands.
- The book adapter only consumes injected mockable snapshot response clients.
- The snapshot source converts read-only ledger/book observations into advisory `ShadowSnapshotInput` objects.
- Ingestion is disabled by default through configuration.

## No Wallet / Signing / Broadcast Guarantee

- No wallet object is imported or used by the Phase 18 ingestion modules.
- No signing, autofill, transaction creation, or transaction broadcast path is added.
- No XRPL write operation is reachable from the ingestion API or dashboard.

## Transaction Creation Guarantee

Phase 18 does not construct OfferCreate, Payment, or any other XRPL transaction payload. The adapter validates outbound commands and rejects non-observation command names.

## XRPL Observation Limits

- Ledger subscription is observation only and is not execution.
- `book_offers` is treated as request/response snapshot polling, not a continuous CEX-style orderbook stream.
- Observed offers may be stale, unfunded, partially funded, or non-executable.
- No mempool visibility is assumed.
- Pathfinding can change between ledgers.

## Fail-Closed Behaviour

- Missing ledger events return `None`.
- Malformed ledger messages return `None`.
- Empty or malformed book snapshots return `None`.
- Stale ledger mismatches are rejected.
- Snapshot source defaults route instability and competition penalty to conservative nonzero values.
- Ingestion status returns safe disabled metadata when no adapter is configured.

## API Safety Review

`GET /live/ingestion/status` is read-only. It does not start ingestion, mutate trading configuration, submit transactions, or expose raw secret-bearing payloads.

## Dashboard Safety Review

The dashboard displays disabled/default ingestion health locally and does not start network ingestion. Warnings explicitly state that observation is read-only and observed liquidity may not execute.

## Validation

- Pytest result: `327 passed in 33.83s`
- Safety grep judgement: no new reachable wallet, signing, transaction submission, autofill, OfferCreate execution, Payment execution, or live trading path introduced. Matches are existing `signal/signals` false positives, pre-existing fail-closed wallet/transaction placeholders, and test-only forbidden-command assertions.
