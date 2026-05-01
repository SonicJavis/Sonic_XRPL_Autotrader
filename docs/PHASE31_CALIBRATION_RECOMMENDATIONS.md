# Phase 31: Human-Guided Calibration Recommendations

## Purpose
Phase 31 adds a read-only, human-guided analytical layer that consumes Phase 30 reconciliation reports. It surfaces specific areas where the simulator's theoretical predictions deviated from real-world execution metadata. 

This module strictly produces **human-reviewable recommendations**. It does NOT change, tune, mutate, or auto-calibrate any parameters within the system. It merely points out where the models or the data collection processes need human attention.

## Relationship to Phase 30
Phase 30 measures the deterministic drift between expectation and reality. Phase 31 interprets those measurements into structured recommendations grouped by category (e.g., `fee_model`, `ledger_timing`, `metadata_collection`).

## Input & Output Files
**Inputs:**
- `reconciliation_records.jsonl`
- `reconciliation_summary.json`
- `reconciliation_limitations.txt`

**Outputs (Append-only to `reports/phase31/<timestamp>/`):**
- `calibration_observations.jsonl`
- `calibration_recommendations.jsonl`
- `calibration_summary.json`
- `calibration_recommendations.md`

## Safety & XRPL Truth Rules Inherited
This phase strictly inherits the XRPL finality constraints implemented in Phase 30:
1. Submission is NOT validation.
2. `tesSUCCESS` does NOT prove the expected trading outcome happened.
3. Only validated ledger metadata serves as final reality.
4. If metadata is missing, we CANNOT infer fill quality or slippage.
5. Missing metadata caps recommendation confidence and redirects the recommendation to focus on improving data collection rather than tweaking models.

## Why Missing Metadata Blocks High Confidence
Without on-chain metadata (e.g. `meta.delivered_amount`), any status recorded (even a manual `tesSUCCESS`) is merely an assertion of technical protocol success, not an assertion of financial success (e.g., the liquidity might have been entirely consumed by a previous transaction). Therefore, any drift flag raised without metadata must be treated with low or medium confidence, and the engine must recommend improving metadata collection rather than altering core trading assumptions.

## Why Recommendations Are Human-Only & Auto-Calibration is Forbidden
This system is an advisory intelligence platform. Auto-calibration introduces dangerous feedback loops where the engine might start relaxing its safety margins or fee caps based on faulty or incomplete data, leading to eventual financial loss. Safety, determinism, and auditability take precedence over automated convenience.

## Confidence Rules
- **High Confidence**: Requires at least 10 affected records, at least 10 metadata-backed pieces of evidence, and no major limitations or ambiguity.
- **Medium/Low Confidence**: Applied when records are few or lacking strict metadata-backed proof.

## Prohibited Behaviors
The system explicitly forbids:
- Adjusting parameters automatically.
- Inferring `0` slippage from missing slippage data.
- Treating unvalidated transactions as completed.
- Selecting the first match when ambiguous mappings occur.

## CLI Usage
```bash
python -m execution_prototype.calibration_recommendations.cli \
  --phase30-report ./reports/phase30/<timestamp> \
  --output-dir ./reports/phase31
```
