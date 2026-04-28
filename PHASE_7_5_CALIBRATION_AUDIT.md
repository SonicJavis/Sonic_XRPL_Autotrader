# Phase 7.5 Calibration Audit

Date: 2026-04-28
Scope: XRPL-aware calibration feedback loop (hardened, read-only, non-executable)

## Core Objective Confirmation
- Calibration is decision support only.
- Calibration does not execute trades.
- Calibration does not auto-apply recommended penalties.
- Calibration can only preserve or increase pessimism.

## System Assumptions (Explicit)
The system assumes:
- partial fundedness
- non-deterministic pathfinding
- unreliable top-of-book visibility

Operational interpretation:
- visible depth is treated as optimistic and potentially non-executable
- fundedness confidence is conservative by design and never treated as certainty
- pathfinding distortions are modeled as additional uncertainty and slippage risk

## System Non-Capabilities (Explicit)
The system does not:
- verify account balances behind visible offers
- simulate routing/pathfinding competition across real participants
- simulate validator ordering or mempool queue visibility

## Phase 7.5 Additions
- Versioned calibration snapshots with:
  - regime
  - severity
  - XRPL risk flags JSON
- XRPL-aware regime classifier with regimes:
  - STABLE, THIN, SPOOFY, COLLAPSING, HIGH_VOLATILITY,
  - PATH_DISTORTED, ILLUSION_LIQUIDITY, UNKNOWN
- Regime-aware recommendation hardening rules:
  - PATH_DISTORTED increases slippage penalty
  - ILLUSION_LIQUIDITY increases depth haircut
  - SPOOFY reduces fundedness confidence
  - COLLAPSING increases drift and latency penalties
- Confidence hardening with penalties for:
  - low sample count
  - unstable regime switching
  - drift error
  - inclusion uncertainty
- Confidence floor behavior:
  - low confidence returns no recommendation
- Gap report upgrades with XRPL bias metrics:
  - depth_illusion_rate
  - path_distortion_rate
  - fundedness_uncertainty_score
  - ledger_delay_error
  - primary KPI retained: simulated_fail_in_real_rate
- Drift/regime interaction monitor additions:
  - regime_transition_rate
  - instability_score
  - accelerated escalation when drift worsens with unstable regime transitions
- Dashboard XRPL warnings and risk surfacing:
  - ORDERBOOK MAY NOT BE FUNDED
  - DEPTH MAY BE NON-EXECUTABLE
  - XRPL PATHFINDING MAY DISTORT FILLS
  - regime, severity, risk flags, and confidence views

## Reinforced Invariants
1. Calibration never increases optimism.
2. Depth is always treated as unreliable.
3. Fundedness is always uncertain.
4. Recommendations never auto-apply.
5. Execution system remains unchanged.
6. No live trading introduced.
7. No wallet logic introduced.
8. No network calls introduced.
9. Low confidence produces no recommendation.
10. XRPL-specific risks are always surfaced.

## Safety Posture Summary
- Pessimistic: yes
- Read-only: yes
- Non-executable: yes
- Deterministic calibration computations: yes
