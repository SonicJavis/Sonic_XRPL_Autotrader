# Phase 46 Research: Provider Fixture System

## Research Summary

Phase 46 research covers the design decisions behind the structured fixture system for offline XRPL provider testing.

## Key Research Questions

### 1. Why not use Mock providers for all tests?

Mock providers return deterministic but **arbitrary** data. They do not reflect real XRPL ledger structure, real account balances, or real transaction metadata. For testing:

- Metadata parsing correctness
- Balance change extraction
- PnL attribution logic
- AMM pool state representation

...mock providers are insufficient. Structured fixtures with real-shape data are required.

### 2. Why JSONL for account_tx?

XRPL `account_tx` responses can be large. JSONL (newline-delimited JSON) allows:

- Streaming processing without loading entire file
- Ledger range filtering without full parse
- Easy append for incremental test data

### 3. Why separate `FixtureManifest`?

The manifest provides:

- **Traceability**: source URLs, creation date, network identifier
- **Integrity**: deterministic checksum prevents silent mutation
- **Range checking**: `ledger_min`/`ledger_max` for stale data detection
- **Audit trail**: limitations documented alongside data

### 4. Why does `FixtureLedgerProvider` NOT fall back to mock?

Silent fallback to mock data hides missing fixtures and can produce false-passing tests. Phase 46 mandates explicit `FixtureMissingError` so tests fail clearly when fixture data is absent.

### 5. Metadata Parser Design

XRPL transaction metadata is the **only sufficient truth** for:
- Delivered amounts (partial payments)
- Actual balance changes
- AMM pool state transitions

The parser explicitly flags `tesSUCCESS` with no `AffectedNodes` as "not sufficient truth" — this is a known XRPL edge case where result code alone cannot determine execution outcome.

### 6. Secret Pattern Selection

Fixture safety scan checks for: `seed`, `private_key`, `mnemonic`

Deliberately **excluded** from scan: `secret` — because `tesSUCCESS` contains "ess" which does not trigger but `secret` in a fixture key would be a false positive concern. The current patterns target real credential patterns only.

## XRPL Fixture Data Shape Reference

### AccountRoot LedgerEntry
```json
{
  "Account": "r...",
  "Balance": "1000000000",
  "Flags": 0,
  "Sequence": 1
}
```

### RippleState LedgerEntry (trust line)
```json
{
  "Balance": {"currency": "USD", "issuer": "r...", "value": "100"},
  "LowLimit": {"currency": "USD", "issuer": "rTrader...", "value": "1000"},
  "HighLimit": {"currency": "USD", "issuer": "rIssuer...", "value": "0"}
}
```

### AMM LedgerEntry
```json
{
  "amount": "1000000000",
  "amount2": {"currency": "USD", "issuer": "r...", "value": "1000"},
  "lp_token": {"currency": "...", "issuer": "r...", "value": "100"},
  "trading_fee": 500,
  "amm_account": "r..."
}
```

## ProviderType Enum Extension

`ProviderType.FIXTURE = "fixture"` was added to the enum to distinguish fixture-backed providers from mock providers in health checks and audit logs.

## FailoverProvider Enhancement

Phase 46 adds `last_failover_reasons` property to `FailoverProvider` to support observability and debugging of provider failover chains. Reasons are reset on each `_call` invocation.

## Health System Extension

`HealthStatus` enum and `FixtureHealthReport` dataclass were added to `health.py` to provide structured fixture health reporting analogous to provider health checking.

## Audit Integration

Phase 46 docs are added to `REQUIRED_DOCS` in `docs_check.py` so the V2 audit validator enforces their presence.
