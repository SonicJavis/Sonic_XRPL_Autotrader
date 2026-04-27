# Sonic XRPL Autotrader

Safety-first modular XRPL trading-system foundation with paper execution only.

## Architecture

- `app/config.py`: runtime settings and safety defaults
- `app/db/`: SQLModel schemas and SQLite session helpers
- `app/xrpl_core/`: read-only XRPL client and placeholders
- `app/market_data/`: token registry and market metrics
- `app/strategies/`: strategy interface and scanner strategy
- `app/risk/`: deterministic risk controls and kill switch
- `app/execution/`: paper executor and orchestration pipeline
- `app/telemetry/`: structured logging and event payloads
- `app/api/`: FastAPI routes
- `dashboard/streamlit_app.py`: local dashboard

## Setup

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -e .[dev]`
3. Copy `.env.example` to `.env` and adjust values.

## Run Tests

- `python -m pytest`

## Run API

- `python -m app.main`

When `ALLOW_REMOTE_ACCESS=false`, run the API on `127.0.0.1` only.

## Run Dashboard

- `streamlit run dashboard/streamlit_app.py`

## Safety Rules

- `BOT_MODE` defaults to `PAPER_TRADING`.
- `LIVE_TRADING_ENABLED` defaults to `false`.
- Wallet seed is optional for paper/scanner flows.
- Risk checks always run before execution.
- Kill switch blocks new entries and allows exits.
- No live trading endpoint in this phase.

## Current Status

Live trading is not implemented yet.
