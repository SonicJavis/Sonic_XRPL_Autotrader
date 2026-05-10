# Live Trading Readiness Gates

**LIVE TRADING IS STRICTLY FORBIDDEN UNTIL ALL GATES ARE MET.**

## Legacy Surface Status (PR 3)

- `app/` is the current runnable legacy API/paper runtime.
- `execution_prototype/` is historical/reference-only unless used by named
  tests or bridge adapters.
- Xaman/manual submission workflow references under `execution_prototype/` are
  historical/manual prototype flows only, not V2 runtime authorization.
- No new features may be added to `app/` or `execution_prototype/` until the
  canonical-path decision is resolved and required safety conformance tests pass.

## Required Readiness Gates

1. **7-Day Paper Campaign Completed**
   - **PASSED**: Phase 39 introduces the campaign runner linking the whole pipeline.
   - **ENHANCED**: Phase 40 adds historical price/liquidity truth for accurate MtM valuation.
   - **ROBUST**: Phase 41 provides standardized, read-only collection of this historical truth.

2. **Paper Review Generated**
   - The Phase 35 review engine must analyze the campaign.
   - All `mistake_tags` must be documented.

3. **Strategy Backtest Completed**
   - The read-only models must undergo historical regression testing on versioned Phase 42 datasets.

4. **Risk Governor Implemented**
   - **PASSED**: Phase 38 implements deterministic risk limits.

5. **Operator Trust Score Implemented**
   - **PASSED**: Phase 38 enforces Trust Score calculation, strictly blocking live actions.

6. **Manual Approval Granted**
   - A human-in-the-loop MUST sign off on the first sandbox test.

7. **Isolated Tiny-Limit Sandbox Designed**
   - Maximum risk bounds of 10 XRP max total liability must be enforced at the hardware/network layer.

8. **CI Safety Gates Updated**
   - `safety_grep.py` must be upgraded to support a "controlled execution mode" isolated from the standard logic flow.

9. **Phase 43 Dataset Strategy Tournament Completed**
   - At least one strategy must be promoted to `promote_to_more_paper_tests` status.
   - Zero critical overfitting warnings allowed for promotion.
   - Dataset quality score >= 60/100 required.
   - Live trading readiness remains at 0/100 regardless of tournament outcome.

10. **Phase 44 Walk-Forward Stability Assessment**
   - Phase 44 adds walk-forward stability tracking. It adds **zero live readiness**.
   - All lifecycle recommendations remain paper-only.
   - live_trading_readiness remains 0/100 regardless of stability scores.
