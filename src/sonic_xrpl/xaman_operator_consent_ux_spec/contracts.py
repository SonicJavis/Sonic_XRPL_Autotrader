from __future__ import annotations

from sonic_xrpl.xaman_operator_consent_ux_spec.models import ConsentDisclosureRequirement

DISCLOSURE_REQUIREMENTS: tuple[ConsentDisclosureRequirement, ...] = (
    ConsentDisclosureRequirement(
        "no_live_execution_disclosure",
        "No live execution is authorized in this phase.",
        True,
        "Prevents mistaken escalation from review-only flows into execution assumptions.",
    ),
    ConsentDisclosureRequirement(
        "no_wallet_material_disclosure",
        "No wallet material entry, handling, or use is permitted.",
        True,
        "Confirms wallet material handling remains blocked in this phase.",
    ),
    ConsentDisclosureRequirement(
        "payload_not_created_disclosure",
        "No Xaman payload is created by this spec layer.",
        True,
        "Prevents conflation of spec outputs with payload creation capability.",
    ),
    ConsentDisclosureRequirement(
        "signing_submission_unavailable_disclosure",
        "Signing and submission are unavailable and out of scope.",
        True,
        "Preserves fail-closed execution boundaries.",
    ),
    ConsentDisclosureRequirement(
        "risk_disclosure",
        "Risk disclosures must be shown before any future consent action.",
        True,
        "Requires human-readable risk framing in future UX implementations.",
    ),
    ConsentDisclosureRequirement(
        "source_provenance_section",
        "Source and provenance summary must be shown.",
        True,
        "Binds future consent review to evidence provenance rather than assumptions.",
    ),
    ConsentDisclosureRequirement(
        "paper_simulation_assumption_section",
        "Paper simulation assumptions must be shown as assumptions, not facts.",
        True,
        "Prevents misinterpretation of simulation output as executable truth.",
    ),
    ConsentDisclosureRequirement(
        "stale_missing_evidence_disclosure",
        "Stale or missing evidence must be explicitly disclosed.",
        True,
        "Ensures uncertainty remains visible during operator review.",
    ),
)

ACKNOWLEDGEMENT_REQUIREMENTS: tuple[str, ...] = (
    "Operator must acknowledge this phase is spec-only and non-executing.",
    "Operator must acknowledge no payload, signing, or submission is available.",
    "Operator must acknowledge no wallet material is requested or accepted.",
    "Operator must provide confirmation phrase before future consent completion.",
)

REJECTION_CANCELLATION_REQUIREMENTS: tuple[str, ...] = (
    "Operator rejection path must remain explicit and immediate.",
    "Operator cancellation path must remain explicit and immediate.",
    "Rejected or cancelled state must not imply future execution readiness.",
)

OPERATOR_AUDIT_BINDING_REQUIREMENTS: tuple[str, ...] = (
    "Future UX must bind operator identity to consent event records.",
    "Future UX must bind consent to candidate and paper-simulation identifiers.",
    "Future UX must preserve immutable audit references for review decisions.",
)
