# Hosted Deployment Guide

This deployment profile serves the XRPL intelligence platform as a hosted, authenticated, read-only system.

## Safety Guarantees

- Execution is disabled in hosted mode.
- No wallet, signing, submission, autofill, `OfferCreate`, or `Payment` path is exposed by the API or dashboard.
- Public API routes serve processed state only: normalized orderbook views, feasibility, hybrid liquidity, and ledger-based decay.
- Ingestion remains internal and is disabled unless explicitly configured.
- Production startup fails closed if execution flags are enabled, auth is missing, replay mode is enabled, debug is enabled, or CORS is wildcard.

## Environment

Copy `.env.example` to `.env` and set:

```env
ENV_MODE=PRODUCTION
DEBUG=false
EXECUTION_ENABLED=false
LIVE_TRADING_ENABLED=false
API_AUTH_TOKEN=<long random token>
ALLOWED_ORIGINS=https://your-dashboard.example
XRPL_INGESTION_ENABLED=false
XRPL_INGESTION_MODE=disabled
XRPL_SHADOW_SOURCE=static
```

Production must never use `ALLOWED_ORIGINS=*`.

## Run

```powershell
docker compose up --build
```

API:

```powershell
curl http://localhost:8000/health
curl -H "X-API-Token: <token>" http://localhost:8000/metrics
```

Dashboard:

```text
http://localhost:8501
```

The dashboard requires the same API access token before loading hosted data in production mode.

## Validation Commands

```powershell
.venv\Scripts\python.exe -m pytest
git grep -n -E "submit|sign|wallet|OfferCreate|Payment|autofill|secret|seed|path_find|ripple_path_find"
```

Expected grep findings are existing safety/audit wording, fail-closed placeholders, `signal/signals`, and test-only forbidden-command assertions. Any new reachable execution path is a blocker.

## XRPL Serving Rules

- Only validated ledger-derived data should be served.
- Raw `book_offers` and raw `amm_info` payloads are not exposed publicly.
- `book_offers` and `amm_info` are ledger snapshots, not durable executable guarantees.
- The dashboard is an inspection surface only and has no controls for trading, execution, signing, or config mutation.
