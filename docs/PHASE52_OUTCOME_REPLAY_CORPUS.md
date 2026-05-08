# Phase 52 - Outcome Replay Corpus

## Objective

Phase 52 adds an offline, deterministic paper observation corpus layer under
`src/sonic_xrpl/outcome_corpus/`.

The layer expands the fixture-backed foundation used by Phase 51 outcome
attribution. It loads paper observation fixture sets, validates provenance and
missing evidence, groups observations into replay cases, computes canonical
window coverage, scores corpus quality conservatively, and writes JSON and
Markdown reports.

## Canonical Windows

The corpus builder supports these paper observation windows:

- `5m`
- `15m`
- `1h`
- `4h`
- `24h`

Missing windows are recorded explicitly on each replay case. Missing timestamps,
prices, returns, liquidity, volume, and provenance remain missing or limited.
The builder does not generate replacement values.

## Safety Scope

Phase 52 is paper-only and offline.

It does not:

- fetch live FirstLedger data
- fetch live XRPL data
- use Xaman
- construct transactions
- sign transactions
- submit transactions
- enable live execution
- mutate Phase 49 scoring thresholds
- perform automatic calibration

Every corpus and replay case keeps `paper_only=True` and
`live_execution_allowed=False`.

## Quality Scoring

Corpus quality is a dataset readiness grade, not a strategy recommendation.

The scorer penalizes:

- missing canonical windows
- synthetic observations
- missing `observed_at`
- missing source/provenance
- missing reference or observed prices
- explicit limitations

Grades are conservative:

- `A`: source-backed, complete canonical windows, no critical limitations
- `B`: source-backed, most windows present, minor limitations
- `C`: partial evidence with missing windows
- `D`: very limited evidence or synthetic/mixed evidence
- `INSUFFICIENT`: empty or unusable corpus

The scorer never emits buy, sell, avoid, or threshold-change decisions.

## CLI

Phase 52 adds offline CLI commands:

```powershell
PYTHONPATH=src python -m sonic_xrpl.cli.main outcome-corpus --fixture tests/fixtures/outcome_corpus/source_backed_multi_window.json
PYTHONPATH=src python -m sonic_xrpl.cli.main outcome-corpus-quality --fixture tests/fixtures/outcome_corpus/source_backed_multi_window.json
PYTHONPATH=src python -m sonic_xrpl.cli.main outcome-corpus-report --fixture tests/fixtures/outcome_corpus/source_backed_multi_window.json --output-dir reports/phase52
```

Each command prints paper-only, offline, live-execution-blocked language.

## Reports

The report writer produces:

- `reports/phase52/outcome_corpus.json`
- `reports/phase52/outcome_corpus.md`
- `reports/phase52/outcome_corpus_quality.json`
- `reports/phase52/outcome_corpus_quality.md`

Reports include corpus ID, case counts, quality grade, complete/partial/missing
counts, canonical window coverage, source-backed versus synthetic counts,
limitations, safety statement, and the recommended next step.

## Next Step

Phase 52 prepares the ground for Phase 53 calibration review by improving
paper observation corpus quality. It does not perform calibration.
