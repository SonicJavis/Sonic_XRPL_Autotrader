# Phase 50: Signal Review Workflow

Scope
- Build a paper-only signal review workflow that consumes Phase 49 FirstLedger candidate signals and turns them into human-reviewable paper decisions. No live or signed actions are performed.

Goals
- Determine which FirstLedger candidates should be reviewed and why.
- Produce deterministic, paper-only decisions with traceable evidence.
- Export review queue, paper decisions, and paper intents for operator review.
- Provide an offline CLI to generate reviews and reports from fixture data.

Operational rules
- Phase 50 is strictly paper-only and offline.
- No wallet, signing, submission, or live trading allowed.
- All decisions must be deterministic and traceable to Phase 49 evidence.
- All outputs must be auditable with an explicit safety statement.

Workflow steps (high level)
- 1. Load Phase 49 signals from fixture input.
- 2. Apply conservative decision policy to generate SignalReviewItem, PaperDecision, and PaperTradeIntent records.
- 3. Build a ReviewQueue (sorted by priority) and an AuditTrail.
- 4. Produce CLI reports (JSON + Markdown) in reports/phase50.
- 5. Validate offline with targeted unit tests and safety checks.

Notes
- This doc is an official Phase 50 guide for the Phase workflow.
- Phase 50 does not alter runtime trading and remains offline.
