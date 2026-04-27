# PNL Realism Audit (XRPL Paper Trading)

Date: 2026-04-27
Scope: PnL realism leaks in paper execution, attribution, slippage, lifecycle, and timing.
Mode: Audit only (no strategy or scoring changes applied in this audit).

## 1. Executive Summary

Current paper results are directionally useful for structure screening, but they are not yet reliable as realistic XRPL execution PnL.

Main conclusion:
- The system has solid reject-biased gating and some realistic entry-side depth walking.
- However, there are still major realism leaks around timing, exit pricing, mark/mid usage, lifecycle linkage, costs, and attribution joins.

Severity summary:
- BLOCKING: 4
- HIGH: 8
- MEDIUM: 8
- LOW: 4

## 2. Confirmed Realistic Components

1. BUY entry simulation does depth-walk asks and computes VWAP-like average fill.
- Evidence: app/execution/fill_simulator.py:4, app/execution/fill_simulator.py:61

2. Partial/unfilled outcomes are represented in outcome persistence.
- Evidence: app/db/models.py:99, app/db/models.py:100, app/db/models.py:102, app/db/models.py:103

3. Risk layer denies non-fillable conditions from slippage estimator.
- Evidence: app/risk/risk_manager.py:74, app/risk/risk_manager.py:77

4. One-sided/invalid books are rejected upstream.
- Evidence: app/market_data/snapshot_builder.py:104

5. Alpha and risk records preserve rejection rationale and attribution metadata.
- Evidence: app/db/models.py:128, app/db/models.py:129, app/db/models.py:140, app/db/models.py:124

## 3. PnL Realism Leaks

### BLOCKING

1. Mid-price is used as canonical market price; this leaks favorable execution assumptions.
- Why this matters: midpoint is not executable in thin XRPL books; using it for signal context and lifecycle updates inflates realism.
- Evidence: app/market_data/snapshot_builder.py:27, app/execution/pipeline.py:184

2. Same-snapshot signal and entry fill with no modeled latency/queue position.
- Why this matters: signal time and execution time are treated as effectively identical, creating lookahead-like favorable fills.
- Evidence: app/execution/pipeline.py:123, app/execution/pipeline.py:194, app/execution/pipeline.py:300

3. Exit and MAE/MFE updates are based on snapshot mid price, not executable bid/ask side.
- Why this matters: unrealized and realized exit path can be materially overstated, especially in no-bid or wide-spread regimes.
- Evidence: app/execution/pipeline.py:464, app/execution/pipeline.py:490

4. Attribution join bug: alpha breakdown maps outcomes by signal_id but matches on alpha.id.
- Why this matters: component and manipulation attribution can be wrong, making model quality conclusions invalid.
- Evidence: app/alpha/performance_engine.py:51, app/alpha/performance_engine.py:58, app/alpha/performance_engine.py:60

### HIGH

5. Legacy PaperTrade PnL path remains mark-price based and uses a generic current_price_xrp input.
- Why this matters: stop/take exits can close at non-executable prices and overstate profitability.
- Evidence: app/execution/paper.py:51, app/execution/paper.py:62, app/execution/paper.py:63

6. No SELL-side (bid-walk) execution simulator for exits.
- Why this matters: long exits assume convertibility without no-bid/no-liquidity slippage penalties.
- Evidence: app/execution/fill_simulator.py:4 (asks-only), app/execution/pipeline.py:286 (BUY-only execution path)

7. Slippage is clipped non-negative, hiding potential price improvement distribution and asymmetry diagnostics.
- Why this matters: clipped metrics distort calibration and error analysis.
- Evidence: app/alpha/engine.py:294, app/execution/fill_simulator.py:61

8. Reality-filtered rejected fills set pnl_xrp=0 without explicit mark-to-market loss opportunity accounting.
- Why this matters: can understate harm of non-execution in adverse moves.
- Evidence: app/execution/pipeline.py:341

