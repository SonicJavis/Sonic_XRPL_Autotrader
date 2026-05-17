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

### Phase 58A - Guard Hardening and Safety Review Triage (Paper-Only)

- Add explicit `REQUIRES_REVIEW` triage policy documentation for safety-scan results.
- Add guard-critical changed-file detection in CI-visible safety checks.
- Keep all controls fail-closed and paper-only.
- No signing, submission, autofill, wallet material handling, runtime mutation, or live enablement.

### Phase 58B - Policy / Spec Hardening (Docs-Only)

- Add authoritative live-readiness policy and explicit post-58 blocker gates.
- Add canonical runtime ownership policy for `src/sonic_xrpl/`, `app/`, and
  `execution_prototype/` boundaries.
- Add Xaman future integration policy (design-spec-first, manual approval only).
- Add FirstLedger future ingestion policy (evidence/provenance-first, fail-closed).
- Add policy index and docs-check registration for Phase 58B policy docs.
- Keep live execution blocked; no signing/submission/autofill/wallet/Xaman
  payload implementation/FirstLedger live ingestion implementation.

### Phase 58C - Migration-Safe Control Checks (Docs/Scripts/Tests Only)

- Define authoritative migration-safe control policy before any future app-to-V2 migration work.
- Create deterministic migration readiness matrix covering all runtime surfaces.
- Add `scripts/migration_safe_check.py` — local deterministic invariant checker.
- Add `tests/safety/test_migration_safe_check.py` — safety tests.
- Integrate migration-safe check into safety-gate CI workflow.
- Register new docs/script in docs-check and guard-critical inventory.
- No runtime migration performed. No live execution enabled.

---

## Phase 59 - FirstLedger Source-Backed Sniper Intelligence Expansion (Paper-Only)

- Expand deterministic FirstLedger intelligence under `src/sonic_xrpl/`.
- Require source-backed evidence for positive paper-only candidate labels.
- Preserve fail-closed behavior for malformed, missing, stale, synthetic-only,
  or conflicting evidence.
- Add deterministic fixture-backed risk coverage for concentration, liquidity,
  freeze/clawback, metadata mismatch, and symbol-collision scenarios.
- Add offline report/view-model outputs for operator review only.
- No live ingestion, no execution coupling, and no runtime mutation.

---

## Phase 60 - Paper-Only Sniper Simulation Harness

- Consume Phase 59 intelligence outputs with deterministic fixture-backed inputs.
- Simulate paper-only entry/exit outcomes with explicit assumptions:
  no-fill, partial-fill, slippage, latency, and ledger-window constraints.
- Reject unsafe or insufficient-evidence candidates with fail-closed reasons.
- Keep all simulation output advisory and non-executing.
- No live ingestion, no order placement, and no runtime mutation.

---

## Phase 61 - Xaman Manual Approval Design Spec Only

- Define deterministic manual-approval design contracts only.
- Add consent UX, replay-protection, expiry/TTL, cancellation, and audit-trail
  requirements as spec outputs.
- Add deterministic threat model and implementation blocker register outputs.
- Keep future testnet and mainnet execution gates blocked.
- No Xaman payload/API/SDK implementation, no signing/submission/autofill/wallet
  handling, and no runtime mutation.

---

## Phase 62 - Xaman Testnet Payload Schema + Verification Design Review

- Define deterministic testnet-only payload schema requirements.
- Define callback verification and replay-protection checklists.
- Define pre-submit and post-submit verification review gates.
- Keep all outputs non-executing and design-review only.
- No payload creation, no Xaman API calls, no SDK integration, and no
  signing/submission/autofill/wallet handling.

---

## Phase 63 - Xaman Testnet Callback Authenticity + Replay Verification Spec

- Define deterministic callback authenticity and replay-verification contracts.
- Define required callback/prohibited field checklists, nonce/TTL/replay
  windows, idempotency expectations, duplicate callback handling, and callback
  ordering requirements as design outputs only.
- Define threat model and blocker register for future callback runtime
  implementation phases.
- Keep all outputs non-executing and callback-spec-only.
- No callback handlers, no webhook runtime verification, no API routes, no
  payload creation, no Xaman API calls or SDK integration, and no
  signing/submission/autofill/wallet handling.

---

