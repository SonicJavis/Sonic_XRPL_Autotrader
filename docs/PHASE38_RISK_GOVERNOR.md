# Phase 38: Risk Governor & Operator Trust Layer

## Purpose
The Risk Governor determines if the system is currently safe enough to continue **PAPER** trading. It computes a deterministic `OperatorTrustScore` and evaluates `RiskRuleResults` based on inputs from prior phases. It explicitly answers "Should we continue paper trading?", and it never answers "Is the system ready for live trading?".

## Research Base
1. **XRPL Amendments**: Verified AMM, Clawback, MPT, and DID are enabled on mainnet. Verified `Batch` and `fixBatchInnerSigs` are currently disabled/unsupported due to known vulnerabilities patched in `rippled` 3.1.1.
2. **rippled Release Notes**: Reviewed `rippled` 3.1.2 security fixes.
3. **XLS Standards**: Verified XLS-39 (Clawback) is Final, but XLS-73 (AMMClawback) and XLS-82 (MPT DEX) are still drafts. The system does not assume draft features are live or executable.
4. **Conclusion**: Live deployment remains strictly forbidden. The trust layer is tailored specifically to paper execution and deterministic historical bounds.

## Inputs (Read-Only)
- Phase 33: `early_warnings.jsonl`, `drift_summary.json`
- Phase 34: `meme_candidates.jsonl`
- Phase 35: `paper_performance_review.json`
- Phase 36: `paper_campaign.json`, `paper_decisions.jsonl`, `paper_trade_history.jsonl`
- Phase 37: `strategy_backtest_results.jsonl`, `strategy_tournament_results.json`

## Outputs (Append-Only)
Outputs are written to `reports/phase38/<timestamp>/`:
- `operator_trust_score.json`
- `risk_rule_results.jsonl`
- `risk_governor_decision.json`
- `risk_governor_report.md`

## Trust Score Formula
The deterministic `OperatorTrustScore` ranges from 0 to 100, weighted across:
- 15% Data Quality (Metadata completeness & Validation integrity)
- 20% Strategy Quality (Tournament backtest scores)
- 15% Drift Stability (Absence of critical drift warnings)
- 20% Paper Performance (Win rates and drawdown constraints)
- 15% Metadata Completeness
- 10% Validation Integrity (Valid ledger metadata required)
- 5% Protocol Risk (Absence of `CLAWBACK_ENABLED` etc.)

Caps and Penalties:
- Trust score is capped heavily if missing metadata exceeds thresholds.
- Critical drift warnings cap the trust score.
- False high-confidence paper entries cap the trust score.

## Risk Rules
The governor runs specific rules:
- `Metadata Completeness` (Fails if missing metadata > 30%)
- `Validation Integrity` (Fails if paper entries lack validated ledger evidence)
- `Strategy Stability` (Fails if unknown outcome rate > 35%)
- `Drawdown / Losses` (Fails if excessive consecutive paper losses occur)
- `Drift Warnings` (Fails if any critical drift warnings exist)
- `Ambiguity` (Warns/reduces risk if ambiguous match rate > 5%)
- `False Confidence` (Fails if high confidence decisions lack metadata)
- `Protocol Features Risk` (Warns if clawbacks or unconfirmed drafts are assumed live)
- `Live Readiness` (**Always fails**; live trading is strictly forbidden by policy)

## Decision Outcomes
The decision applies *only* to paper trading:
1. `allow_paper`: Trust score >= 60 and no critical failures.
2. `reduce_paper_risk`: Trust score 40-59 or non-critical warnings triggered.
3. `halt_paper`: Trust score < 40 or any critical rule failure.
4. `insufficient_data`: Required phase reports are missing.

## Why Live Trading Remains Forbidden
- The system evaluates historical deterministic fixtures.
- Real fund movement requires active key management (seeds/wallets) which is physically removed and audited out via `safety_grep.py`.
- The `Live Readiness` rule is hardcoded to fail with severity `critical` to prevent auto-promotion.

## Next Phase Recommendation
Phase 39: Operator Visualization & Frontend Dashboard. The backend architecture is robustly tested and deterministic; the human operator requires a clean interface to visualize the generated reports and manage paper campaigns.
