# Phase 37: Strategy Performance Engine & Backtest Tournament

## Purpose
To evaluate historical paper trades and discovery candidates against deterministic paper-only strategies, answering "Which strategies performed best under what evidence conditions?" without promoting any strategy to live execution.

## Research Base
1. **XRPL Finality & Features**: Verified rippled 3.1.2 is the latest patch. Evaluated protocol features such as AMM, MPT, DID, and Clawback/Permissioned Domains.
2. **FirstLedger/Clio APIs**: A generic robust public websocket for querying all historical state without a private node is still not universally reliable, reinforcing the need for our fixture-based offline engine.

## Inputs
- Phase 34: `meme_candidates.jsonl`
- Phase 36: `paper_decisions.jsonl`, `paper_trade_history.jsonl`
- Price Fixtures

## Outputs
Append-only records in `reports/phase37/<timestamp>/`:
- `strategy_evaluations.jsonl`
- `strategy_backtest_results.jsonl`
- `strategy_tournament_results.json`
- `strategy_performance_report.md`

## Defined Strategies
- `trustline_spike_watch`
- `amm_seeded_launch_watch`
- `metadata_backed_high_attention`
- `avoid_offer_only_noise`
- `early_but_validated_watch`
- `liquidity_first_watch`
- `conservative_metadata_only`
- `aggressive_high_attention_paper_only`
- `clawback_risk_avoidance`
- `mpt_feature_watch`

## Tournament Scoring
The tournament ranks strategies deterministically:
`Score = (WinRate * 2.0) + (AvgWin * 100.0) + (AvgLoss * 50.0) + (MetaSuccess * 0.5) + (AMMSuccess * 0.5) + (TrustlineSuccess * 0.2) - (UnknownRate * 1.5) - (OfferFailRate * 0.5) - (MissingHighConfidencePenalty)`

## XRPL Truth Model
- AMMCreate is strong liquidity evidence.
- OfferCreate alone is weak (noise).
- Validated ledger metadata is the highest truth.
- Same ticker, different issuer are strictly separate.

## Absolute Constraints
- The tournament winner **does not** authorize live trading.
- Manual human review is required.
- The engine operates purely read-only on fixtures.

## Next Phase Recommendation
Phase 38 should focus on Risk Governance and live sandbox bounds.
