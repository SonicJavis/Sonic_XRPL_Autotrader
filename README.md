# Sonic XRPL Autotrader

Safety-first modular XRPL trading-system foundation with paper execution only and XRPL live shadow observation.

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

The commands below describe the current runnable API and dashboard only. They do
not authorize runtime migration, live execution, sniper-style behavior, signing,
or transaction submission.

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

**Windows (recommended):** Use the virtual-environment interpreter so that
project dependencies (`sqlmodel`, `xrpl-py`, etc.) are available:

```powershell
# Create and activate the venv once:
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Then run tests with the venv interpreter (not the global `python`):
.venv\Scripts\python.exe -m pytest
```

**Linux / macOS (with venv activated):**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

> **Note:** Running bare `python -m pytest` without installing into the venv
> will fail if the global Python interpreter does not have `sqlmodel`, `xrpl`,
> or other project dependencies.  Always use the venv interpreter or activate
> the venv first.

## Run API

- `python -m app.main`

When `ALLOW_REMOTE_ACCESS=false`, run the API on `127.0.0.1` only.

## Run Dashboard

- `streamlit run dashboard/streamlit_app.py`

## Phase 9 Live Shadow Mode

Phase 9 adds XRPL live shadow observation only.

- Read-only: live observation does not mutate execution configuration or auto-apply calibration/validation outputs.
- Shadow-only: the system simulates hypothetical ledger-aligned outcomes and does not place real trades.
- No wallet/signing/broadcast: there is no wallet signing flow, no transaction autofill path, and no XRPL transaction submission path for live shadow mode.
- Snapshot limitation: XRPL `book_offers` is treated as a snapshot request, not a continuous orderbook stream. Observed liquidity may be stale, unfunded, or non-executable.

### Live Shadow API

The FastAPI app exposes read-only shadow endpoints:

- `GET /live/status`
- `GET /live/metrics`
- `GET /live/executions`
- `GET /live/uncertainty`

Each live endpoint explicitly returns:

- `is_live=true`
- `is_shadow=true`
- `is_executable=false`
- `is_truth=false`
- `xrpl_warning`

### Dashboard Panels

The Streamlit dashboard includes live shadow surfaces for:

- ledger status
- snapshot age / quality
- shadow execution stream
- real-time disagreement / uncertainty framing
- execution possibility range
- XRPL warnings panel

## Safety Rules

- `BOT_MODE` defaults to `PAPER_TRADING`.
- `LIVE_TRADING_ENABLED` defaults to `false`.
- Wallet seed is optional for paper/scanner flows.
- Risk checks always run before execution.
- Kill switch blocks new entries and allows exits.
- No live trading execution path is enabled.

## Current Status

- Live trading is not implemented.
- Live shadow mode is read-only, shadow-only, and non-executing.
