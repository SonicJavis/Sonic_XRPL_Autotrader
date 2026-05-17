# Sonic XRPL Autotrader

Safety-first modular XRPL trading-system foundation with paper execution only and XRPL live shadow observation.

## Canonical Path Decision: Resolved

Canonical future runtime surface: `src/sonic_xrpl/`.
Decision record: `docs/CANONICAL_PATH_DECISION.md`.

No runtime migration or sniper/live work may proceed unless required safety
conformance tests and audit gates pass.

Historical checkpoint label retained for audit compatibility:
`Canonical Path Decision: Pending` (resolved by `docs/CANONICAL_PATH_DECISION.md`).

Facts vs inference:

- Fact: `app/main.py` is current runnable API.
- Fact: `src/sonic_xrpl/` is V2 governance/offline stack.
- Decision: `src/sonic_xrpl/` is the canonical future runtime target.

The commands below describe the current runnable API and dashboard only. They do
not authorize runtime migration, live execution, sniper-style behavior, signing,
or transaction submission.

Phase 57 adds runtime-profile consolidation and conformance reporting under
`src/sonic_xrpl/runtime_profile/` and `reports/phase57/` to reduce app/V2 drift
while preserving paper-only fail-closed execution boundaries.

## Legacy Freeze Status

- `app/` is the current runnable legacy API/paper runtime surface.
- `execution_prototype/` is historical/reference-only unless used by named
  tests or bridge adapters.
- Xaman/manual submission content under `execution_prototype/` is historical
  manual prototype behavior only and is not V2 runtime authorization.
- No new features may be added to `app/` or `execution_prototype/` until the
  convergence migration is complete; changes are limited to compatibility and
  safety-preserving migration steps in `docs/CANONICAL_PATH_DECISION.md`.
  All migration steps require safety conformance tests pass.
  This repository remains blocked until required safety conformance tests pass.

## Phase 58C Migration-Safe Control Checks

Phase 58C adds deterministic migration-safe control checks only.

- Live trading remains blocked.
- No runtime migration is performed.
- No signing, submission, autofill, wallet-material handling, Xaman payload
  implementation, or FirstLedger live ingestion is authorized.
- Runtime behavior remains unchanged and fail-closed.
- Migration-safety references:
  - `docs/MIGRATION_SAFE_CONTROL_CHECKS.md`
  - `docs/MIGRATION_READINESS_MATRIX.md`
  - `scripts/migration_safe_check.py`

## Phase 59 FirstLedger Intelligence Expansion

Phase 59 adds deterministic FirstLedger intelligence under
`src/sonic_xrpl/firstledger_intelligence/` using fixture-backed inputs only.

- Intelligence-only, paper-only, non-executing.
- No live FirstLedger ingestion and no network calls.
- No signing, submission, autofill, wallet handling, or Xaman payloads.
- Positive labels are review/paper-only labels, not execution instructions.
- Missing or synthetic-only evidence cannot become positive qualification.

## Phase 60 Paper-Only Sniper Simulation Harness

Phase 60 adds deterministic paper-sniper simulation under
`src/sonic_xrpl/paper_sniper_simulation/` using offline fixtures only.

- Simulation-only and paper-only.
- Explicit fill/no-fill/partial-fill/slippage/latency assumptions.
- Rejection paths for unsafe or insufficient-evidence candidates.
- No live ingestion, no execution path, and no wallet/signing/submission.

## Phase 61 Xaman Manual Approval Design Spec Only

Phase 61 adds deterministic design-spec contracts under
`src/sonic_xrpl/xaman_manual_approval_spec/` using offline fixtures only.

- Spec-only and non-executing.
- Defines consent UX, replay-protection, audit-trail, and blocker contracts.
- Explicitly blocks payload creation, signing, submission, autofill, wallet
  material handling, and live execution.

## Phase 62 Xaman Testnet Payload Schema Review

Phase 62 adds deterministic schema/verification review contracts under
`src/sonic_xrpl/xaman_testnet_payload_spec/` using offline fixtures only.

- Design-review only and non-executing.
- Defines testnet-only payload schema gates and callback verification checklists.
- Explicitly blocks payload creation, Xaman API calls, signing, submission,
  wallet material handling, and live execution.

## Phase 63 Xaman Callback Verification Spec

Phase 63 adds deterministic callback authenticity and replay-verification
design contracts under `src/sonic_xrpl/xaman_callback_verification_spec/`
using offline fixtures only.

- Callback-spec-only and non-executing.
- Defines authenticity, nonce/TTL/replay, idempotency, duplicate-callback,
  audit-trail, consent-linkage, and gate checklist requirements.
- Explicitly blocks callback handlers, webhook runtime, API routes, payload
  creation, Xaman API/SDK integration, signing, submission, wallet material
  handling, testnet execution, and live execution.

## Phase 64 Xaman Audit + Idempotency Store Spec

Phase 64 adds deterministic audit-trail and idempotency-store design contracts
under `src/sonic_xrpl/xaman_audit_idempotency_spec/` using offline fixtures
only.

