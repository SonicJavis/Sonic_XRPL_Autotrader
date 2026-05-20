# Xaman Future Integration Policy

## Current status

- Xaman is future/manual-approval-only.
- No V2 Xaman payload creation implementation exists today.
- Historical `execution_prototype` Xaman helpers are non-canonical reference material.

## Design-spec-first requirement

Any future Xaman work must begin with a design spec before implementation.
The design spec must define:

1. payload lifecycle states and transitions
2. explicit user-consent UX and confirmation semantics
3. append-only audit trail requirements
4. replay-protection rules
5. secrets/key-material handling boundaries
6. failure modes, rejection handling, and rollback behavior

## Explicitly blocked in Phase 58B

- no Xaman payload creation code
- no signing implementation
- no transaction submission implementation
- no transaction autofill implementation
- no wallet seed/private-key handling implementation

## Approval boundary

No Xaman signing/submission path may be implemented without explicit future human approval in a dedicated live-enablement phase.

## Phase 61 continuity note

Phase 61 adds design-spec-only contracts under
`src/sonic_xrpl/xaman_manual_approval_spec/`.

Phase 61 does not create payloads, call Xaman APIs, add Xaman SDK
dependencies, implement signing/submission/autofill, use wallet material, or
authorize testnet/mainnet execution.

## Phase 62 continuity note

Phase 62 adds testnet payload schema and verification design-review contracts
only under `src/sonic_xrpl/xaman_testnet_payload_spec/`.

Phase 62 does not create payloads, call Xaman APIs, add Xaman SDK
dependencies, implement signing/submission/autofill, or authorize testnet or
mainnet execution.

## Phase 63 continuity note

Phase 63 adds callback authenticity and replay-verification design contracts
only under `src/sonic_xrpl/xaman_callback_verification_spec/`.

Phase 63 does not add callback handlers, webhook runtime verification, API
routes, payload creation, Xaman API calls, SDK dependencies, signing,
submission, autofill, wallet material handling, testnet execution, or mainnet
execution.

## Phase 64 continuity note

Phase 64 adds audit-trail and idempotency-store design contracts only under
`src/sonic_xrpl/xaman_audit_idempotency_spec/`.

Phase 64 does not implement persistence, database writes, callback runtime,
API routes, payload creation, Xaman API calls, SDK dependencies, signing,
submission, autofill, wallet material handling, testnet execution, or mainnet
execution.

## Phase 65 continuity note

Phase 65 adds approval state-machine design contracts only under
`src/sonic_xrpl/xaman_approval_state_machine_spec/`.

Phase 65 does not implement runtime state-machine execution, persistence,
database writes, callback runtime, API routes, payload creation, Xaman API
calls, SDK dependencies, signing, submission, autofill, wallet material
handling, testnet execution, or mainnet execution.

## Phase 66 continuity note

Phase 66 adds operator-consent UX contract design outputs only under
`src/sonic_xrpl/xaman_operator_consent_ux_spec/`.

Phase 66 does not implement UI screens, dashboard routes, API routes, runtime
consent services, persistence/database writes, callback runtime, payload
creation, Xaman API calls, SDK dependencies, signing, submission, autofill,
wallet material handling, testnet execution, or mainnet execution.

## Phase 67 continuity note

Phase 67 adds consent evidence-pack contract design outputs only under
`src/sonic_xrpl/xaman_consent_evidence_pack_spec/`.

Phase 67 does not implement UI/dashboard/API/runtime services, export/download/
file-write implementation, persistence/database writes, callback runtime,
payload creation, Xaman API calls, SDK dependencies, signing, submission,
autofill, wallet material handling, testnet execution, or mainnet execution.

## Phase 68 continuity note

Phase 68 adds preflight safety checklist contract design outputs only under
`src/sonic_xrpl/xaman_preflight_safety_checklist_spec/`.

Phase 68 does not implement runtime checklist runners, UI/dashboard/API/runtime
services, export/download/file-write implementation, persistence/database
writes, callback runtime, payload creation, Xaman API calls, SDK dependencies,
signing, submission, autofill, wallet material handling, testnet execution, or
mainnet execution.

## Phase 69 continuity note

