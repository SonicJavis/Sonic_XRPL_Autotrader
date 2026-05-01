# Phase 40: Historical Market Fixture Engine + Paper Mark-to-Market Enrichment

## Purpose
Phase 40 introduces an offline historical market fixture layer. It allows paper trading campaigns to calculate accurate mark-to-market (MtM) valuations using deterministic price and liquidity snapshots. This reduces the number of "unknown" outcomes in paper reports by providing historical "truth" for PnL calculation without requiring live network access.

## Research Sources Checked
- **XRPL Known Amendments**: AMM, AMMClawback, Clawback, MPT, DID, and Permissioned DEX are enabled.
- **rippled Release Notes**: Batch and fixBatchInnerSigs are unsupported/disabled in 3.1.2.
- **xrpl-py**: Verified utility `xrpl.utils.get_balance_changes(metadata)` exists.
- **FirstLedger API**: Supports historical trades and price history for tokens.

## Fixture Formats
The engine supports JSONL files in `fixtures/market/`:
- `prices.jsonl`: Price snapshots (XRP and USD).
- `liquidity.jsonl`: Liquidity snapshots (AMM and Orderbook depth).

## Asset Key Rules
Assets are uniquely identified via a deterministic SHA256 hash of:
- `issuer:CURRENCY` (for Issued Currencies)
- `None:XRP` (for XRP)

This ensures that the same ticker across different issuers (e.g., USD from two different gateways) is never collapsed.

## Mark-to-Market Rules
1. **Entry**: Uses the entry price from the paper position record.
2. **Current Value**: Finds the latest available snapshot in the fixture timeline for that asset.
3. **PnL**: Calculates unrealized PnL and percentage change.
4. **Outcome**: Classifies as `win`, `loss`, or `breakeven` based on MtM price vs entry price.
5. **Unknown**: If no price snapshots exist for the asset, the outcome remains `unknown`.

## How to Run CLI
```bash
python -m execution_prototype.market_fixtures.cli \
    --market-fixtures ./fixtures/market \
    --phase36-report ./reports/phase36/latest \
    --output-dir ./reports/phase40
```

## Why Live Trading Is Still Forbidden
This phase remains strictly offline. It enriches existing paper trade logs with historical market data. No live execution pathways, wallets, or transaction submission logic exists.

## Limitations
- **Fixture Quality**: MtM accuracy depends on the frequency and precision of the provided snapshots.
- **Liquidity Estimates**: Liquidity exit feasibility is estimated based on fixture capacity; it is not a guarantee of execution.
