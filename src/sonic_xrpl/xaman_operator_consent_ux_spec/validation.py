from __future__ import annotations

from sonic_xrpl.xaman_operator_consent_ux_spec.contracts import (
    ACKNOWLEDGEMENT_REQUIREMENTS,
    DISCLOSURE_REQUIREMENTS,
    OPERATOR_AUDIT_BINDING_REQUIREMENTS,
    REJECTION_CANCELLATION_REQUIREMENTS,
)
from sonic_xrpl.xaman_operator_consent_ux_spec.models import (
    CONSENT_BLOCKED,
    CONSENT_SPEC_INVALID,
    CONSENT_SPEC_REVIEW_REQUIRED,
    CONSENT_SPEC_VALID,
    INSUFFICIENT_EVIDENCE,
    Phase66Blocker,
    XamanOperatorConsentUxFixtureInput,
    XamanOperatorConsentUxSpec,
    XamanOperatorConsentUxSpecReport,
)


def _base_blockers() -> tuple[Phase66Blocker, ...]:
    return (
        Phase66Blocker("P6601", "CRITICAL", "No UI implementation authorization", "UI implementation is out of scope for Phase 66.", True, True, True),
        Phase66Blocker("P6602", "CRITICAL", "No API/runtime consent authorization", "API routes and runtime consent services are blocked in this phase.", True, True, True),
        Phase66Blocker("P6603", "CRITICAL", "No persistence/DB authorization", "Persistence and database writes are blocked in this phase.", True, True, True),
        Phase66Blocker("P6604", "CRITICAL", "No payload/API/signing/submission authorization", "Payload creation, API usage, signing, and submission remain blocked.", False, True, True),
        Phase66Blocker("P6605", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending separate approval.", False, True, True),
    )


def build_xaman_operator_consent_ux_spec(row: XamanOperatorConsentUxFixtureInput) -> XamanOperatorConsentUxSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    checks = (
        ("missing_no_live_execution_disclosure", row.has_no_live_execution_disclosure),
        ("missing_no_wallet_material_disclosure", row.has_no_wallet_material_disclosure),
        ("missing_payload_not_created_disclosure", row.has_payload_not_created_disclosure),
        ("missing_signing_submission_unavailable_disclosure", row.has_signing_submission_unavailable_disclosure),
        ("missing_risk_disclosure", row.has_risk_disclosure),
        ("missing_source_provenance_section", row.has_source_provenance_section),
        ("missing_paper_simulation_assumption_section", row.has_paper_simulation_assumption_section),
        ("missing_stale_missing_evidence_disclosure", row.has_stale_missing_evidence_disclosure),
        ("missing_operator_acknowledgement", row.has_operator_acknowledgement),
        ("missing_confirmation_phrase_requirement", row.has_confirmation_phrase_requirement),
    )
    for label, present in checks:
        if not present:
            errors.append(label)

    marker_map = {
        "invalid_auto_approval_marker": row.invalid_auto_approval_marker,
        "invalid_one_click_execution_marker": row.invalid_one_click_execution_marker,
        "attempted_ui_implementation_marker": row.attempted_ui_implementation_marker,
        "attempted_api_route_marker": row.attempted_api_route_marker,
        "attempted_payload_creation_marker": row.attempted_payload_creation_marker,
        "attempted_xaman_api_marker": row.attempted_xaman_api_marker,
        "attempted_signing_submission_marker": row.attempted_signing_submission_marker,
        "attempted_wallet_material_marker": row.attempted_wallet_material_marker,
        "attempted_testnet_live_execution_marker": row.attempted_testnet_live_execution_marker,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = CONSENT_BLOCKED
        elif len(errors) >= 7:
            outcome = INSUFFICIENT_EVIDENCE
        elif len(errors) >= 4:
            outcome = CONSENT_SPEC_INVALID
        else:
            outcome = CONSENT_SPEC_REVIEW_REQUIRED
    else:
        outcome = CONSENT_SPEC_VALID

    spec = XamanOperatorConsentUxSpec(
        phase="66",
        objective="Xaman testnet operator consent UX contract spec",
        candidate_id=row.candidate_id,
        disclosures=DISCLOSURE_REQUIREMENTS,
        acknowledgement_requirements=ACKNOWLEDGEMENT_REQUIREMENTS,
        rejection_cancellation_requirements=REJECTION_CANCELLATION_REQUIREMENTS,
        operator_audit_binding_requirements=OPERATOR_AUDIT_BINDING_REQUIREMENTS,
        blockers=_base_blockers(),
    )

    return XamanOperatorConsentUxSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
