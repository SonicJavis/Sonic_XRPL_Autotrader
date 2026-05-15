from __future__ import annotations

from sonic_xrpl.xaman_consent_evidence_pack_spec.models import EvidenceReferenceRequirement

EVIDENCE_REQUIREMENTS: tuple[EvidenceReferenceRequirement, ...] = (
    EvidenceReferenceRequirement("candidate_identity", "Candidate identity reference", True, "Binds review to a concrete candidate identity."),
    EvidenceReferenceRequirement("source_provenance", "Source provenance reference", True, "Ensures evidence traceability to source-backed inputs."),
    EvidenceReferenceRequirement("firstledger_intelligence", "FirstLedger intelligence reference", True, "Requires Phase 59 intelligence context."),
    EvidenceReferenceRequirement("paper_simulation", "Paper simulation reference", True, "Requires Phase 60 simulation context."),
    EvidenceReferenceRequirement("paper_simulation_assumptions", "Paper simulation assumption summary", True, "Prevents assumptions from being treated as facts."),
    EvidenceReferenceRequirement("xaman_payload_schema", "Xaman payload schema reference", True, "Binds to Phase 62 schema review context only."),
    EvidenceReferenceRequirement("callback_verification", "Callback verification reference", True, "Requires Phase 63 callback/replay context."),
    EvidenceReferenceRequirement("audit_idempotency", "Audit/idempotency reference", True, "Requires Phase 64 audit/idempotency context."),
    EvidenceReferenceRequirement("approval_state_machine", "Approval state-machine reference", True, "Requires Phase 65 transition contract context."),
    EvidenceReferenceRequirement("consent_ux_contract", "Consent UX contract reference", True, "Requires Phase 66 disclosure/acknowledgement context."),
    EvidenceReferenceRequirement("risk_disclosure_bundle", "Risk disclosure bundle", True, "Requires explicit risk framing before future consent."),
    EvidenceReferenceRequirement("stale_missing_evidence_bundle", "Stale/missing evidence disclosure", True, "Preserves uncertainty visibility."),
    EvidenceReferenceRequirement("no_live_execution_blocker", "No-live-execution blocker status", True, "Prevents mistaken escalation to execution."),
    EvidenceReferenceRequirement("wallet_material_exclusion", "Wallet-material exclusion requirement", True, "Ensures no wallet material is included."),
    EvidenceReferenceRequirement("secrets_exclusion", "Secrets exclusion requirement", True, "Ensures no secret/key material is included."),
)

TRACEABILITY_REQUIREMENTS: tuple[str, ...] = (
    "Evidence pack must map candidate identity to intelligence and simulation references.",
    "Evidence pack must map consent UX contract to required disclosure references.",
    "Evidence pack must map callback verification and audit/idempotency references to blocker status.",
    "Evidence pack must preserve explicit missing-evidence and stale-evidence trace links.",
)

COMPLETENESS_REQUIREMENTS: tuple[str, ...] = (
    "Candidate identity, provenance, intelligence, and simulation references are required.",
    "Risk, stale/missing evidence, and blocker disclosures are required.",
    "Payload not created, Xaman not called, and no signing/submission must remain explicit.",
    "Evidence pack remains spec-only and non-executing.",
)
