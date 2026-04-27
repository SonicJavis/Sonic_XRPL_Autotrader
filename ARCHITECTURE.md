# Architecture

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
