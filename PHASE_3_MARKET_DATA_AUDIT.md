# PHASE_3_MARKET_DATA_AUDIT

## Scope

Audit focus:
- XRPL book_offers direction correctness
- taker_gets / taker_pays normalization
- XRP drops to XRP conversion
- IOU amount parsing
- bid/ask classification
- price_xrp_per_token math
- spread calculation
- liquidity calculation
- slippage estimation
- snapshot persistence
- risk integration
- pipeline flow
- API output correctness
- dashboard correctness

## Pytest Result

Command run:

- python -m pytest

Result:

- 27 passed in 3.71s

## Confirmed Correct Items

- Read-only-only safety posture is intact:
  - No live transaction submission path enabled.
  - Existing submit path remains blocked by NotImplementedError when live trading is disabled.
- XRPL drops conversion exists in client normalization:
  - Integer/string drop values are converted via 1,000,000 divisor.
- IOU value parsing is supported for object-form amounts (`{"value": ...}`).
- Pipeline direction split is explicit:
  - ask book request is tagged side=ask.
  - bid book request is tagged side=bid.
- Bid/ask classification in parser is deterministic using side tags from pipeline.
- price_xrp_per_token normalization is consistently computed as XRP value / token amount.
- Spread formula is implemented as:
  - (ask - bid) / ask * 100.
- Liquidity is computed from top-of-book depth with dust and outlier filtering and aggregated into XRP value.
- Risk engine consumes market snapshot + parsed depth and applies:
  - liquidity guard
  - spread guard
  - thin-book guard
  - orderbook integrity gap guard
  - slippage guard
- Snapshot persistence is active in pipeline and stores:
  - price_xrp, spread_pct, liquidity_xrp, bid_count, ask_count, best_bid, best_ask, order count.
- API exposes market data endpoints:
  - GET /market/snapshots
  - GET /market/orderbook
- Dashboard surfaces Phase 3 market fields:
  - price, spread, liquidity, bid/ask, order count, and structure quality badge.

## Possible Math Errors / Logic Risks

- `book_offers` amount normalization can misclassify numeric strings:
  - In `XRPLReadOnlyClient._normalize_amount`, any digit-only string is treated as drops and divided by 1e6.
  - If an IOU ever appears as digit-only string (without object form), it would be incorrectly divided.
- `quality` field is fetched but ignored in parser math:
  - Current parser computes price from normalized amounts only.
  - This is acceptable for current flow but can diverge from XRPL quality semantics in partially-funded edge cases.
- Snapshot persistence loses missing-side information:
  - `spread_pct` and `price_xrp` are persisted with `0.0` fallback when unavailable, which can mask “no valid quote” vs actual zero.
- Slippage model uses only asks and assumes BUY-style fill path:
  - Works for current BUY-only scanner, but it is not side-generalized for future SELL/exit path reuse.

## XRPL-Specific Edge Cases To Address

- Partially funded offers and funded fields:
  - XRPL may expose funded amounts (`taker_gets_funded`/`taker_pays_funded`) that better represent executable depth.
  - Current parser does not prefer funded fields.
- Autobridging is not yet integrated:
  - Direct book midpoint can be inferior to autobridged path.
  - Placeholder exists, full integration is pending.
- Currency encoding edge cases:
  - Non-standard currency encodings (40-char hex style) require strict normalization/decoding policy.
- Book fragmentation across sparse levels:
  - Current outlier filtering is simple median-bounds based and may still admit pathological books.

## Security / Safety Risks

- `safe_request` timeout is post-call elapsed check, not a hard network timeout:
  - A blocked network call can still stall until underlying client returns/raises.
- API orderbook endpoint uses internal pipeline method directly:
  - Functional today, but this tight coupling can bypass dedicated validation layers as code evolves.
- Dashboard kill-switch display remains local-instance based:
  - UI does not reflect process-wide kill-switch state from running API container.

## Required Fixes Before Moving To Signal Alpha

1. Harden XRPL amount normalization with explicit asset-type context:
   - Convert drops only when amount is XRP-side by request context or field type.
2. Preserve “missing quote” semantics in persistence:
   - Store nullable price/spread in snapshots instead of forcing `0.0` fallbacks.
3. Add funded-amount aware depth handling:
   - Prefer funded fields for liquidity and slippage when present.
4. Implement true request-level timeout control in XRPL calls:
   - Use client/session timeout primitives rather than elapsed-after-return checks only.
5. Decouple API market route from private pipeline internals:
   - Introduce a dedicated market-data service boundary for orderbook retrieval.
6. Make dashboard consume shared runtime kill-switch state:
   - Avoid presenting local ephemeral status as operational truth.
7. Add targeted tests for XRPL edge cases:
   - partially funded offers
   - missing-side books with nullable persistence
   - digit-only IOU parsing guard
   - autobridge placeholder behavior contract

## Overall Verdict

Phase 3 is structurally strong for a read-only XRPL market-data foundation, with correct high-level flow (fetch -> parse -> snapshot -> strategy -> risk -> paper). The main blockers before signal alpha are XRPL edge-case hardening (amount typing, funded depth, null quote semantics) and runtime robustness/safety refinements around request timeouts and operational state consistency.
