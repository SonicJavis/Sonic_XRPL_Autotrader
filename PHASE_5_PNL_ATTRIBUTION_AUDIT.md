# Phase 5 PnL Attribution Audit

Date: 2026-04-27
Repository: Sonic_XRPL_Autotrader
Scope: Strict XRPL PnL attribution engine audit only (no feature changes)

## Executive Summary

The attribution layer has a strong foundation for fill-based accounting and traceability, but it is not yet fully strict under all failure and lifecycle paths.

Confirmed strengths:
- Realized PnL is computed from persisted exit fills (not requested size).
- Exit simulation in attribution engine is bid-side depth-walked.
- No-bid exits are explicitly treated as failures.
- Failure events are queryable via API.

Critical gaps remain:
- Exit lifecycle can freeze after first failed exit (no retry path).
- Position exits are auto-attempted every snapshot without explicit exit intent/risk decision.
- Midpoint is still used for slippage metric generation in simulator.
- Dual lifecycle systems (PaperTradeOutcome and Position) can diverge.

Overall: strong progress, but additional hardening is required before edge validation is trusted.

## 1. Confirmed Correct Logic

1. Position model core fields exist and support partial exits.
- Position includes entry/exit VWAPs, entry/exit filled sizes, remaining size, snapshot linkage, status.
- Position opens only from create_position_from_entry when entry filled size > 0.

2. ExecutionRecord captures requested vs filled and timing metadata.
- Includes requested_size, filled_size, fill_status, avg_fill_price, fill_levels_json, snapshot/signal/execution times, latency and snapshot age.

3. PositionExitFill model supports realized PnL per exit fill.
- Uses fill_size and per-fill pnl_xrp, enabling multi-exit aggregation.

4. Realized PnL uses filled exits only.
- realized_pnl_summary sums PositionExitFill.pnl_xrp values only.
- Failed exits do not generate PositionExitFill rows.

5. Unrealized PnL is separated from realized.
- unrealized_pnl_summary returns independent unrealized output.
- If non-fillable (e.g., no bids), unrealized_pnl is None.

6. Partial entry and partial exit are represented.
- Entry size is based on execution_result.filled_size.
- Position.remaining_size updates as partial exits occur.

7. No-bid exit is treated as failure, not synthetic 0 PnL fill.
- simulate_exit_sell returns UNFILLED + failure_reason NO_BIDS.
- Position set to FAILED_EXIT on unfilled exit attempt.

8. Signal/risk/execution/position traceability is present at schema level.
- Position links signal_id, risk_decision_id, execution_id.
- ExecutionRecord links token_id, signal_id, risk_decision_id, snapshot_id, position_id.

9. APIs expose core attribution and failure surfaces.
- /positions, /positions/{id}, /pnl/realized, /pnl/unrealized, /failures, /execution/{id}.

## 2. PnL Realism Risks

### BLOCKING

1. Position lifecycle can get stuck after a single failed exit.
- update_positions_for_snapshot only processes OPEN/PARTIAL_EXIT.
- On first failed exit, position status becomes FAILED_EXIT and is no longer retried.
- This can permanently freeze an otherwise recoverable position and distort long-horizon attribution.

2. Exit execution is triggered automatically on every new snapshot without explicit exit signal/risk intent.
- This creates forced liquidation behavior unrelated to strategy/risk decisions.
- Can bias realized PnL path and attribution interpretation.

### HIGH

3. Midpoint is still used to compute slippage metrics in simulator.
- Slippage metric uses mid=(best_bid+best_ask)/2 for both entry and exit.
- Even if PnL itself is fill-based, this slippage metric can mislead quality analysis.

4. Dual accounting tracks can diverge (PaperTradeOutcome vs Position/ExecutionRecord).
- Pipeline updates PaperTradeOutcome lifecycle and independently updates Position lifecycle.
- Divergence risk in closures/failure reasons/PnL semantics.

5. Time-order invariant is not explicitly validated/persisted as a hard check.
- execution_time >= signal_time >= snapshot_time is generally implied, not asserted.
- Missing explicit guard can allow edge-case violations under clock/serialization anomalies.

### MEDIUM

6. Requested-size leak risk in external consumers.
- Data model correctly separates requested and filled.
- But API returns both raw fields without opinionated derived fields, so downstream misuse remains possible.

7. Realized PnL relies on persisted pnl_xrp in PositionExitFill.
- If upstream write bug occurs, summary trusts stored value instead of recomputing from fill_size and VWAPs.

8. Position.close semantics are size-based only.
- No explicit invariant checks for overfill, cumulative fill consistency, or monotonic remaining_size.

9. ExecutionRecord fill_levels_json is serialized text in API responses.
- Not normalized to structured JSON response schema; interpretation errors possible by clients.

## 3. XRPL-Specific Risks

1. Autobridging remains unmodeled.
- Current execution model uses direct book only.
- Conservative but may under/over represent executable paths in some pairs.

