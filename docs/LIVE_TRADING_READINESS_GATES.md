# Live Trading Readiness Gates

**LIVE TRADING IS STRICTLY FORBIDDEN UNTIL ALL GATES ARE MET.**

## Required Readiness Gates

1. **7-Day Paper Campaign Completed**
   - **PASSED**: Phase 39 introduces the campaign runner linking the whole pipeline.

2. **Paper Review Generated**
   - The Phase 35 review engine must analyze the campaign.
   - All `mistake_tags` must be documented.

3. **Strategy Backtest Completed**
   - The read-only models must undergo historical regression testing.

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
