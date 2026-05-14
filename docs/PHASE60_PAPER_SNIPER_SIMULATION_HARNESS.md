# Phase 60 - Paper-Only Sniper Simulation Harness

## Scope

Phase 60 adds a deterministic, fixture-backed, paper-only simulation harness
under `src/sonic_xrpl/paper_sniper_simulation/`.

It consumes Phase 59 intelligence outputs through fixture-backed inputs and
models hypothetical paper outcomes only.

## Implemented evidence

- `src/sonic_xrpl/paper_sniper_simulation/models.py`
- `src/sonic_xrpl/paper_sniper_simulation/loader.py`
- `src/sonic_xrpl/paper_sniper_simulation/rules.py`
- `src/sonic_xrpl/paper_sniper_simulation/simulation.py`
- `src/sonic_xrpl/paper_sniper_simulation/reporting.py`
- `tests/fixtures/paper_sniper_simulation/`
- `tests/unit/test_phase60_paper_sniper_simulation.py`
- `tests/safety/test_phase60_paper_sniper_safety.py`
- CLI commands in `src/sonic_xrpl/cli/main.py`:
  - `paper-sniper-simulation`
  - `paper-sniper-simulation-report`

## What Phase 60 adds

- Deterministic paper-sniper simulation decisions (`SIMULATED`,
  `SIMULATION_REJECTED`).
- Explicit fill-assumption labels (`FILLED`, `PARTIAL_FILL`, `NO_FILL`,
  `REJECTED`).
- Explicit slippage, latency, ledger-window, and liquidity assumptions.
- Loader default handling: omitted `liquidity_available_pct_assumption` keeps
  the scenario default (`1.0`); explicit null/empty remains a missing-liquidity
  assumption and fails closed.
- Explicit reject/fail-closed reasons for unsafe or insufficient evidence.
- Deterministic JSON/Markdown report renderers.

## Safety interpretation

- Phase 60 is paper-only and non-executing.
- Simulated fills are assumptions, not facts.
- Simulated outcomes are paper-only assumptions, not real PnL.
- `PAPER_ONLY_CANDIDATE` and `BUY_CANDIDATE` do not become orders.
- Positive simulation output is not investment advice.

## Not authorized by Phase 60

- No live FirstLedger ingestion.
- No live network calls.
- No signing, submission, or autofill.
- No wallet seed/private-key handling.
- No Xaman payload creation or signing/submission workflow.
- No runtime mutation.
- No execution-path changes.

## Validation expectations

Phase 60 completion requires:

- Phase 60 unit/safety tests passing
- full repository safety/audit/dependency checks passing
- CLI safety checks passing
- guard-critical check passing (or explicit non-strict review note when
  expected)

Still no live execution.
