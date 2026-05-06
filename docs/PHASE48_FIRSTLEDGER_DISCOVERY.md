# Phase 48 — Accurate FirstLedger Discovery Boundary

## Status

Merged in PR #32 on 2026-05-06.

## Purpose

Phase 48 starts the FirstLedger discovery track without pretending that the dashboard has verified live launch data.

The goal is to build source-backed discovery plumbing that can later ingest FirstLedger/XRPL observations, score them, and present them for human review.

## Safety Boundary

This phase is read-only.

It does not add:

- wallet seed handling
- private key handling
- signing
- Xaman payload creation
- transaction submission
- auto-buy execution
- live sniper execution

## Data Accuracy Rule

The dashboard and discovery layer must not hardcode fake token launches as if they are live FirstLedger opportunities.

Any launch/candidate shown to the operator must be one of:

1. **Source-backed** — includes issuer, currency, validated ledger, transaction hash, metadata status, and source/provenance.
2. **Synthetic fixture** — explicitly labelled as synthetic/test data.
3. **Unavailable** — the UI should say live discovery data is unavailable rather than inventing rows.

## Parser Added

`execution_prototype/discovery/firstledger_reader.py` now parses source-backed fixture rows into `RawDiscoveryEvent` objects.

The parser is intentionally strict:

- rows with missing issuer/currency/ledger/tx hash are ignored
- unsupported event types are ignored
- unvalidated events are marked with a limitation
- missing metadata is marked as low confidence
- missing `observed_at` remains empty and is marked with `observed_at_missing`
- deterministic event IDs are generated from source-backed fields only

## Supported Discovery Event Types

- `trustline_created`
- `amm_created`
- `issuer_activity`
- `offer_activity_low_confidence`

## Validation

Run locally:

```powershell
cd "D:\Codex Projects\Sonic_XRPL_Autotrader"
.\venv\Scripts\Activate.ps1
.\run_tests.ps1
.\venv\Scripts\python.exe -m pytest tests/test_firstledger_reader.py
```

## Next Step

Add a dashboard panel that reads from source-backed discovery reports/fixtures and displays `No verified FirstLedger launch data available` when no data source exists.
