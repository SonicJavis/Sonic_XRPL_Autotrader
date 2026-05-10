# Architecture

## Canonical Path Decision: Pending

The repository has not resolved which surface is the future canonical runtime
path. No runtime migration or sniper/live work until this decision is resolved +
PR 4 safety tests pass.

Open options:

- Option A: Keep `app/` as canonical runtime.
- Option B: Promote `src/sonic_xrpl/` to future canonical runtime.
- Option C: Adapter hybrid (`app/` API shell + V2 domain logic).

Facts vs inference:

- Fact: `app/main.py` is current runnable API.
- Fact: `src/sonic_xrpl/` is V2 governance/offline stack.
- Inference: `src/sonic_xrpl/` is likely future target but not yet runtime canonical.

This document describes the current `app/` architecture surface. It does not
make `app/` the future canonical runtime by itself.

---

The project is organized as a safety-first modular trading foundation:

- `app/config.py`: typed runtime settings with conservative defaults.
- `app/db/`: SQLite persistence models and session management.
- `app/xrpl_core/`: read-only XRPL wrappers and transaction builder placeholders.
- `app/market_data/`: token registry and market metric helpers.
- `app/strategies/`: pluggable strategy interfaces and scanner strategy.
- `app/risk/`: deterministic risk checks and kill switch.
- `app/execution/`: scanner context, paper executor, orchestration pipeline.
- `app/telemetry/`: structured event logging and event contracts.
- `app/api/`: FastAPI route modules.
- `dashboard/`: Streamlit operational view.

Pipeline flow:

`strategy registry -> signal generation -> risk evaluation -> paper execution -> audit/telemetry`

Live trading is intentionally not implemented in this phase.
