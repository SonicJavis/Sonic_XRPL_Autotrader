# Phase 46: Provider Fixtures

## Overview

Phase 46 introduces a structured, file-based fixture system for offline XRPL data. This enables deterministic, network-free testing across all provider interfaces.

## Architecture

### New Modules

| Module | Purpose |
|--------|---------|
| `providers/errors.py` | Fixture-specific error hierarchy |
| `providers/fixture_models.py` | Typed dataclasses for fixture data |
| `providers/fixture_manifest.py` | `FixtureManifest` with deterministic checksums |
| `providers/fixture_store.py` | `FixtureStore` — structured directory loader |
| `providers/fixture_ledger.py` | `FixtureLedgerProvider` — replaces mock fallback |
| `providers/fixture_market_data.py` | `FixtureMarketDataProvider` — market snapshots |
| `providers/metadata_parser.py` | Offline transaction metadata parsing |
| `providers/balance_changes.py` | Balance change extraction from metadata |
| `providers/normalizers.py` | Asset/identifier normalization |
| `providers/safety_scan_fixtures.py` | Secret pattern scan for fixture files |

### Error Hierarchy

```
ProviderError (core)
├── ProviderUnavailableError
├── DataQualityError
├── FixtureMissingError   — fixture file/directory not found
├── FixtureCorruptError   — fixture file cannot be parsed
└── StaleFixtureError     — fixture data outside expected ledger range
```

### Fixture Directory Structure

```
tests/fixtures/xrpl/
├── manifest.json           # FixtureManifest with checksums
├── server_info.json        # Server info snapshot
├── ledgers/                # ledger_{index}.json
├── accounts/               # {account}.json
├── account_lines/          # {account}_lines.json
├── account_tx/             # {account}_tx.jsonl (newline-delimited JSON)
├── transactions/           # tx_*.json
├── orderbooks/             # {assetA}_{assetB}.json
├── amm/                    # {assetA}_{assetB}.json
├── mpt/                    # holders_sample.json or holders_{id}.json
└── metadata/               # metadata JSON for parser tests
```

## FixtureLedgerProvider

The `FixtureLedgerProvider` **does not fall back to mock data**. It raises `FixtureMissingError` when a requested fixture is not found. This prevents silent test pollution with mock data.

## FixtureManifest

Each fixture directory must have a `manifest.json` describing the fixture set:

```json
{
  "name": "synthetic_test_fixture",
  "version": "1.0.0",
  "network": "synthetic",
  "created_at": "2025-01-01T00:00:00Z",
  "source_summary": "...",
  "source_urls": [],
  "ledger_min": 1000,
  "ledger_max": 1001,
  "account_count": 2,
  "transaction_count": 2,
  "amm_count": 1,
  "orderbook_count": 1,
  "mpt_snapshot_count": 1,
  "limitations": ["synthetic data only, not real XRPL data"]
}
```

A deterministic `fixture_id` is computed from `name|version|network` via SHA256.

## Metadata Parser

`metadata_parser.py` provides structured parsing of XRPL transaction metadata:

- `parse_metadata(metadata)` → `MetadataParseResult`
- `extract_affected_nodes(metadata)` → `list[AffectedNode]`
- `get_delivered_amount(metadata, tx)` → delivered amount
- `is_sufficient_truth(metadata)` → `False` if `tesSUCCESS` with no `AffectedNodes`

**Key limitation**: `tesSUCCESS` with no `AffectedNodes` is NOT sufficient truth for PnL attribution. The parser flags this in `limitations`.

## Balance Change Extraction

`balance_changes.py` extracts balance changes from metadata `AffectedNodes`:

- `AccountRoot` nodes → XRP balance changes (drops)
- `RippleState` nodes → IOU balance changes

## Asset Normalization

`normalizers.py` provides validated normalization:

- `normalize_asset_key("USD", "rIssuer")` → `NormalizedAssetKey(currency="USD", issuer="rIssuer")`
- `parse_asset_key("XRP")` → `NormalizedAssetKey(currency="XRP", issuer=None)`
- `normalize_tx_hash(h)` → uppercase 64-char hex
- `normalize_ledger_index(idx)` → non-negative int

## Safety

- Fixture files are scanned for `seed`, `private_key`, `mnemonic` patterns
- `tesSUCCESS` does **not** trigger false positives (deliberately excluded from scan patterns)
- `FixtureStore.validate_health()` runs secret scan on all JSON/JSONL files

## CLI Commands (Phase 46)

```bash
sonic_xrpl fixtures --path tests/fixtures/xrpl
sonic_xrpl fixture-health --path tests/fixtures/xrpl
sonic_xrpl fixture-account --path tests/fixtures/xrpl --account rTrader
sonic_xrpl fixture-amm --path tests/fixtures/xrpl --asset-a XRP --asset-b USD_rIssuer
sonic_xrpl fixture-balance-changes --metadata tests/fixtures/xrpl/metadata/payment_partial_metadata.json
```

## Safety Notes

- No secrets in fixture files
- No live network calls
- No transaction submission
- Fixture provider raises errors rather than silently returning mock data

## Limitations

- Fixture data is point-in-time; price/liquidity series are not available
- `is_sufficient_truth` requires `AffectedNodes` — incomplete metadata cannot be used for PnL attribution
- MPT holder fixtures contain synthetic data only
