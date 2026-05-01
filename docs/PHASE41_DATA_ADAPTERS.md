# Phase 41: Read-Only Historical Data Adapters

## Purpose
Phase 41 introduces a read-only historical data collection layer. It provides standardized adapters for fetching historical transaction and ledger data from XRPL, Clio, and FirstLedger, then normalizing it into Phase 40-compatible fixture files. This ensures that the paper trading sandbox has a continuous supply of high-quality, deterministic market data.

## Research Sources Checked
- **XRPL Known Amendments**: AMM, AMMClawback, Clawback, MPT, DID enabled.
- **Batch Safety**: `fixBatchInnerSigs` (v3.1.0) enabled to address 2026-02-19 vulnerability.
- **Clio v2.1.0**: Confirmed `account_tx` supports `tx_type` filtering and full AMM integration.
- **xrpl-py**: Verified `get_balance_changes(metadata)` availability for metadata parsing.
- **FirstLedger**: Public API `api.firstledger.net` verified for historical trade collection.

## Supported Sources
1. **fixture** (Default): Reads local raw data files and normalizes them.
2. **clio**: Fetches validated transactions via `account_tx` with optional `tx_type` filtering.
3. **xrpl_rpc**: General-purpose read-only RPC for ledger/transaction inspection.
4. **firstledger**: Specialized trade history collection for DEX memes.

## Absolute Safety: Read-Only & Disabled-by-Default
All network adapters are strictly **disabled by default**. 
- Network access requires the explicit `--enable-network-read` flag.
- **NO WALLET**: No wallet or private key logic is included.
- **NO SIGNING**: No transaction signing primitives.
- **NO SUBMISSION**: No write-access methods enabled.
- **BOUNDED QUERIES**: All network requests require ledger bounds or record/page limits to prevent runaway ingestion.

## Normalization Truth Rules
- **Delivered Amount**: For Payment analysis, the system strictly uses `meta.delivered_amount` to account for partial payments.
- **AffectedNodes**: Required for accurate balance-change reconstruction.
- **Confidence**: If metadata is missing or incomplete, fixtures are marked as `low` confidence.

## How to Run (Fixture Mode)
```bash
python -m execution_prototype.data_adapters.cli \
    --source fixture \
    --input ./fixtures/raw \
    --output-dir ./fixtures/generated \
    --dry-run
```

## How to Run (Clio Bounded Mode)
```bash
python -m execution_prototype.data_adapters.cli \
    --source clio \
    --endpoint https://clio.xrpl.org \
    --account r... \
    --ledger-min 90000000 \
    --ledger-max 90001000 \
    --enable-network-read \
    --no-dry-run \
    --output-dir ./fixtures/generated
```

## Why This Is Not Live Trading
This module is a **data preparation tool**. It converts historical network state into static files for the paper-trading engine. It does not possess the credentials or logic to interact with the XRPL state in a mutable way.

## Limitations
- **API Availability**: Clio/RPC performance depends on the public node's rate limits and history availability.
- **Data Completeness**: Older ledgers may lack full metadata expansion depending on node configuration.
