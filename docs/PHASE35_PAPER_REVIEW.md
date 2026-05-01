# Phase 35: Paper Trading History + Master-Class Review Layer

## Purpose
The Paper Review Layer is a deterministic, append-only journal for simulated trading. It captures the exact conditions of entry and exit, assigns outcome classifications strictly based on pricing data, and generates a Master-Class style review.

This system answers the question: "What did we do well, what did we do badly, and what should a human review next?" It is designed to expose poor logic, weak metadata dependencies, and reckless risk assumptions without automating the underlying strategy.

## Outcome Classification Rules
- **Win**: Positive PnL percentage.
- **Loss**: Negative PnL percentage.
- **Breakeven**: 0% PnL.
- **Unknown**: Any missing price data forces an unknown state. Fake PnL is strictly prohibited.

## Mistake & Success Tags
Decisions are mapped into deterministic tags like `WEAK_METADATA_ENTRY` or `AMM_BACKED_ENTRY`.
Repeated mistakes across a campaign trigger explicit recommendations for human engineers.

## Review Logic & Prohibited Auto-Actions
The Master-Class Review engine provides explicit `prohibited_auto_action` guardrails on every trade and summary. 
The agent is allowed to *learn by reporting*. It is explicitly forbidden to *learn by changing itself*.
- It cannot adjust risk weights.
- It cannot widen slippage dynamically based on a string of losses.
- It cannot promote a paper campaign to live trading automatically.

## Integration
This runs periodically or after a campaign concludes, ingesting paper trade results into `reports/paper_review/<timestamp>/`. Outputs include `jsonl` logs for programmatic ingestion and an MD report for human review.