9. Entry uses simulator VWAP, but post-entry monitor horizon closure uses latest snapshot price, not executable side.
- Why this matters: mixed execution model introduces hidden optimism/ inconsistency.
- Evidence: app/execution/pipeline.py:300, app/execution/pipeline.py:490

10. No explicit stale snapshot rejection in risk or pipeline before trade decision.
- Why this matters: trading on stale snapshots can produce artificial fills.
- Evidence: app/risk/rules.py:16 (no age fields), app/execution/pipeline.py:55 (no freshness gate)

11. No fee model (network fee/spread-crossing overhead beyond slippage) in realized PnL.
- Why this matters: paper edge can disappear net of costs.
- Evidence: app/config.py:12-58 (no fee assumptions), app/execution/paper.py:18, app/execution/pipeline.py:490

12. PnL unit mismatch risk in legacy PaperTrade formula (price delta multiplied by size_xrp not token inventory).
- Why this matters: dimensionally inaccurate PnL can look profitable/less risky.
- Evidence: app/execution/paper.py:18

### MEDIUM

13. No explicit linkage between PaperTrade and PaperTradeOutcome lifecycle.
- Why this matters: two parallel truth sources can diverge.
- Evidence: app/db/models.py:74, app/db/models.py:88 (no shared FK field)

14. Outcome model has one snapshot_id only (no exit_snapshot_id / entry depth reference).
- Why this matters: weaker replayability for precise execution reconstruction.
- Evidence: app/db/models.py:94

15. PERF_LIQUIDITY_DISAPPEAR_SECONDS exists but is not enforced in monitoring path.
- Why this matters: configured realism guard may be assumed active but is not.
- Evidence: app/config.py:52, app/execution/pipeline.py:313-322

16. Synthetic depth and spoof detection are heuristic and static; no order persistence duration.
- Why this matters: spoofed liquidity may still pass if briefly present.
- Evidence: app/alpha/engine.py:233

17. One-sided dominance is computed but not used as explicit hard stop in pipeline execution path.
- Why this matters: warning signal may not fully translate to execution constraints.
- Evidence: app/market_data/snapshot_builder.py:72

18. No explicit distinction between ledger time and local ingestion time in snapshot schema.
- Why this matters: ordering and freshness can be wrong during node lag.
- Evidence: app/db/models.py:46

19. No transaction-queue/latency penalty model between signal approval and execution.
- Why this matters: optimistic fill assumptions in fast-moving or toxic books.
- Evidence: app/execution/pipeline.py:194-364

20. No explicit no-bid rug exit scenario handling in realized exit path.
- Why this matters: practical inability to exit IOUs is a core XRPL risk.
- Evidence: app/execution/pipeline.py:490, app/execution/paper.py:63

### LOW

21. Autobridging is explicitly placeholder (not modeled).
- Why this matters: direct-only liquidity may misestimate executable prices.
- Evidence: app/market_data/snapshot_builder.py:37, app/market_data/snapshot_builder.py:82

22. XRPL issuer transfer-rate / frozen / trustline constraints are not represented in PnL path.
- Why this matters: eventual live behavior may diverge from paper.
- Evidence: no corresponding fields/guards in app/db/models.py or app/risk/risk_manager.py

23. Outcome monitors use local wall time for elapsed checks.
- Why this matters: less robust under clock skew/process pauses.
- Evidence: app/execution/pipeline.py:457, app/execution/pipeline.py:475

24. API metrics can be read without explicit realism disclaimers.
- Why this matters: operators may over-trust outputs.
- Evidence: app/api/routes_performance.py:9

## 4. XRPL-Specific Realism Risks

1. No explicit modeling of no-bid unwind for IOU exits.
2. No autobridge/path liquidity comparison against direct book.
3. No issuer transfer-rate/trustline freeze gating in execution realism.
4. No differentiation between visible offers and reliably funded/persistent executable depth.
5. Drops/IOU parsing exists, but precision/rounding impact on liquidation path is not audited end-to-end in PnL.