## Phase 64 - Xaman Testnet Audit Trail + Idempotency Store Design Spec

- Define deterministic audit-trail and idempotency-store contracts.
- Define callback event envelope bindings, idempotency key derivation, conflict
  policy, duplicate/replay/stale callback design rules, and bounded TTL
  requirements as design outputs only.
- Define append-only/tamper-evident/retention/redaction checklist requirements.
- Define future persistence, testnet, and live blocker registers.
- Keep all outputs non-executing and spec-only.
- No persistence implementation, no database writes, no callback runtime, no
  payload creation, no Xaman API calls/SDK integration, and no
  signing/submission/autofill/wallet handling.

---

## Phase 65 - Xaman Testnet Approval State Machine Design Spec

- Define deterministic approval state and transition contracts.
- Define valid transitions, invalid transitions, and transition evidence
  requirements for operator review, callback verification, and audit gates.
- Define fail-closed transition blocks for payload/API/signing/submission/
  wallet/testnet/live runtime paths.
- Keep all outputs non-executing and state-machine-spec-only.
- No runtime state machine implementation, no persistence/database writes, no
  callback runtime implementation, and no payload/API/signing/submission/
  autofill/wallet handling.

---

## Phase 68 - Xaman Testnet Preflight Safety Checklist Spec

- Define deterministic preflight checklist contracts and required safety gates.
- Require evidence-pack, payload schema, callback verification,
  audit/idempotency, approval-state, and consent-UX prerequisite gates.
- Require dependency/safety/audit/migration/guard-critical check gates.
- Require no-secrets/no-wallet-material/no-Xaman-API/no-payload/no-signing/
  submission/no-testnet/no-live gates.
- Keep all outputs non-executing and spec-only.
- No runtime checklist runner, no UI/API/runtime implementation, no
  export/file-write implementation, no persistence/database writes, and no
  payload/API/signing/submission/wallet handling.

---

## Phase 69 - Xaman Testnet Dry-Run Readiness Review Pack Spec

- Define deterministic dry-run readiness review pack contracts and outcomes.
- Compose prerequisite references from Phase 61-68 spec layers.
- Require explicit safety-gate and no-execution status completeness.
- Define fail-closed blocked markers for invalid testnet/live approval claims.
- Keep all outputs non-executing and spec-only.
- No runtime dry-run/checklist runner, no UI/API/runtime implementation, no
  export/file-write implementation, no persistence/database writes, and no
  payload/API/signing/submission/wallet handling.

---

## Phase 70 - Xaman Testnet Governance Sign-Off Matrix Spec

- Define deterministic governance roles, sign-off domains, statuses, and
  evidence requirements for future non-executing review controls.
- Define conservative readiness classifications:
  `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_ONLY_READY`, `BLOCKED`.
- Define fail-closed blockers for payload ambiguity, wallet-material ambiguity,
  dependency risk, and prohibited testnet/live approval markers.
- Keep all outputs non-executing and governance/spec-only.
- No runtime runner, no payload creation, no API/SDK usage, no signing/
  submission/autofill/wallet handling, no testnet execution, and no live
  execution.

---

## Phase 71 - Xaman Testnet Governance Evidence Integrity + Attestation Spec

- Define deterministic governance evidence artifact records and attestation
  contracts with explicit owner/reviewer linkage.
- Define integrity findings for missing artifacts, hash/provenance issues,
  stale/synthetic evidence, ambiguous sign-off linkage, and missing safety
  evidence.
- Define conservative readiness classifications:
  `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_REVIEW_READY`, `BLOCKED`.
- Keep all outputs non-executing and spec-only.
- No runtime attestation service, no callback/webhook runtime, no payload/API/
  SDK usage, no signing/submission/autofill/wallet handling, no testnet
  execution, and no live execution.

---

## Phase 72 - Xaman Testnet Governance Evidence Review Workflow Spec

- Define deterministic governance evidence review workflow roles, stages,
  statuses, transitions, handoffs, and escalation records.
- Define conservative workflow readiness classifications:
  `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_REVIEW_READY`, `BLOCKED`.
- Define fail-closed blocked/review-required outcomes for stale/missing/
  synthetic/ambiguous evidence and unsafe markers.