Phase 69 adds dry-run readiness review pack contract design outputs only under
`src/sonic_xrpl/xaman_dry_run_readiness_review_spec/`.

Phase 69 does not implement runtime dry-run runners, runtime checklist runners,
UI/dashboard/API/runtime services, export/download/file-write implementation,
persistence/database writes, callback runtime, payload creation, Xaman API
calls, SDK dependencies, signing, submission, autofill, wallet material
handling, testnet execution, or mainnet execution.

## Phase 70 continuity note

Phase 70 adds governance sign-off matrix contract design outputs only under
`src/sonic_xrpl/xaman_governance_signoff_matrix_spec/`.

Phase 70 does not implement runtime runners, UI/dashboard/API/runtime
services, export/download/file-write implementation, persistence/database
writes, callback runtime, payload creation, Xaman API calls, SDK dependencies,
signing, submission, autofill, wallet material handling, testnet execution, or
mainnet execution.

## Phase 71 continuity note

Phase 71 adds governance evidence integrity and attestation contract design
outputs only under
`src/sonic_xrpl/xaman_governance_evidence_attestation_spec/`.

Phase 71 does not implement runtime attestation services, runtime runners,
UI/dashboard/API/runtime services, callback runtime, payload creation, Xaman
API calls, SDK dependencies, signing, submission, autofill, wallet material
handling, testnet execution, or mainnet execution.

## Phase 72 continuity note

Phase 72 adds governance evidence review workflow contract design outputs only
under `src/sonic_xrpl/xaman_governance_evidence_review_workflow_spec/`.

Phase 72 does not implement runtime workflow engines, runtime services,
UI/dashboard/API/runtime services, callback/webhook runtime, payload creation,
Xaman API calls, SDK dependencies, signing, submission, autofill, wallet
material handling, testnet execution, or mainnet execution.

## Phase 73 continuity note

Phase 73 adds governance escalation-resolution SLA contract design outputs only
under `src/sonic_xrpl/xaman_governance_escalation_resolution_sla_spec/`.

Phase 73 does not implement runtime SLA engines, schedulers, notification
senders, callback/webhook runtime, UI/dashboard/API/runtime services, payload
creation, Xaman API calls, SDK dependencies, signing, submission, autofill,
wallet material handling, testnet execution, or mainnet execution.


## Phase 74 continuity note

Phase 74 adds governance exception waiver register contract design outputs only under
`src/sonic_xrpl/xaman_governance_exception_waiver_register_spec/`.

Phase 74 does not implement runtime waiver services, safety bypasses, payload creation,
Xaman API calls, SDK dependencies, signing, submission, autofill, wallet material handling,
testnet execution, or mainnet execution.


## Phase 75 continuity note

Phase 75 adds governance final readiness bundle contract design outputs only under
`src/sonic_xrpl/xaman_governance_final_readiness_bundle_spec/`.

Phase 75 does not implement runtime readiness services, safety bypasses, payload creation,
Xaman API calls, SDK dependencies, signing, submission, autofill, wallet material handling,
testnet execution, or mainnet execution.

## Phase 76 review export boundary

Phase 76 may package deterministic synthetic review evidence for spec review only. It does not authorize runtime export services, downloadable archives, API/UI export routes, payload creation, Xaman API/SDK usage, signing, submission, autofill, wallet handling, testnet execution, or live execution.

## Phase 77 manifest audit boundary

Phase 77 may audit deterministic synthetic review-export manifests for spec review only. It does not authorize runtime manifest audit services, downloadable archives, API/UI audit routes, payload creation, Xaman API/SDK usage, signing, submission, autofill, wallet handling, testnet execution, or live execution.

## Phase 78 approval packet boundary

Phase 78 may compose deterministic synthetic approval packets for spec review only. It does not authorize runtime approval services, downloadable archives, API/UI approval routes, payload creation, Xaman API/SDK usage, signing, submission, autofill, wallet handling, testnet execution, or live execution.

## Phase 79 review checklist boundary

Phase 79 may compose deterministic synthetic review checklists for spec review only. It does not authorize runtime checklist services, downloadable archives, API/UI checklist routes, payload creation, Xaman API/SDK usage, signing, submission, autofill, wallet handling, testnet execution, or live execution.