## 5. Lookahead / Future-Data Risks

1. Signal and fill are computed from same snapshot parse in a single pass.
- Evidence: app/execution/pipeline.py:123, app/execution/pipeline.py:194, app/execution/pipeline.py:300

2. Midpoint used as market anchor for strategy context and ongoing outcome evaluation.
- Evidence: app/market_data/snapshot_builder.py:27, app/execution/pipeline.py:184, app/execution/pipeline.py:464

3. Attribution engine uses future snapshots for reject accuracy by design; acceptable for evaluation, but must never feed execution decisions.
- Evidence: app/alpha/performance_engine.py:131-137

## 6. Missing Fields / Models for Realistic Attribution

1. Missing PaperTrade -> PaperTradeOutcome foreign key.
2. Missing entry_snapshot_id and exit_snapshot_id on outcome lifecycle (single snapshot_id is insufficient).
3. Missing entry/exit price source fields (bid/ask/vwap/mid) in outcome.
4. Missing snapshot age / ledger index / ledger close time fields in MarketSnapshot.
5. Missing execution latency fields (signal_ts, risk_ts, simulated_fill_ts).
6. Missing fee/cost fields per outcome (network fee, spread-cross cost estimate).

## 7. Misleading Dashboard / API Risks

1. Dashboard top metric uses legacy PaperTrade pnl_xrp and labels it as total paper PnL, which can be interpreted as executable-realistic PnL.
- Evidence: dashboard/streamlit_app.py:51

2. Performance metrics do not explicitly label assumptions (mid-based exits, no fees, no bid-walk exits).
- Evidence: dashboard/streamlit_app.py:116-183, app/api/routes_performance.py:9-28

3. No explicit panel separating filled, partial, rejected, and unfilled opportunity-cost views beyond simple fill_pct.
- Evidence: dashboard/streamlit_app.py:122-133

## 8. Required Fixes Before Building/Trusting Performance Attribution

Severity-tagged required sequence:

### BLOCKING

1. Replace midpoint-based lifecycle exit/MAE/MFE pricing with side-correct executable pricing.
2. Introduce explicit signal->risk->execution timestamp chain with latency budget and enforce max age.
3. Fix alpha attribution join (signal_id linkage), then re-baseline breakdown metrics.
4. Unify truth model: prevent legacy PaperTrade mark-price PnL from being displayed as execution-realistic PnL.

### HIGH

5. Add SELL-side bid-walk simulation and no-bid exit failure states.
6. Add snapshot freshness checks in risk/pipeline with explicit rejection reasons.
7. Add fee assumptions to net PnL.
8. Add PaperTradeOutcome lifecycle linkage to trade ids and entry/exit snapshot ids.

### MEDIUM

9. Enforce PERF_LIQUIDITY_DISAPPEAR_SECONDS or remove from config until implemented.
10. Record price source tags and slippage calc source tags for auditability.
11. Add explicit issuer/trustline realism flags for attribution-risk diagnostics.
12. Add strict operator-facing disclaimers in API/dashboard responses.

## 9. Recommended Test Additions

Current tests cover partial fills, zero-liquidity fill, slippage mismatch metric, and MAE/MFE progression.

Missing tests (recommended):

1. Midpoint fantasy fill prevention (entry/exit never at mid when spread > 0).
2. SELL exit must walk bids and fail under no-bid conditions.
3. Stale snapshot rejection path with reason code persisted.
4. Signal->fill latency penalty test (execution after delay worsens fills).
5. Fee subtraction test on net pnl.
6. PaperTrade and PaperTradeOutcome consistency test.
7. Attribution join integrity test (alpha.signal_id relation correctness).
8. Lookahead guard test ensuring fill uses only permissible post-signal data model.
9. Snapshot ledger-time ordering test vs local ingestion time.
10. Rug-exit scenario test (liquidity disappears before planned exit).

## 10. Pytest Result

Command:
- python -m pytest

Result:
- 55 passed in 5.89s
