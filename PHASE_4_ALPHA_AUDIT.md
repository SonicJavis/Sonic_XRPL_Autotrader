# PHASE 4 ALPHA SIGNAL ENGINE — AUDIT REPORT

**Date:** 2026-04-27
**Branch:** `main`
**Commit at audit time:** `44d3b56 feat: add phase 4 alpha signal engine`
**Pytest result:** `41 passed in 6.00s` (Python 3.14.3)

---

## 1. CONFIRMED CORRECT LOGIC

### AlphaEngine scoring math
- Weighted composite score uses 6 components: spread quality (20%), depth (20%), imbalance (10%), stability (20%), fill feasibility (20%), slippage penalty (10%). Weights sum to 100%. Clamped to [0.0, 1.0].
- All arithmetic involves guarded divisions (`max(…, 1e-6)` on denominators), preventing ZeroDivisionError for spread/slippage/liquidity-relative terms.
- Spread quality is 0.0 when spread is `None`, so a missing spread never contributes positively.

### Depth metrics
- Top-N levels are capped by `ALPHA_DEPTH_LEVELS`. Imbalance = `(bid_liq - ask_liq) / total_liq`, correctly bounded [-1, +1]. Returns `0.0` when total liquidity is zero (no divide-by-zero).
- WAP calculation is guarded: divides only when `bid_tokens > 0` / `ask_tokens > 0`.

### Stability metrics
- Requires full `ALPHA_STABILITY_WINDOW` history before any approval; returns `stable_enough=False` when fewer records exist. This is conservative.
- CV (coefficient of variation) used for spread/liquidity/mid-price series — captures relative variability correctly.
- Imbalance flip rate correctly counts sign changes divided by `max(1, N-1)`.

### Fill simulation
- Correctly walks the ask ladder consuming up to `ALPHA_DEPTH_LEVELS` levels.
- Fill ratio is continuous (partial fills yield fractional probability).
- `fill_possible` is only `True` when `remaining <= 0` (full fill achieved).
- Slippage computed as VWAP vs. best ask percentage.

### Manipulation flags
- 5 flags: `liquidity_concentrated`, `book_collapses_fast`, `imbalance_flips_fast`, `synthetic_depth`, `suspicious_issuer`.
- Any single flag being `True` causes rejection — appropriately conservative.

### Pipeline integration
- Invalid snapshot → audited, logged, `continue` (no further evaluation). Confirmed.
- Alpha evaluation runs before strategy signal generation.
- Alpha REJECT forces all candidates to `HOLD` with `suggested_size_xrp=0.0`.
- Alpha REJECT is immediately persisted as a `RiskEvent(ALPHA_REJECT)` before candidates loop.
- Paper execution only reached when `candidate.side.upper() == "BUY"` and `risk_eval.decision == APPROVE`.
- `LIVE_TRADING_ENABLED` is hardcoded `False` by default. `live_trading_requested=False` is hardcoded in `RiskContext` construction. No live/transaction-submission path was added.

### AlphaSignal persistence
- Persists: `pair`, `score`, `decision`, `reasons_json`, `spread_pct`, `depth_xrp`, `imbalance`, `slippage_pct`, `fill_probability`, `stability_score`, `token_id`, `snapshot_id`, `created_at`.
- Stored for every token processed, regardless of decision.

### RiskDecisionRecord persistence
- Persists per signal candidate, regardless of approve or deny.
- Stores alpha `score` and `reasons_json` alongside the risk `decision` and `reason`.
- Cross-references `token_id` and `snapshot_id`.

### API outputs
- `/signals/alpha` — returns all `AlphaSignal` rows, latest first, limit 100.
- `/risk/decisions` — returns all `RiskDecisionRecord` rows.
- `/market/depth` — depth levels for the most recent snapshot, grouped by side.
- `/market/history` — snapshots, optionally filtered by `token_id`, limit capped at 200.

### Safety
- XRPL client is `XRPLReadOnlyClient` — no submission paths exist in the codebase.
- Kill switch engages before risk evaluation; alpha REJECT engages before kill switch.
- No new `LIVE_TRADING_ENABLED=True` pathways introduced.

---

## 2. WEAKNESSES

### W1 — Global cooldown, not per-token
The `rejection_timestamps` list in `pipeline.run_once` is scoped to the **single call invocation**, not persisted, and shared across all tokens in that loop iteration. If 3 or more tokens are processed and each is rejected, token 4 would be blocked by the cooldown even though its rejections all came from different tokens.

**Risk:** If you have sparse watchlists, this is low impact. With ≥3 tokens, a cascade of rejections can silence later tokens in the same run. It is not persisted across calls, so it resets between pipeline runs.

