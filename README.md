# ⚡ Sonic XRPL Autotrader

Production-quality automated trading system for the XRP Ledger.

> **⚠️ DISCLAIMER:** This software is for educational and research purposes only.
> It is **NOT** financial advice. All live trading is disabled by default and must
> be explicitly enabled with full awareness of the risks.

---

## Architecture

```
app/
├── config.py              # Pydantic Settings (loaded from .env)
├── main.py                # FastAPI application entry point
├── db/
│   ├── models.py          # SQLModel models (Token, Signal, PaperTrade)
│   └── session.py         # SQLite engine & session factory
├── xrpl_core/
│   ├── client.py          # JSON-RPC client wrapper
│   ├── wallet.py          # Wallet loader (seed from env only)
│   ├── transactions.py    # OfferCreate builder + safe submit
│   └── ledger_stream.py   # WebSocket transaction stream
├── strategies/
│   ├── base.py            # BaseStrategy ABC + SignalPayload
│   ├── strategy_registry.py
│   └── new_token_scanner.py  # Phase-1 placeholder strategy
├── risk/
│   ├── rules.py           # Position size + open-trade limits
│   └── kill_switch.py     # KILL_SWITCH file sentinel
├── execution/
│   ├── paper.py           # PaperExecutor (simulated trades)
│   └── scanner.py         # Strategy → Risk → Execution pipeline
├── api/
│   └── routes_health.py   # /health endpoints
└── telemetry/
    └── __init__.py        # Structured logging (structlog)

dashboard/
└── streamlit_app.py       # Real-time monitoring dashboard

tests/                     # pytest test suite
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env as needed — do NOT enable live trading without full review
```

### 3. Run the API server

```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

### 4. Run the dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

### 5. Run tests

```bash
pytest
```

---

## Safety Rules

| Rule | Default | Notes |
|------|---------|-------|
| `LIVE_TRADING_ENABLED` | `false` | Must be explicitly set to `true` |
| `BOT_MODE` | `PAPER_TRADING` | Change to `LIVE_TRADING` *and* set flag |
| Kill switch | inactive | Create a `KILL_SWITCH` file to halt all new entries |
| Wallet seed | not set | Only required for live trading |

### Kill Switch

Create a file named `KILL_SWITCH` in the project root to immediately block all
new trade entries. Existing positions can still be closed.

```bash
touch KILL_SWITCH      # activate
rm KILL_SWITCH         # deactivate
```

---

## Development Phases

- [x] Phase 1 — Project scaffold
- [x] Phase 2 — Config, FastAPI, database models
- [x] Phase 3 — XRPL core (client, wallet, transactions, stream)
- [x] Phase 4 — Paper trading engine
- [x] Phase 5 — Strategy engine (NewTokenScannerStrategy)
- [x] Phase 6 — Risk engine (rules + kill switch)
- [x] Phase 7 — Strategy → Risk → Execution pipeline
- [x] Phase 8 — Streamlit dashboard
- [x] Phase 9 — Structured logging & telemetry
- [x] Phase 10 — Safety locks (LIVE_TRADING_ENABLED guard)
- [ ] Phase 11 — FirstLedger integration
- [ ] Phase 12 — Real XRPL execution
- [ ] Phase 13 — Advanced strategies
- [ ] Phase 14 — Autonomous risk management

---

## License

MIT