- Spec-only and non-executing.
- Defines callback audit-envelope bindings, idempotency key/conflict/replay
  policies, and append-only tamper-evident audit requirements.
- Explicitly blocks persistence implementation, database writes, callback
  runtime, payload creation, Xaman API/SDK integration, signing/submission,
  wallet material handling, and testnet/live execution.

## Phase 65 Xaman Approval State Machine Spec

Phase 65 adds deterministic approval state and transition design contracts
under `src/sonic_xrpl/xaman_approval_state_machine_spec/` using offline
fixtures only.

- Spec-only and non-executing.
- Defines allowed states, valid transitions, invalid transition blocks, and
  evidence/audit/idempotency/replay requirements.
- Explicitly blocks runtime state machine implementation, persistence/DB
  writes, callback runtime, payload/API/signing/submission/wallet handling,
  and testnet/live execution.

## Phase 66 Xaman Operator Consent UX Contract Spec

Phase 66 adds deterministic operator consent UX contract design outputs under
`src/sonic_xrpl/xaman_operator_consent_ux_spec/` using offline fixtures only.

- Spec-only and non-executing.
- Defines required disclosures, acknowledgement contracts, confirmation phrase
  requirements, and rejection/cancellation requirements.
- Explicitly blocks UI implementation, API/runtime services, persistence/DB
  writes, callback runtime, payload/API/signing/submission/wallet handling,
  and testnet/live execution.

## Phase 67 Xaman Consent Evidence Pack Spec

Phase 67 adds deterministic operator consent evidence-pack contract outputs
under `src/sonic_xrpl/xaman_consent_evidence_pack_spec/` using offline
fixtures only.

- Spec-only and non-executing.
- Defines evidence completeness, traceability, risk disclosure, and blocker
  status requirements for future operator consent reviews.
- Explicitly blocks UI/API/runtime implementation, export/file-write
  implementation, persistence/DB writes, callback runtime, payload/API/
  signing/submission/wallet handling, and testnet/live execution.

## Phase 68 Xaman Preflight Safety Checklist Spec

Phase 68 adds deterministic preflight safety checklist contract outputs under
`src/sonic_xrpl/xaman_preflight_safety_checklist_spec/` using offline fixtures
only.

- Spec-only and non-executing.
- Defines required preflight gates, blocker checks, and checklist outcomes for
  future approval readiness reviews.
- Explicitly blocks runtime checklist runners, UI/API/runtime implementation,
  export/file-write implementation, persistence/DB writes, callback runtime,
  payload/API/signing/submission/wallet handling, and testnet/live execution.

## Phase 69 Xaman Dry-Run Readiness Review Pack Spec

Phase 69 adds deterministic dry-run readiness review pack outputs under
`src/sonic_xrpl/xaman_dry_run_readiness_review_spec/` using offline fixtures
only.

- Spec-only and non-executing.
- Defines prerequisite-reference completeness and safety-gate status contracts
  for future dry-run readiness reviews.
- Explicitly blocks runtime dry-run/checklist runners, UI/API/runtime
  implementation, export/file-write implementation, persistence/DB writes,
  callback runtime, payload/API/signing/submission/wallet handling, and
  testnet/live execution.

## Phase 70 Xaman Testnet Governance Sign-Off Matrix Spec

Phase 70 adds deterministic governance sign-off matrix outputs under
`src/sonic_xrpl/xaman_governance_signoff_matrix_spec/` using offline fixtures
only.

- Spec-only and non-executing.
- Defines governance roles, sign-off domains/statuses, evidence requirements,
  blocker categories, and conservative readiness classifications.
- Explicitly blocks runtime runners, callback runtime, payload/API/SDK usage,
  signing/submission/autofill/wallet handling, and testnet/live execution.

## Phase 71 Xaman Governance Evidence Integrity + Attestation Spec

Phase 71 adds deterministic governance evidence integrity and attestation
outputs under `src/sonic_xrpl/xaman_governance_evidence_attestation_spec/`
using offline fixtures only.

- Spec-only and attestation-only.
- Defines evidence artifact records, attestation records, integrity findings,
  traceability mapping, and conservative readiness classifications.
- Explicitly blocks payload/API/SDK usage, signing/submission/autofill/wallet
  handling, and testnet/live execution.

## Phase 58B Policy / Spec Hardening

Phase 58B is documentation/policy/spec hardening only.

- Live trading remains blocked.
- No signing, submission, autofill, wallet-material handling, Xaman payload
  implementation, or FirstLedger live ingestion is authorized.
- Runtime behavior remains unchanged and fail-closed.
- Authoritative policy references:
  - `docs/LIVE_READINESS_POLICY.md`
  - `docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md`
  - `docs/XAMAN_FUTURE_INTEGRATION_POLICY.md`
  - `docs/FIRSTLEDGER_FUTURE_INGESTION_POLICY.md`
  - `docs/POLICY_INDEX.md`

## Architecture

