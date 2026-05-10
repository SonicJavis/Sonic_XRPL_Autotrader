# Live Trading Readiness Gates

**LIVE TRADING IS STRICTLY FORBIDDEN UNTIL ALL GATES ARE MET.**

## Sniper-Style Execution Gate

Sniper/live execution planning is blocked until
`docs/SNIPER_READINESS_GATES.md` is fully marked ready (`[x]` for all
checklist items).

## Legacy Surface Status (PR 3)

- `app/` is the current runnable legacy API/paper runtime.
- `execution_prototype/` is historical/reference-only unless used by named
  tests or bridge adapters.
- Xaman/manual submission workflow references under `execution_prototype/` are
  historical/manual prototype flows only, not V2 runtime authorization.
- No new features may be added to `app/` or `execution_prototype/` until the
  canonical-path decision is resolved and required safety conformance tests pass.

## Sniper/Live Pre-Requisites (Phase 2)

- [ ] Hot wallet architecture + spending limits.
- [ ] Deterministic replay harness for sniper decisions.
- [ ] Transaction lifecycle for sequence, `LastLedgerSequence`, result-codes, retry.
- [ ] Reconciliation from intent to ledger metadata.

## Sniper/Live Safety Gates (Phase 2)

- [ ] Max position size per token enforced.
- [ ] Max daily and total loss limits enforced.
- [ ] Emergency stop persistent across restarts.
- [ ] Slippage/liquidity validation before submit.

## Sniper/Live Test Requirements (Phase 2)

- [ ] 100% coverage of signing/submission paths.
- [ ] Partial fill simulation coverage.
- [ ] Stale quote rejection coverage.
- [ ] Sequence collision handling coverage.

## BLOCKED UNTIL (Phase 2)

- [ ] `docs/SNIPER_READINESS_GATES.md` checklist is fully `[x]`.
- [ ] Safety conformance tests (`test_execution_guard`, `test_live_guard`,
      `test_safety_scan`) all pass.
- [ ] `safety_grep.py`, audit validator, and V2 safety scan all pass.

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
