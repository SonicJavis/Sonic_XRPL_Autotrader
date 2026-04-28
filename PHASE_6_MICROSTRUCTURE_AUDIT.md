# Phase 6 Microstructure Audit

Date: 2026-04-28
Scope: XRPL microstructure + ledger realism simulation (paper-only, deterministic)

## Ledger Timing Status
- Implemented explicit ledger fields on `ExecutionRecord`:
  - `ledger_index_snapshot`
  - `ledger_index_signal`
  - `ledger_index_execution`
  - `ledger_index_inclusion`
- Enforced invariants:
  - snapshot <= signal <= execution <= inclusion
  - inclusion delay bounded by config (`MIN_LEDGER_DELAY`, `MAX_LEDGER_DELAY`)
- Invalid ordering raises `FAILED_INVALID_LEDGER_TIMING`.

## Latency Model Status
- Implemented staged latency fields:
  - `snapshot_to_decision_ms`
  - `decision_to_submission_ms`
  - `submission_to_inclusion_ms`
  - `total_execution_latency_ms`
- Simulator now computes total latency from stage sum and rejects stale snapshots accordingly.
- Longer staged latency increases effective latency haircut pessimistically.

## Drift Model Status
- Added deterministic pessimistic drift window (`EXECUTION_WINDOW_SNAPSHOTS`).
- Simulates over-window deterioration only:
  - level removal
  - liquidity shrinkage
  - spread widening
  - top-of-book deterioration
- Guarantees:
  - never improves entry price
  - never creates hidden liquidity
  - never improves fillability compared with no-drift baseline

## Inclusion Uncertainty Status
- Added inclusion metadata on executions:
  - `inclusion_delay_ledgers`
  - `inclusion_status` (`INCLUDED`, `DELAYED`, `FAILED_INCLUSION`)
  - `inclusion_failure_reason`
- Added deterministic inclusion model in pipeline (no network broadcast/signing).
- Behavior:
  - `FAILED_INCLUSION` forces `UNFILLED` and prevents position creation
  - `DELAYED` applies additional execution degradation
  - failed inclusion releases reserved capital

## Multi-Ledger Partial Fill Status
- Added `ExecutionFillSlice` model with per-ledger slice persistence:
  - `execution_id`, `ledger_index`, `side`
  - `requested_size`, `filled_size`, `avg_price`
  - `fill_status`, `fill_levels_json`, `degradation_factors_json`
- Added deterministic slice creation for each execution.
- Enforced attribution usage:
  - position entry size uses sum of slice fills
  - exit attribution uses slice-effective fill size
  - failed inclusion creates unfilled slice(s), no realized PnL impact

## Deterministic Replay Status
- Added replay engine: `app/execution/replay_engine.py`
- Replay reconstructs:
  - fill size
  - VWAP
  - fill status
  - slippage reference
  - realized PnL from persisted exit fills
  - failure reason
- Added checksum-based integrity check across slice fill-level payloads.
- Replay result status:
  - `REPLAY_OK`
  - `REPLAY_MISMATCH` (including `slice_levels_checksum_mismatch`)

## API + Dashboard Surfaces Status
- Added API endpoints:
  - `GET /execution/replay/{execution_id}`
  - `GET /execution/ledger-slices/{execution_id}`
  - `GET /execution/latency-summary`
  - `GET /execution/inclusion-summary`
- Dashboard now exposes (paper/simulated labeled surfaces):
  - inclusion status counts
  - ledger delay distribution
  - fill slices per execution
  - replay mismatch alerts
  - staged latency/degradation metrics
- Failures are shown first in dedicated sections.

## XRPL Limitations Still Not Modeled
- Real transaction queue contention from live mempool
- Real validator consensus timing variance
- Real pathfinding/autobridging execution routes
- Issuer transfer rates
- Frozen/authorized trustline enforcement from live ledger state
- True offer fundedness from current validated ledger balances

## Pytest Result
- Full suite run before this audit commit:
  - `126 passed`

## Invariant Check
- No midpoint pricing: enforced
- No static snapshot fantasy: enforced via staged latency + drift window
- No instant execution: enforced via staged latency and ledger ordering
- No hidden liquidity: enforced
- No fill without consumed depth: enforced
- No position without fill: enforced
- No PnL without exit fill: enforced
- No capital reuse while locked: enforced
- No stale snapshot execution: enforced
- No replay mismatch tolerance: enforced via replay status + mismatch signaling
