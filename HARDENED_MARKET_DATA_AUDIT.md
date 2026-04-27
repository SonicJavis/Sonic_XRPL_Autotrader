# HARDENED_MARKET_DATA_AUDIT

## Scope

Critical correctness audit of hardened XRPL market data layer with focus on:
- amount normalization
- book direction and side math
- price/spread/liquidity/slippage correctness
- pipeline safety and risk integration
- API/dashboard output integrity
- manipulation resistance

## Pytest Validation

Command executed:

- python -m pytest

Result:

- 36 passed in 3.46s

## 1. ✅ Confirmed Correct Components

- Amount normalization utility is centralized in `normalize_amount()` and reused in XRPL client and parser flow.
- XRP drops to XRP conversion is implemented for digit-like string/int amounts (divide by 1,000,000).
- IOU amount parsing from XRPL object (`{"value": ...}`) is implemented.
- Pipeline explicitly tags and merges ask/bid views before parsing, reducing accidental side confusion.
- Parser computes `price_xrp_per_token = xrp_amount / token_amount` consistently after side mapping.
- Spread formula is correct: `(ask - bid) / ask * 100`.
- Negative spread is treated as invalid (returns `None`) and invalid snapshots are blocked before strategy execution.
- Liquidity is depth-based and split by side (`liquidity_bid_xrp`, `liquidity_ask_xrp`, `total_liquidity_xrp`).
- Slippage simulation uses progressive depth consumption with VWAP and partial-fill detection.
- Risk engine rejects on missing price/spread/liquidity, one-sided books, thin books, excessive spread, and excessive slippage.
- Pipeline prevents invalid snapshots from reaching strategy/risk path and logs invalid reason metadata.
- API market endpoints expose parsed/derived market fields in XRP-space (not drops).

## 2. ⚠️ Potential Math/Logical Risks

- `normalize_amount()` assumes any digit-only string is XRP drops.
  - If upstream ever passes a non-XRP numeric string (without IOU dict wrapper), it will be mis-scaled.
- Float conversion is used throughout for amounts/prices.
  - For extreme values, binary float rounding may introduce precision drift in comparison and filtering boundaries.
- `quality` sanity check uses minimum of direct and inverse deviation.
  - This avoids false positives on orientation ambiguity but may also under-detect some semantic mismatches.
- Outlier filtering median is computed across combined bid+ask price levels.
  - In very wide but still legitimate markets, one side can be over-pruned as outlier.
- One-sided liquidity dominance is flagged in snapshot payload but not used as a hard risk reject condition.
- API may expose `None` values for invalid quote fields (`price_xrp`, `spread_pct`, `best_bid`, `best_ask`) when snapshot invalid.
  - This is safe for backend, but consumer contracts must explicitly handle nullable fields.

## 3. ❌ Critical Issues

No critical correctness break was found that would currently allow invalid snapshot execution into strategy/paper flow.

No bypass was identified that enables live transaction submission.

## 4. XRPL-Specific Edge Cases Identified

- Empty book: handled; snapshot marked invalid and skipped.
- One-sided book: handled; spread invalid and snapshot rejected.
- Inverted/reversed book (`bid > ask`): spread becomes invalid (`None`) and snapshot rejected.
- Extreme spread (>100%): mathematically supported and then rejected by risk thresholds if configured.
- Autobridging absence: explicit placeholder exists (`autobridge_price=None`), direct price only for now.
- Token with no trustlines/no executable depth: naturally surfaces as empty/invalid snapshot.
- Partially funded offers:
  - Not explicitly using funded fields (`*_funded`) yet; this is a known XRPL microstructure sensitivity.

## 5. Manipulation Risks (Spoofing / Liquidity Traps)

- Spoof/dust resistance improved via dust filter and invalid/outlier filters.
- Fake large wall risk reduced by slippage simulation and depth checks, but remains possible if walls are rapidly canceled between snapshots.
- Outlier cutoffs (`0.2x` to `5x` median) are static and can be gamed in very sparse books.
- One-side dominance metric is computed but not yet enforced as rejection, leaving residual trap exposure.

## 6. Required Fixes BEFORE Alpha Strategies

1. Enforce explicit amount-type context in normalization path.
   - Avoid treating ambiguous numeric strings as drops unless XRP-typed by context.
2. Add funded-amount handling (`taker_gets_funded` / `taker_pays_funded`) for executable depth realism.
3. Add optional decimal-based precision path for critical price/liquidity/slippage calculations.
4. Promote one-sided liquidity dominance into explicit risk denial (or configurable risk escalation).
5. Tighten API schema contracts for nullable fields and define consumer-safe response guarantees.
6. Add tests for malformed XRPL payloads (missing keys, wrong types, huge exponent strings) and ensure safe failure behavior.

## Area-by-Area Audit Notes

### Amount Normalization

- Correct for core expected XRPL structures.
- Residual ambiguity exists for numeric strings without explicit asset context.

### Orderbook Direction

- Current bid/ask separation is pipeline-driven and parser-consistent.
- No inversion bug observed in hardened path.

### Price Math

- Formula application is consistent across parser/snapshot/risk usage.
- Division-by-zero and invalid values are filtered prior to inclusion.

### Quality Handling

- Quality is used as sanity signal, not trusted blindly.
- Deviation warnings are tracked and logged.

### Cleaning & Manipulation Resistance

- Dust, invalid, and outlier filtering implemented and tested.
- Threshold tuning remains a future calibration task.

### Liquidity & Spread

- Correct formulas and `None` propagation protections exist.
- Snapshot validity gating blocks downstream misuse.

### Slippage

- Partial-fill detection is present and integrated into risk denial.
- BUY-path modeling is appropriate for current scanner behavior.

### Pipeline Safety

- Invalid snapshot rejection is explicit and audited.
- `None` execution price is blocked before paper execution.

### Risk Integration

- Check ordering is strict and defensive.
- No obvious bypass path found in current flow.

### API & Dashboard

- Units are in XRP-space in exposed market metrics.
- Dashboard reflects backend snapshot values; invalid states are surfaced as `n/a`.

## Overall Readiness Statement

The hardened market data layer is materially safer and mathematically consistent for pre-alpha read-only/paper workflows. Remaining risks are mainly XRPL edge-depth realism (funded amounts), precision robustness, and stronger enforcement against one-sided liquidity dominance/manipulation patterns.