### W2 — Stability window includes the just-committed snapshot
History is queried **after** the current snapshot is committed, ordered by `created_at DESC`, limit `ALPHA_STABILITY_WINDOW`. This means the very first snapshot can be included in its own stability evaluation, trivially achieving 100% spread/liquidity consistency for a single data point (though the size check `< ALPHA_STABILITY_WINDOW` still blocks approval if total history count < window). For a token with exactly `ALPHA_STABILITY_WINDOW` snapshots, the current one counted in the window means the history spans only N-1 independent prior observations.

**Risk:** Slightly overstated stability scores on first-window transitions. Conservatively, this tightens approval, not loosens it, because diversity decreases when the newest row is identical to prior rows.

### W3 — `book_collapses_fast` uses absolute `MAX_TRADE_XRP * 2` threshold
The spoof-detection heuristic compares the top-2 ask XRP value to `MAX_TRADE_XRP * 2`. With the default `MAX_TRADE_XRP=5`, this threshold is 10 XRP — extremely sensitive. Legitimate books with sparse top levels on illiquid pairs would almost always trigger this flag, forcing rejection and a manipulation log. Additionally, this flag will always be `True` for any book where top-2 ask XRP < 10, regardless of whether the rest of the book is deep, inflating false-rejection rates.

**Risk:** May over-reject moderate-liquidity book structures when `MAX_TRADE_XRP` is small. Not a safety risk — the failure mode is excessive rejection, not accidental approval.

### W4 — `slippage_pct` may be negative (not clipped in scoring)
When fill simulation finds VWAP < best ask (e.g. if multiple levels are at identical prices), slippage would be negative. The raw value is stored in `AlphaSignal.slippage_pct`. The `slippage_penalty` in scoring is clamped via `_clamp()`, so negative slippage becomes 0.0 penalty — which is correct. However, raw negative slippage in the persistence record could mislead attribution analysis.

**Risk:** Attribution-only concern; no incorrect rejections caused by this.

### W5 — `suspicious_issuer` flag checks only `r000` prefix
Suspicious issuer detection is limited to empty issuer strings and `r000…` patterns. This ignores other common spoofed-token patterns (e.g. known rug-pull addresses, zero-supply issuers, self-referential issuers).

**Risk:** Manipulation from spoofed issuers not matching `r000` pattern will not be flagged at this level. Mitigation: the register-token flow validates issuer XRPL address format, so malformed issuers cannot be registered. But a legitimate-format issuer address could still be a rug.

### W6 — `RiskDecisionRecord` does not store the signal ID
`RiskDecisionRecord` stores `token_id`, `snapshot_id`, `decision`, `reason`, alpha `score`, and `reasons_json`. It does **not** store a `signal_id` foreign key. This means you cannot directly join a risk decision record back to the specific signal that triggered it without timestamp inference.

**Risk:** Attribution gap. Fine for paper modes, but impedes performance forensics when multiple candidates exist per snapshot.

### W7 — `AlphaSignal` stores `component_scores` and `manipulation_flags` only in-memory, not persisted
The `AlphaEvaluation` dataclass carries `component_scores` and `manipulation_flags` dicts but neither is stored in the `AlphaSignal` database model. Only the final scalar fields are persisted.

**Risk:** Post-hoc debugging of why a specific signal scored as it did is difficult — the constituent factor scores are discarded. Attribution analysis would require re-running the engine.

### W8 — `stability_score` in `AlphaSignal` is the mean of three sub-scores, discarding sub-values
The stored `stability_score` collapses `spread_stability`, `liquidity_consistency`, and `mid_price_stability` into a single mean. The individual components are not stored.

**Risk:** In attribution, you cannot distinguish between a rejection that stemmed from price instability vs. liquidity instability vs. spread instability. Attribution is limited to scalar-level granularity.

### W9 — All approvals pass a fixed `ALPHA_MIN_SCORE=0.72` threshold, but in practice, `stable_enough=False` blocks nearly everything on short-lived tokens
For a new token with fewer than 6 snapshots (window default = 6), `stable_enough` is always `False`, forcing rejection regardless of score. This is correct behavior, but means **no new token can ever be approved until it has accumulated 6 pipeline cycles of history**. This is an intentional design choice but is not documented in code comments.

**Risk:** No safety risk. Latent behavior that could surprise operators analyzing approval rates of newly-added tokens.

---

## 3. SAFETY RISKS

| ID | Description | Severity |
|----|-------------|----------|
| S1 | Cooldown is non-persistent and per-invocation only — sustained rejection bursts cannot accumulate cooldown state across separate `run_once` calls (e.g., a scheduler calling it every 10 minutes would reset the count each time). | LOW |
| S2 | `RiskDecisionRecord` is written **before** the risk denial path, meaning a denied signal still generates a `RiskDecisionRecord` with `decision=DENY`. This is correct but could be misread as a successful decision in the risk table without filtering by the `decision` field. | LOW |
| S3 | `live_trading_requested=False` is hardcoded in all `RiskContext` constructions. If a future pipeline variant accidentally passes `True`, the safety comment provides no enforcement. The `LIVE_TRADING_ENABLED=False` default is the enforcement backstop. | LOW |

