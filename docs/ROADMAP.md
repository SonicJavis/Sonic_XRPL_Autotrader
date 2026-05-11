# Roadmap

## Docs-First Migration Classification

This roadmap is part of the docs-first migration plan and follow-on hardening
work. Canonical future runtime is `src/sonic_xrpl/` (`docs/CANONICAL_PATH_DECISION.md`).
The roadmap does not authorize live execution, sniper-style execution, signing,
submission, wallet handling, or safety scanner weakening.

| Surface | Current classification | Evidence |
|---|---|---|
| `app/` | Current runnable FastAPI/paper-runtime legacy surface | `app/main.py`, `app/execution/pipeline.py`, `app/execution/execution_guard.py` |
| `execution_prototype/` | Historical/prototype/offline workflow surface | `execution_prototype/README.md`, `execution_prototype/reconciliation/`, `execution_prototype/walk_forward_replay/` |
| `src/sonic_xrpl/` | Canonical future runtime + V2 governance/offline architecture surface introduced in Phase 45+ | `docs/CANONICAL_PATH_DECISION.md`, `docs/PROJECT_BLUEPRINT.md`, `docs/V2_ARCHITECTURE.md`, `src/sonic_xrpl/` |

Phase evidence for the requested Phase 1-55 migration timeline is classified in
`docs/PHASE_LEDGER.md`. Phase 56 artifacts exist in the repository, but Phase 56
is treated as a continuation outside the requested Phase 1-55 migration timeline
until explicitly reconciled.

---

## Phase 45 - V2 Foundation Architecture Rebuild

Establish the V2 package foundation, protocol capability matrix, provider
contracts, execution domain models, simulation interfaces, reconciliation bridge,
and CLI. All existing tests preserved. Live trading blocked.

---

## Phase 46 - Provider Integration and Offline Fixture Expansion

- Implement fixture-backed provider interfaces with no submission.
- Expand fixture library for account, ledger, AMM, orderbook, metadata, and MPT states.
- Add provider health checks, fixture safety scanning, and failover tests.
- Keep all fixtures loadable offline.

---

## Phase 47 - XRPL Capability-Aware Market Snapshot Engine

- Implement capability-aware market data ingestion from provider fixtures.
- Build AMM pool snapshots, orderbook depth snapshots, account context,
  trustline context, MPT snapshots, and metadata signals.
- Add market snapshot reports and quality scoring.
- Keep live trading blocked.

---

## Phase 48 - FirstLedger Discovery Boundary + Dependency Audit

- Accurate FirstLedger discovery boundary with strict source-backed parsing.
- Dependency and supply-chain audit with `scripts/dependency_audit.py`.
- Detect compromised `xrpl.js` versions where Node dependency files exist.
- No runtime trading behavior changed.

---

## Phase 49 - Evidence-Backed FirstLedger Candidate Signals

- Source-backed FirstLedger fixture boundary.
- Deterministic candidate risk signals.
- Explicit missing-evidence limitations.
- Synthetic fixture labelling.
- No execution approval.

---

## Phase 50 - Signal Review Workflow

- Paper-only signal review queue.
- Deterministic paper decisions.
- Paper trade intents with live execution blocked.
- Offline reports for operator review.

---

## Phase 51 - Paper Outcome Attribution + Signal Feedback Loop

- Paper outcome observations from fixtures.
- Deterministic attribution to Phase 49 signals.
- Signal feedback aggregation by signal type.
- Offline reports for paper review and calibration planning.

---

## Phase 52 - Source-Backed Paper Observation Dataset Expansion + Outcome Replay Corpus

- Larger deterministic paper observation fixture sets.
- Source/provenance validation and explicit missing evidence.
- Replayable paper outcome cases across canonical windows.
- Conservative corpus quality scoring and reports.
- Offline CLI commands for corpus validation and reporting.
- No threshold calibration and no live execution.

---

## Phase 53 - Calibration Readiness Review + Non-Mutating Threshold Recommendation Layer

