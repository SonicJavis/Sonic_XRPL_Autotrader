# Sonic XRPL Autotrader (Scaffold)

Local scaffold for an XRP Ledger autotrader project.

## Structure

- `app/`: core trading modules (config, strategy, trader, XRPL client wrapper)
- `dashboard/`: Streamlit dashboard placeholder
- `tests/`: pytest suite for core behavior

## Quickstart

1. Create and activate a virtual environment.
2. Install package and dev dependencies:
   - `pip install -e .[dev]`
3. Run tests:
   - `pytest`
4. Run trader loop:
   - `autotrader`
5. Run dashboard:
   - `streamlit run dashboard/app.py`

## Env setup

Copy `.env.example` to `.env` and update values as needed.
