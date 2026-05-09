# Roadmap

---

## Phase 45 — V2 Foundation Architecture Rebuild ✅ (this phase)

Establish the V2 package foundation, protocol capability matrix, provider contracts,
execution domain models, simulation interfaces, reconciliation bridge, and CLI.
All existing tests preserved. Live trading blocked.

---

## Phase 46 — Provider Integration and Offline Fixture Expansion

- Implement `XRPLRippledProvider` (optional live network read — no submission)
- Implement `ClioProvider` (historical data read via Clio WebSocket)
- Expand fixture library for common account/ledger/AMM states
- Add provider health monitoring and failover tests
- All fixtures loadable offline

---

## Phase 47 — XRPL Capability-Aware Market Snapshot Engine

- Implement capability-aware market data ingestion from LedgerProvider
- AMM pool snapshots (using `amm_info`)
- Orderbook depth snapshots (using `book_offers`)
- Price Oracle ingestion (using `get_aggregate_price`)
- MPT issuance snapshots
- Market snapshot caching and staleness management

---

## Phase 48 — Dependency Audit / Supply-Chain Guardrails ✅

Read-only audit of Python and Node dependency supply chain.
Detects compromised xrpl.js versions. Runs pip check and pip-audit.
Produces CI artifact reports. No runtime trading behaviour changed.

---

## Phase 49 — Evidence-Backed FirstLedger Candidate Signals ✅

- Source-backed FirstLedger fixture boundary
- Deterministic candidate risk signals
- Explicit missing-evidence limitations
- Synthetic fixture labelling
- No execution approval

---

## Phase 50 — Signal Review Workflow ✅

- Paper-only signal review queue
- Deterministic paper decisions
- Paper trade intents with live execution blocked
- Offline reports for operator review

---

## Phase 51 — Paper Outcome Attribution + Signal Feedback Loop ✅

- Paper outcome observations from fixtures
- Deterministic attribution to Phase 49 signals
- Signal feedback aggregation by signal type
- Offline reports for paper review and calibration planning

---

## Phase 52 — Source-Backed Paper Observation Dataset Expansion + Outcome Replay Corpus ✅

- Larger deterministic paper observation fixture sets
- Source/provenance validation and explicit missing evidence
- Replayable paper outcome cases across canonical windows
- Conservative corpus quality scoring and reports
- Offline CLI commands for corpus validation and reporting
- No threshold calibration and no live execution

---

## Phase 53 — Calibration Readiness Review + Non-Mutating Threshold Recommendation Layer ✅

- Review Phase 52 corpus quality before any calibration proposal
- Offline readiness rules for source-backed paper evidence
- Human-review-only threshold recommendations
- No automatic calibration and no runtime mutation
- No live execution

---

## Phase 54 — Human-Reviewed Calibration Proposal Pack ✅

- Generate exact proposed calibration changes for manual review
- Include evidence tables, risk notes, rollback notes, and sign-off checklist
- Do not apply proposed changes automatically
- Live execution remains blocked

---

## Phase 55 — Reconciliation V2 and Execution Quality Reports

- Full V2 reconciliation pipeline
- Execution quality reports (fill rate, slippage, fee accuracy)
- Comparison with Phase 30 legacy reconciliation where applicable
- Exportable reports (JSON, Markdown)

---

## Phase 56 — Local Dashboard / Operator Console

- Streamlit dashboard integration with V2
- V2 health, capabilities, recent simulations display
- Paper trade P&L tracker
- Safety status panel

---

## Phase 57 — Live Readiness Checklist Only

- Structural verification checklist
- Provider connectivity tests (read-only)
- Amendment status verification
- Risk policy review
- **No live submission enabled in this phase**

---

## Phase 58 — Security Review Before Any Live Trading

- External or internal security audit
- Live guard review and sign-off
- Dependency audit
- Submission path implementation (behind new safety gates)
- **First phase where live trading may be considered**

## Roadmap reconciliation addendum — Phases 48–50

- **Phase 48**: Accurate FirstLedger discovery boundary plus dependency audit addendum. This phase established the strict parser boundary and kept missing `observed_at` missing instead of inventing launch times.
- **Phase 49**: Evidence-backed FirstLedger candidate risk + strategy signal contracts. This phase is signal/evidence only and does not execute trades.
- **Phase 50**: Paper-only signal review workflow. This phase turns signal records into review items, paper decisions, and paper intents without live execution.
- **Phase 51**: Paper outcome attribution and signal feedback. This phase links deterministic paper observations back to signals and keeps feedback advisory.
- **Phase 52**: Source-backed paper observation corpus and replay readiness. This phase expands deterministic paper observation data and quality reporting without calibration or live execution.
- **Phase 53**: Calibration readiness review and non-mutating threshold recommendation layer. This phase does not apply calibration or approve execution.
- **Phase 54**: Human-reviewed calibration proposal packs. This phase creates exact proposed before/after values for review only; it does not apply changes or enable live execution.
- **Phase 55+**: Future work may add deeper simulation, paper-trading review, dashboard presentation, live-readiness review, and security review. Live execution remains out of scope unless a future named phase explicitly authorizes it and passes safety review.
