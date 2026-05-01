# Phase 39: Operator Trust Dashboard + 7-Day Paper Campaign Runner

## Purpose
Phase 39 introduces a visible, deterministic Operator Trust Dashboard and Campaign Runner to facilitate the full 7-day paper execution test. It connects Phase 34 (Discovery), Phase 36 (Paper Operator), Phase 35 (Paper Review), Phase 37 (Strategy Performance), and Phase 38 (Risk Governor) into a single reproducible pipeline that aggregates metrics into an append-only state store and a human-readable dashboard.

## Research Sources Checked & Protocol Truth
Before implementation, the following XRPL facts were verified to ensure no draft/unconfirmed features were assumed live:
1. **XRPL Amendments**: AMM, AMMClawback, Clawback, MPT, and DID are enabled on Mainnet.
2. **rippled Release Notes**: Version 3.1.2 patches security flaws; server updates are required for operators.
3. **XLS Standards**: XLS-81 (Permissioned DEX) is final but requires amendment status verification.
4. **Batch Transactions**: `Batch` and `fixBatchInnerSigs` are disabled/unsupported due to known vulnerabilities.

## How It Works
The `execution_prototype/campaign_runner/cli.py` handles the execution of a cycle. It does **not** run a hidden daemon. Instead, a human operator or external cron executes it (e.g., once daily) to advance the paper state.

```bash
# Example execution
python -m execution_prototype.campaign_runner.cli \
    --campaign-name "7-day-paper-test-001" \
    --discovery-report data/discovery_mock \
    --output-dir reports/campaigns \
    --duration-days 7 \
    --run-cycle
```

1. It creates or loads the `CampaignRunState`.
2. Runs Phase 36 Paper Pipeline.
3. Runs Phase 37 Strategy Backtest Tournament.
4. Runs Phase 38 Risk Governor.
5. Emits `campaign_dashboard_data.json`.
6. Generates `campaign_report.md`.

## The Dashboard
The `dashboard/pages/phase39_campaign_dashboard.py` Streamlit page provides an operator-friendly visualization. It strictly reads from `campaign_dashboard_data.json` without direct access to XRPL nodes, wallets, or Xaman payloads.

It visualizes:
- **Campaign Overview** (Trust Score, Governor Decision, Status)
- **Paper Performance** (Simulated Balance, PnL)
- **Risk Summary** (Triggered warnings and critical rule failures)
- **Strategy Leaderboard** (Top deterministic strategy)
- **Trade Journal** (Recent paper actions)
- **Protocol Context Observed**

## Why Live Trading Is Still Forbidden
The Operator Dashboard contains strict architectural and visual boundaries preventing live functionality:
- A permanent red banner states: `PAPER ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. NO XAMAN PAYLOAD CREATION. LIVE TRADING FORBIDDEN.`
- The `campaign_runner` relies on the deterministic Risk Governor which hardcodes the `RULE_LIVE_1` failure.
- There are no forms or UI buttons for wallet seeds or payload creation.

## Limitations
- **Missing price data**: If the historical fixtures lack oracle prices or DEX rates, the paper PnL cannot be calculated, leaving unknown outcomes.
- **Fixture dependence**: The campaign runner merely links existing sub-modules which run off local JSON files.

## Next Phase Recommendation
The current system successfully runs a deterministic 7-day paper test in a sandbox. The next step would be verifying CI/CD deployment logic using the offline tools or integrating live *read-only* ingestions into a real-time (but still paper-only) state watcher.
