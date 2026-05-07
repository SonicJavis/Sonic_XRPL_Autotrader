# Phase 51: Paper Outcome Attribution + Signal Feedback Loop

Scope
- Add deterministic paper outcome attribution for Phase 49 FirstLedger signals.
- Add paper-only feedback summaries that aggregate observed fixture outcomes by signal type.
- Add offline CLI commands for outcome summaries and reports.

Out of scope
- Live trading.
- Network polling or streaming.
- Automatic threshold mutation.
- Real fill claims from fixture prices.

Workflow
- 1. Load Phase 49 FirstLedger candidate signals from a local fixture.
- 2. Load Phase 51 paper outcome observations from a local fixture.
- 3. Match observations by `signal_id` when available, otherwise by `candidate_id`.
- 4. Calculate observed return, baseline return, and excess return in basis points.
- 5. Assign `WIN`, `LOSS`, `FLAT`, or `NO_OBSERVATION` using deterministic thresholds.
- 6. Aggregate signal feedback by signal class.
- 7. Write JSON and Markdown reports when requested.

CLI commands
- `paper-outcomes --signals-fixture <firstledger.json> --outcomes-fixture <outcomes.json>`
- `paper-outcome-report --signals-fixture <firstledger.json> --outcomes-fixture <outcomes.json> --output-dir <dir>`
- `signal-feedback-report --signals-fixture <firstledger.json> --outcomes-fixture <outcomes.json> --output-dir <dir>`

Safety rules
- Phase 51 is offline and paper-only.
- Phase 51 does not alter Phase 49 signal classification or Phase 50 review policy.
- Phase 51 does not add transaction construction or execution behavior.
- All Phase 51 output records include `paper_only=True` and `live_execution_allowed=False`.

Accuracy rules
- Missing outcome rows produce `NO_OBSERVATION` with an explicit limitation.
- Fixture prices are paper observations only and do not prove available liquidity or executable fills.
- Feedback recommendations are advisory and require human review before any future scoring change.

Validation
- Unit tests cover attribution, missing observations, and feedback aggregation.
- Smoke tests cover all new CLI commands.
- Safety validation must include `python scripts/safety_grep.py` before merge.
