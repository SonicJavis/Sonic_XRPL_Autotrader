# Phase 42: Historical Backtest Dataset Builder

## Purpose
Phase 42 implements a deterministic, versioned, and reusable historical dataset builder. This tool packages discovery records, market fixtures, and adapter exports into standardized datasets suitable for repeatable strategy backtesting across many time windows without risk of future leakage.

## Research Sources Checked
- **XRPL Known Amendments**: Verified status of `AMMClawback`, `Credentials`, `MPTokensV1` (Enabled). `Batch` and `fixBatchInnerSigs` are Obsolete.
- **Rippled 3.1.2**: Security/continuity release, no new features affecting dataset reconstruction.
- **Batch Vulnerability Disclosure**: Confirmed critical inner-transaction signature validation flaw in the obsolete Batch amendment.
- **xrpl.js getBalanceChanges**: Metadata parsing patterns for deterministic balance reconstruction.

## Key Features
- **Deterministic IDs**: All IDs (Dataset, Window, Quality Report) are generated using SHA256 of sorted inputs.
- **No-Future-Leak Checks**: Strict verification that decision events do not reference snapshots from future ledger indices.
- **Chronological Splitting**: 60/20/20 train/validation/test split by default, preserving ledger order without shuffling.
- **Quality Scoring**: Automated scoring based on data coverage, asset identity clarity, and protocol safety.
- **Append-Only Output**: Datasets are written to versioned, timestamped folders to prevent mutation of history.

## Supported Inputs
1. **Phase 34 Discovery Reports**: `meme_candidates.jsonl`, `discovery_scores.jsonl`.
2. **Phase 40 Market Fixtures**: `normalized_price_snapshots.jsonl`, `normalized_liquidity_snapshots.jsonl`.
3. **Phase 41 Adapter Exports**: `raw_source_records.jsonl`, `prices.jsonl`, `liquidity.jsonl`.

## Dataset Manifest Format
The `dataset_manifest.json` includes:
- `dataset_id`: Unique deterministic hash.
- `asset_count`: Number of unique tickers/issuers.
- `time_range_summary` & `ledger_range_summary`.
- `dataset_hash`: Stability verify for the entire dataset contents.

## Quality Scoring Rules
- **Base Score**: 100
- **Ambiguous Asset Identity**: Caps score at 50.
- **Future Leakage**: Caps score at 30.
- **Unsupported Batch Context**: Caps score at 60.
- **Xahau/Hook Context**: Caps score at 60.
- **Missing Data**: Progressive penalties based on record counts.

## Usage
```bash
python -m execution_prototype.backtest_datasets.cli \
  --dataset-name "xrpl-meme-v1" \
  --discovery-report ./reports/phase34/latest \
  --market-fixtures ./reports/phase40/latest \
  --output-dir ./datasets/backtests
```

## Safety Gate: Why Live Trading Is Still Forbidden
Phase 42 is **READ-ONLY**. It does not contain:
- Wallet handling or seed management.
- Transaction signing or submission logic.
- Live RPC mutation capabilities.
- Real-time fund movement primitives.

It is strictly for offline replay and evaluation of paper strategy performance.

## Limitations
- Performance is bound by JSONL parsing speed for very large datasets.
- Does not currently support complex multi-hop pathfinding reconstruction (Relies on adapter output).

## Next Phase Recommendation
**Phase 43: Integrated Backtest Replay Engine** to consume these versioned datasets for high-fidelity strategy tournaments.