- Keep all outputs non-executing and review-workflow-spec-only.
- No runtime workflow engine, no callback/webhook runtime, no payload/API/SDK
  usage, no signing/submission/autofill/wallet handling, no testnet execution,
  and no live execution.

---

## Phase 73 - Xaman Testnet Governance Escalation Resolution SLA Spec

- Define deterministic escalation-resolution SLA contracts for owner
  accountability, due policy, overdue/expiry classification, and blocker
  handling.
- Define resolution-evidence linkage and traceability across Phase 70-72
  governance artifacts.
- Define conservative readiness classifications:
  `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_REVIEW_READY`, `OVERDUE`, `BLOCKED`.
- Keep all outputs non-executing and SLA-spec-only.
- No runtime SLA engine, no scheduler, no notifications, no callback/webhook
  runtime, no payload/API/SDK usage, no signing/submission/autofill/wallet
  handling, no testnet execution, and no live execution.

---

## Phase 66 - Xaman Testnet Operator Consent UX Contract Spec

- Define deterministic operator consent UX contract requirements.
- Define mandatory disclosures, acknowledgement contracts, confirmation phrase
  requirements, and rejection/cancellation requirements as design outputs only.
- Define operator identity and audit-binding checklist requirements.
- Define fail-closed blocked markers for auto-approval, one-click execution,
  and prohibited runtime/API/payload/signing/wallet paths.
- Keep all outputs non-executing and spec-only.
- No UI implementation, no API/runtime consent service, no persistence/DB
  writes, no callback runtime, and no payload/API/signing/submission/autofill/
  wallet handling.

---

## Phase 67 - Xaman Testnet Operator Consent Evidence Pack Spec

- Define deterministic evidence-pack envelope and completeness contracts.
- Define required candidate/provenance/intelligence/simulation/callback/audit/
  state-machine/consent-UX references for future operator review.
- Define explicit risk disclosure, stale/missing evidence, and blocker-status
  requirements as design outputs only.
- Define traceability matrix requirements across Phase 59-66 artifacts.
- Keep all outputs non-executing and spec-only.
- No UI/API/runtime implementation, no export/file-write implementation, no
  persistence/DB writes, no callback runtime, and no payload/API/signing/
  submission/autofill/wallet handling.

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


---

## Phase 74 - Xaman Testnet Governance Exception Waiver Register Spec

- Define deterministic waiver roles, domains, severities, statuses, expiry/revocation rules, and blocker categories.
- Define waiver traceability across Phase 70-73 governance artifacts.
- Define conservative readiness classifications:
  `NOT_READY`, `REVIEW_REQUIRED`, `SPEC_REVIEW_READY`, `EXPIRED`, `REVOKED`, `BLOCKED`.
- Keep all outputs non-executing and waiver-register-spec-only.
- No runtime waiver service, no safety bypass, no payload/API/SDK usage, no signing/submission/autofill/wallet handling, no testnet execution, and no live execution.


---

## Phase 75 - Xaman Testnet Governance Final Readiness Bundle Spec

- Compose Phase 70-74 governance artifacts into one deterministic final spec-review packet.
- Define artifact references, completeness checks, limitation register entries, traceability, and conservative final readiness classifications.
- Keep all outputs non-executing and final-readiness-bundle-spec-only.
- No runtime readiness service, no safety bypass, no payload/API/SDK usage, no signing/submission/autofill/wallet handling, no testnet execution, and no live execution.

## Phase 76 - Xaman Testnet Governance Final Readiness Review Export Spec

- Package Phase 75 plus Phase 70-74 support evidence into a deterministic reviewer export spec.
- Preserve inclusion/redaction state, manifest references, reviewer summaries, limitations, and traceability.
- No runtime export service, no download service, no API/UI export route, no payload/API/SDK usage, no signing/submission/autofill/wallet handling, no testnet execution, and no live execution.

## Phase 77 - Xaman Testnet Governance Review Export Manifest Audit Spec

- Audit Phase 76 manifest consistency, declared-versus-observed hashes, redaction labels, reviewer summaries, limitation coverage, and traceability.
- Preserve hidden-blocker detection and fail-closed audit classifications.
- No runtime manifest audit service, no download service, no API/UI audit route, no payload/API/SDK usage, no signing/submission/autofill/wallet handling, no testnet execution, and no live execution.