2. Trustline/issuer constraints are not enforced in attribution logic.
- Freeze/authorization/issuer transfer effects are not represented in position exit feasibility.

3. Liquidity haircut is global and static.
- Does not adapt to issuer/book conditions or ledger volatility regimes.

4. Offer fundedness and disappearance between ledgers are approximated, not fully modeled.
- Fill levels are persisted for reproducibility, but microstructure transitions are still simplified.

## 4. Lookahead / Future-Data Risks

1. Snapshot-to-exit coupling can create interpretation ambiguity.
- Exits are attempted immediately on each latest snapshot event.
- Without explicit exit trigger model, future intent attribution can be blurred.

2. Stale-data rejection is implemented in simulator, but not all call paths assert temporal ordering in one place.
- Practical risk is moderate, but formal anti-lookahead contract is not centrally enforced.

3. Performance analytics path still includes legacy-style records.
- Existing summary/breakdown routes can mix semantics from PaperTradeOutcome with strict position ledger interpretation.

## 5. Attribution Gaps

1. Position does not store explicit list of all execution_ids (entry + exits), only a single execution_id field.
2. Position detail endpoint does not return stitched execution/fill timeline in one response.
3. RiskDecision linkage on exits is reused from entry context; no dedicated exit risk decision record.
4. Multiple lifecycle stores (Position, ExecutionRecord, PositionExitFill, PaperTradeOutcome, PaperTrade) increase reconciliation burden.

## 6. Dashboard/API Misleading Risks

1. Dashboard still shows "Paper Performance Attribution" metrics from legacy performance engine while strict position metrics are also shown.
- Mixed metric families can confuse operators.

2. Dashboard still displays legacy PaperTrade and PaperTradeOutcome tables alongside strict Position/Execution records.
- Without strong labeling, this can be interpreted as one coherent metric stream.

3. API /execution/{id} returns fill_levels_json as string; clients may not parse and may miss exact fill path details.

4. /pnl/unrealized returns aggregate None if any position is non-fillable.
- Conservative behavior is valid, but clients may misread as system failure rather than explicit risk state.

## 7. Required Fixes Before Edge Validation

### BLOCKING

1. Add a recoverable exit state policy.
- FAILED_EXIT should be retryable under explicit conditions, or separated into transient/permanent failures.

2. Decouple automatic exit attempts from snapshot ingestion.
- Require explicit exit intent/risk approval before converting unrealized to realized fills.

3. Remove midpoint dependency from reported slippage quality metrics.
- Keep depth-walk-based executable references only.

### HIGH

4. Consolidate lifecycle truth source.
- Define strict canonical ledger (Position + ExecutionRecord + PositionExitFill) and demote/retire conflicting fields.

5. Add invariant checks on write path.
- Assert monotonic remaining_size, no overfill, and strict timestamp ordering.

6. Provide stitched position timeline endpoint.
- One response showing signal, risk decision, entry execution, all exit executions/fills.

### MEDIUM

7. Normalize API output of fill levels as structured JSON objects, not opaque strings.
8. Add explicit schema docs/labels separating strict realized vs legacy analytics metrics.

## 8. Test Coverage Review and Missing Edge Cases

Covered well:
- Partial entry sizing
- Partial exit realized PnL
- No-bid exit failure
- Filled-size-based PnL
- Multi-exit aggregation
- Unrealized bid-side behavior
- Zero-liquidity unrealized behavior

Missing/high-value tests:
1. Timestamp order invariant test (execution_time >= signal_time >= snapshot_time) across entry and exit writes.
2. Retry behavior test for FAILED_EXIT transition policy (currently absent/implicit freeze).
3. Reconciliation test between strict ledger and legacy tables to detect divergence.
4. Overfill protection test (sum exit fills never exceeds entry filled size).
5. API contract test that /positions/{id} exposes full traceability payload needed for audit replay.

## 9. Direct Answers to Requested Checks

- Does PnL use filled_size only?
Yes for strict realized/unrealized paths (PositionExitFill and simulated exits).

- Can requested_size leak into PnL?
Not in current strict formulas, but downstream misuse risk remains via raw API fields.

- Are exits always bid-side depth-walked?
Yes in strict attribution engine exits.

- Are failed exits excluded from realized PnL?
Yes; failed exits do not create PositionExitFill rows.

- Is unrealized PnL clearly separate from realized?
Yes in API and dashboard top metrics, though legacy panels remain visible.

- Are multiple partial exits aggregated correctly?
Yes by PositionExitFill summation and tested.

- Is no-bid exit handled as failure, not 0 PnL?
Yes in strict engine.

- Are snapshot_time, signal_time, execution_time correctly ordered?
Generally yes in flow, but hard invariant assertions are missing.

- Can future data or stale snapshots affect PnL?
Stale rejection exists; future-data risk is moderate due automatic exit-on-snapshot behavior and mixed lifecycle semantics.

- Are failures queryable and visible?
Yes via /failures and dashboard failure metrics.

## 10. Pytest Result

Command:
- python -m pytest

Result:
- 72 passed in 10.30s
