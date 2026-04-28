# Phase 9 Live Shadow Audit

## Scope

Phase 9 converts the system into a live shadow-mode observer for XRPL microstructure. It does not submit orders, sign transactions, manage wallets, or execute trades. The system remains read-only, fail-closed, and uncertainty-first.

## Ledger-Based Execution Explanation

XRPL execution is modeled at ledger boundaries only.

- Live websocket ingestion tracks ledger-close events rather than treating orderbooks as continuous streams.
- Snapshot polling is triggered on new ledgers, with interval fallback only as a stale-data recovery path.
- Shadow execution reconstructs hypothetical execution outcomes only on future ledgers `N+1`, `N+2`, and later within a bounded hold window.
- Mid-ledger fills are explicitly disabled in the shadow execution metadata.

This matters because XRPL liquidity may appear visible between closes without being executable at the next validated ledger.

## Snapshot Limitations

`book_offers` is treated as a snapshot, not a stream.

- Snapshots can be stale, delayed, or inconsistent with the next validated ledger.
- The snapshot engine tracks `snapshot_age_ms` and marks cached views as possibly stale.
- Snapshot diffs are used to identify changing top-of-book, disappearing liquidity, and flicker events.
- Missing-ledger gaps are treated as uncertainty, not as evidence of stable liquidity.

## Pathfinding Uncertainty

Path execution is explicitly uncertain.

- Direct pair visibility is not assumed to reflect actual route quality.
- Multi-hop risk increases as route count rises or direct depth disappears.
- Route instability rises with churn, stale snapshots, missing ledgers, and ledger delay.
- Path distortion likelihood rises when autobridged depth materially diverges from direct visible depth.

The live system therefore exposes `path_execution_risk` and `route_confidence` rather than any claim of path correctness.

## Fundedness Limitations

Visible orderbook depth is not treated as fully funded.

- Large visible walls can disappear between ledgers.
- Concentrated top-of-book depth is treated conservatively.
- Sequence reconstruction flags fake-wall and flicker conditions when visible depth collapses abruptly.
- Shadow execution only consumes a conservative fraction of visible depth.

## Live Calibration And Disagreement

Calibration remains read-only.

- Live disagreement metrics are added to the existing calibration gap report.
- `live_simulated_fail_rate` estimates how often the simulator appears more optimistic than shadow-observed execution.
- `ledger_delay_error` remains an uncertainty metric, not a truth label.
- `path_mismatch_rate` tracks cases where path risk and simulated fillability conflict.

These metrics harden assumptions only. They never loosen execution controls.

## Dashboard Guarantees

The live dashboard surfaces:

- ledger status
- snapshot age and quality
- ledger-based shadow executions
- live disagreement score
- execution possibility range
- explicit XRPL warnings

Required warnings are shown to prevent false confidence:

- ORDERBOOK IS SNAPSHOT ONLY
- EXECUTION OCCURS AT LEDGER CLOSE
- LIQUIDITY MAY BE UNFUNDED
- PATHFINDING MAY ALTER RESULTS

## Explicit Statement

Observed liquidity is NOT guaranteed executable liquidity.

That statement governs all Phase 9 behavior. The live system reconstructs possible execution reality under uncertainty; it does not validate truth and it does not trade.