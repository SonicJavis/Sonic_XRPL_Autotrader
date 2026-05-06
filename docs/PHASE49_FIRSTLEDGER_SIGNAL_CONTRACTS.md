# Phase 49 — Evidence-Backed FirstLedger Candidate Risk + Strategy Signal Contracts

## Objective completed

Phase 49 adds a deterministic, offline signal contract layer that converts source-backed or explicitly limited FirstLedger candidate evidence into non-executing advisory signals:

- `BUY_CANDIDATE`
- `WATCH`
- `AVOID`
- `INSUFFICIENT_EVIDENCE`

`BUY_CANDIDATE` means only that minimum offline evidence requirements passed. It is not an execution instruction.

## Safety boundary

This phase does **not** enable live trading. It adds no wallet seed handling, no private-key handling, no mnemonic handling, no Xaman payload creation, no signing, no transaction autofill, no submit path, no `submitAndWait`, no auto-buy, no order placement, no polling loop, and no streaming loop.

Every `CandidateRiskSignal` has `live_execution_allowed=False`.

## Evidence requirements

A candidate must include:

- issuer
- currency
- transaction hash
- ledger index
- source URL or source identifier
- observed time, or a preserved `observed_at_missing` limitation
- validated metadata status, unless explicitly kept watch-only
- no critical limitations
- market snapshot context for `BUY_CANDIDATE`

Missing evidence remains explicit and lowers confidence. Unknown values remain unknown.

## Scoring limitations

The scoring layer is conservative. It rewards source-backed provenance and validated metadata, but penalizes missing required fields, unknown market context, synthetic fixtures, unvalidated metadata, and explicit freeze/clawback/risk limitations.

It does not infer liquidity from volume, holder count from transaction count, dev holdings from issuer balance, or any “safe buy”, “rug safe”, “moonshot”, liquidity lock, or burn status.

## CLI usage

```bash
PYTHONPATH=src python -m sonic_xrpl.cli.main firstledger-signals --fixture tests/fixtures/firstledger/source_backed_candidates.json
PYTHONPATH=src python -m sonic_xrpl.cli.main firstledger-signal-report --fixture tests/fixtures/firstledger/source_backed_candidates.json --output-dir reports/phase49
```

The CLI is offline/read-only and prints provenance, limitations, synthetic fixture labels, and the live-execution block.

## Rollback

No DB migrations or runtime trading changes were introduced. Roll back with:

```bash
git revert <merge_commit_sha>
```

## Next recommended step

Phase 50 should connect these signals to simulation/paper decision review only, with no live execution, and should add deeper source-backed market snapshot fixtures before any dashboard expansion.