---

## 4. TRADING-MODEL RISKS

| ID | Description | Impact |
|----|-------------|--------|
| T1 | `book_collapses_fast` threshold (W3) will over-reject valid structures with `MAX_TRADE_XRP=5`, potentially suppressing alpha signals even on reasonable books. | Median — inflate apparent rejection rate |
| T2 | Cooldown is global per-run-once invocation (W1). A multi-token watchlist may have later tokens blocked unfairly in the same cycle. | Medium — rare with ≤3 active tokens |
| T3 | Approval requires full stability window (W9). New tokens will always reject for first N cycles. Paper performance attribution must account for this warm-up period. | Attribution: always mark first N results as "under evaluation" |
| T4 | `AlphaSignal.slippage_pct` can be stored as negative (W4). If downstream attribution divides by slippage, it could misidentify actual performance. | Low — no live action, but distorts paper attribution |
| T5 | Missing `signal_id` reference in `RiskDecisionRecord` (W6). Multi-candidate snapshots cannot be attributed to specific signal origins. | Low — single strategy at present |

---

## 5. REQUIRED FIXES BEFORE PAPER PERFORMANCE ATTRIBUTION

The following are recommended fixes before trusting performance attribution data from the paper trading ledger:

1. **[BLOCKING] Add `component_scores_json` and `manipulation_flags_json` columns to `AlphaSignal`** so each decision can be fully reconstructed from the database alone without re-running the engine.

2. **[BLOCKING] Add `signal_id` field to `RiskDecisionRecord`** so risk decisions can be joined to specific signal records for attribution.

3. **[RECOMMENDED] Make cooldown persistent** — persist rejection event timestamps in the DB (or a lightweight key-value store) so cooldown works across `run_once` call cycles, not just within one.

4. **[RECOMMENDED] Clip and store individual stability sub-scores** (`spread_stability`, `liquidity_consistency`, `mid_price_stability`) in `AlphaSignal` so attribution can drill into specific instability causes.

5. **[INFORMATIONAL] Reconsider `book_collapses_fast` threshold** — consider scaling the threshold relative to `MIN_LIQUIDITY_XRP` rather than `MAX_TRADE_XRP * 2`, which is far too small for the default trade size.

6. **[INFORMATIONAL] Document stability window warm-up** in `AlphaEngine.evaluate` docstring so operators know new tokens will reject for first `ALPHA_STABILITY_WINDOW` pipeline cycles.

7. **[INFORMATIONAL] Clip negative slippage** in `AlphaSignal.slippage_pct` storage — `slippage_pct = max(0.0, slippage_estimate)` before persistence to prevent misleading attribution charts.

---

## 6. LIVE-TRADING / TRANSACTION-SUBMISSION AUDIT

**Result: CLEAN — no live-trading or transaction-submission paths added in Phase 4.**

Verified:
- `XRPLReadOnlyClient` has no `submit`, `sign`, or wallet-broadcast methods.
- `app.execution.pipeline` does not call any XRPL write endpoints.
- `live_trading_requested=False` is hardcoded in all `RiskContext` constructions.
- `LIVE_TRADING_ENABLED=False` by default in `Settings`.
- No new environment variables that could enable live trading were added.

---

## 7. TEST COVERAGE SUMMARY

| Test file | Coverage |
|-----------|----------|
| `test_alpha_engine.py` | Spread missing, book concentrated, fill probability too low, cooldown triggers |
| `test_api.py` | All 4 new phase-4 endpoints: `/signals/alpha`, `/market/depth`, `/market/history`, `/risk/decisions` |
| `test_pipeline.py` | Signals stored, risk denials stored, updated for alpha engine injection |
| `test_risk.py` | Kill switch, exposure, spread, liquidity, thin book, slippage gates |
| `test_market_data_hardening.py` | Orderbook math, normalization, spread/liquidity accuracy |
| `test_orderbook_snapshot.py` | Snapshot validity, parsing edge cases |
| `test_paper_execution.py` | PnL math, open/close trade lifecycle |
| `test_safety.py` | Settings guard, live trading disabled |
| `test_strategy.py` | Strategy signal generation |

**Missing test cases (no automated coverage):**
- Alpha approves correctly on a well-formed, stable, deep, low-slippage book.
- `simulate_fill` with empty ask list.
- Negative-slippage storage in `AlphaSignal`.
- Cooldown does NOT trigger before threshold count.
- Stability window boundary: exactly `ALPHA_STABILITY_WINDOW - 1` snapshots should reject; exactly `ALPHA_STABILITY_WINDOW` should reach evaluation.

---

## 8. PYTEST RESULT

```
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\Codex Projects\Sonic_XRPL_Autotrader
configfile: pyproject.toml
testpaths: tests
41 passed in 6.00s
```

All 41 tests pass. No failures. No warnings.