- `app/config.py`: runtime settings and safety defaults
- `app/db/`: SQLModel schemas and SQLite session helpers
- `app/xrpl_core/`: read-only XRPL client and placeholders
- `app/market_data/`: token registry and market metrics
- `app/strategies/`: strategy interface and scanner strategy
- `app/risk/`: deterministic risk controls and kill switch
- `app/execution/`: paper executor and orchestration pipeline
- `app/telemetry/`: structured logging and event payloads
- `app/api/`: FastAPI routes
- `dashboard/streamlit_app.py`: local dashboard

## Setup

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -e .[dev]`
3. Copy `.env.example` to `.env` and adjust values.

## Run Tests

**Windows (recommended):** Use the virtual-environment interpreter so that
project dependencies (`sqlmodel`, `xrpl-py`, etc.) are available:

```powershell
# Create and activate the venv once:
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Then run tests with the venv interpreter (not the global `python`):
.venv\Scripts\python.exe -m pytest
```

**Linux / macOS (with venv activated):**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

> **Note:** Running bare `python -m pytest` without installing into the venv
> will fail if the global Python interpreter does not have `sqlmodel`, `xrpl`,
> or other project dependencies.  Always use the venv interpreter or activate
> the venv first.

## Run API

- `python -m app.main`

When `ALLOW_REMOTE_ACCESS=false`, run the API on `127.0.0.1` only.

## Run Dashboard

- `streamlit run dashboard/streamlit_app.py`

## Phase 9 Live Shadow Mode

Phase 9 adds XRPL live shadow observation only.

- Read-only: live observation does not mutate execution configuration or auto-apply calibration/validation outputs.
- Shadow-only: the system simulates hypothetical ledger-aligned outcomes and does not place real trades.
- No wallet/signing/broadcast: there is no wallet signing flow, no transaction autofill path, and no XRPL transaction submission path for live shadow mode.
- Snapshot limitation: XRPL `book_offers` is treated as a snapshot request, not a continuous orderbook stream. Observed liquidity may be stale, unfunded, or non-executable.

### Live Shadow API

The FastAPI app exposes read-only shadow endpoints:

- `GET /live/status`
- `GET /live/metrics`
- `GET /live/executions`
- `GET /live/uncertainty`

Each live endpoint explicitly returns:

- `is_live=true`
- `is_shadow=true`
- `is_executable=false`
- `is_truth=false`
- `xrpl_warning`

### Dashboard Panels

The Streamlit dashboard includes live shadow surfaces for:

- ledger status
- snapshot age / quality
- shadow execution stream
- real-time disagreement / uncertainty framing
- execution possibility range
- XRPL warnings panel

## Safety Rules

- `BOT_MODE` defaults to `PAPER_TRADING`.
- `LIVE_TRADING_ENABLED` defaults to `false`.
- Wallet seed is optional for paper/scanner flows.
- Risk checks always run before execution.
- Kill switch blocks new entries and allows exits.
- No live trading execution path is enabled.

## Current Status

- Live trading is not implemented.
- Live shadow mode is read-only, shadow-only, and non-executing.

## Phase 72 Xaman Governance Evidence Review Workflow Spec

Phase 72 adds deterministic governance evidence review workflow contracts under
`src/sonic_xrpl/xaman_governance_evidence_review_workflow_spec/` with
fixture-backed review, handoff, escalation, and traceability outputs.

This phase remains spec-only and non-executing:

- no runtime workflow engine
- no callback/webhook runtime
- no Xaman payload creation/API/SDK usage
- no signing/submission/autofill/wallet handling
- no testnet execution
- no live execution

## Phase 73 Xaman Governance Escalation Resolution SLA Spec

Phase 73 adds deterministic governance escalation-resolution SLA contracts
under
`src/sonic_xrpl/xaman_governance_escalation_resolution_sla_spec/`
with fixture-backed overdue/expiry classification, accountability records, and
traceability outputs.

This phase remains spec-only and non-executing:

- no runtime SLA engine
- no scheduler
- no notification sender
- no callback/webhook runtime
- no Xaman payload creation/API/SDK usage
- no signing/submission/autofill/wallet handling
- no testnet execution
- no live execution


## Phase 74 Xaman Governance Exception Waiver Register Spec

Phase 74 adds deterministic governance exception-waiver register contracts under
`src/sonic_xrpl/xaman_governance_exception_waiver_register_spec/` with fixture-backed
waiver records, expiry/revocation rules, blocker categories, and traceability outputs.

This phase remains spec-only and non-executing:

- no runtime waiver service
- no safety bypass
- no Xaman payload creation/API/SDK usage
- no signing/submission/autofill/wallet handling
- no testnet execution
- no live execution


## Phase 75 Xaman Governance Final Readiness Bundle Spec

Phase 75 adds deterministic final governance bundle contracts under
`src/sonic_xrpl/xaman_governance_final_readiness_bundle_spec/` with artifact references,
completeness checks, limitation register entries, and final fail-closed readiness outputs.

This phase remains spec-only and non-executing:

- no runtime readiness service
- no safety bypass
- no Xaman payload creation/API/SDK usage
- no signing/submission/autofill/wallet handling
- no testnet execution
- no live execution
