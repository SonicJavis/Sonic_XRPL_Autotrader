# Phase 10 XRPL Calibration Audit

Date: 2026-04-28
Scope: XRPL-aware Bayesian shadow calibration layer (read-only, advisory-only, non-executing)

## Core Statement

Phase 10 adds a Bayesian shadow calibration layer that learns systematic simulator error under XRPL execution uncertainty.

This layer is advisory only.

It does not execute trades, does not sign transactions, does not use wallets, does not broadcast transactions, and does not auto-apply calibration outputs.

## XRPL-Specific Risks Modeled

The calibration layer explicitly encodes:

1. `book_offers` is snapshot-derived liquidity, not executable certainty
2. visible liquidity may be unfunded or stale
3. pathfinding is non-deterministic
4. ledger timing dominates fill outcomes
5. execution competition is invisible
6. partial fills are the normal case, not the exception

## Phantom Liquidity Explanation

Phase 10 introduces phantom liquidity measurement:

- `phantom_liquidity = max(0, snapshot_derived_liquidity - observed_possible_fill)`
- `phantom_penalty = min(phantom_liquidity / requested_size, 1.0)`

Interpretation:

- visible depth may overstate what shadow observation suggests was plausibly fillable
- higher phantom penalty increases pessimism
- expected slippage multipliers are widened conservatively from this signal

## Path Instability Explanation

Route instability is modeled from:

- route changes across snapshots when available
- fallback to `1 - route_confidence` when explicit route sequences are unavailable

This prevents direct-pair visibility from being treated as stable route evidence.

## Ledger Competition Explanation

Competition risk is modeled when:

- the simulator appears substantially fillable
- observed_possible_fill remains minimal

This produces a competition penalty that reduces competition reliability and increases conservative risk multipliers.

## Decay Logic Justification

Bayesian reliability updates use time decay:

- `decay_factor = exp(-age_seconds / decay_half_life)`
- default half-life: `300 seconds`

This is required because XRPL conditions change quickly. Older disagreements should influence reliability less than recent shadow disagreement.

## Reliability Dimensions

Phase 10 tracks lower-bound reliability separately for:

- liquidity
- path
- latency
- fill
- competition

Only conservative lower bounds are surfaced for decision support. Means are not used as decision inputs.

## Safety Guarantees

- paper-only: preserved
- read-only: preserved
- non-executing: preserved
- no wallet usage: preserved
- no signing: preserved
- no transaction submission: preserved
- no live trading: preserved
- no auto calibration application: preserved
- fail-closed outputs: preserved
- pessimistic default posture: preserved

## API Safety Review

New advisory endpoints:

- `GET /calibration/shadow/xrpl/errors`
- `GET /calibration/shadow/xrpl/reliability`
- `GET /calibration/shadow/xrpl/recommendations`

Each response includes:

- `is_shadow_calibration=true`
- `is_truth=false`
- `is_executable=false`
- `auto_apply=false`
- `requires_manual_review=true`
- `xrpl_warning`

## Dashboard Safety Review

Phase 10 dashboard additions surface:

- phantom liquidity vs observed_possible_fill
- route instability
- ledger delay distribution
- competition failure rate
- reliability lower bounds only

Warnings explicitly state:

- XRPL liquidity is not guaranteed executable
- observed orderbook data may be stale or unfunded
- calibration is advisory only

## Determinism Check

- calculations are deterministic
- decay uses explicit timestamps only
- no randomness introduced
- no external mutation path added

## Pytest Requirement

Phase 10 is only valid if the full suite passes after implementation.