- Review Phase 52 corpus quality before any calibration proposal.
- Offline readiness rules for source-backed paper evidence.
- Human-review-only threshold recommendations.
- No automatic calibration and no runtime mutation.
- No live execution.

---

## Phase 54 - Human-Reviewed Calibration Proposal Pack

- Generate exact proposed calibration changes for manual review.
- Include evidence tables, risk notes, rollback notes, and sign-off checklist.
- Do not apply proposed changes automatically.
- Live execution remains blocked.

---

## Phase 55 - Human Review Approval Ledger + Calibration Change Request Workflow

- Implemented evidence: `docs/PHASE55_HUMAN_REVIEW_APPROVAL_LEDGER.md`,
  `docs/research/PHASE55_HUMAN_REVIEW_APPROVAL_LEDGER_RESEARCH.md`,
  `src/sonic_xrpl/calibration_approval/`, `tests/fixtures/calibration_approval/`,
  Phase 55 unit/smoke/safety tests, and `reports/phase55/`.
- Deterministic approval ledger from Phase 54 proposal packs plus review fixtures.
- Deterministic calibration change-request workflow for rejected/deferred edits.
- Exportable governance reports (JSON, Markdown).
- No runtime threshold mutation and no live execution enablement.

---

## Phase 56 - Approved Calibration Change Implementation Plan + Dry-Run Patch Pack

- Existing repo evidence: `docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md`,
  `docs/research/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN_RESEARCH.md`,
  `src/sonic_xrpl/calibration_implementation_plan/`, Phase 56 tests, and
  `reports/phase56/`.
- Treated as a continuation after Phase 55 and outside the requested Phase 1-55
  migration timeline for the docs-first classification work.
- Deterministic implementation plan from Phase 55 approval ledger + change requests.
- Deterministic dry-run patch preview text with no executable patch application.
- No runtime threshold mutation, no runtime config mutation, and no live execution enablement.

---

## Phase 57 - Runtime Profile Consolidation + App/V2 Drift Reduction

- Add deterministic runtime-profile contracts shared across app/V2 surfaces.
- Add profile conformance checks for execution/live flags, dry-run invariants,
  app-V2 alignment, and Docker profile alignment.
- Export deterministic runtime profile and conformance reports under `reports/phase57/`.
- Keep live execution blocked and runtime mutation blocked.

---

## Phase 58 - Security Review Before Any Live Trading

- External or internal security audit.
- Live guard review and sign-off.
- Dependency audit.
- Submission path implementation may only be considered behind new safety gates.
- First phase where live trading may be considered, and only after explicit approval.

---

## Roadmap Reconciliation Notes

- **Phase 48**: Accurate FirstLedger discovery boundary plus dependency audit addendum. This phase established the strict parser boundary and kept missing `observed_at` missing instead of inventing launch times.
- **Phase 49**: Evidence-backed FirstLedger candidate risk + strategy signal contracts. This phase is signal/evidence only and does not execute trades.
- **Phase 50**: Paper-only signal review workflow. This phase turns signal records into review items, paper decisions, and paper intents without live execution.
- **Phase 51**: Paper outcome attribution and signal feedback. This phase links deterministic paper observations back to signals and keeps feedback advisory.
- **Phase 52**: Source-backed paper observation corpus and replay readiness. This phase expands deterministic paper observation data and quality reporting without calibration or live execution.
- **Phase 53**: Calibration readiness review and non-mutating threshold recommendation layer. This phase does not apply calibration or approve execution.
- **Phase 54**: Human-reviewed calibration proposal packs. This phase creates exact proposed before/after values for review only; it does not apply changes or enable live execution.
- **Phase 55**: The earlier roadmap placeholder listed "Reconciliation V2 and Execution Quality Reports." Repository evidence now shows the implemented Phase 55 is the Human Review Approval Ledger + Calibration Change Request Workflow.
- **Phase 56**: Existing continuation evidence is present, but Phase 56 remains outside the requested Phase 1-55 migration classification timeline until explicitly reconciled.
