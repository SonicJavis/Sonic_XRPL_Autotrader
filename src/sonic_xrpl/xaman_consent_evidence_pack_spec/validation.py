from __future__ import annotations

from sonic_xrpl.xaman_consent_evidence_pack_spec.evidence import (
    COMPLETENESS_REQUIREMENTS,
    EVIDENCE_REQUIREMENTS,
    TRACEABILITY_REQUIREMENTS,
)
from sonic_xrpl.xaman_consent_evidence_pack_spec.models import (
    EVIDENCE_PACK_BLOCKED,
    EVIDENCE_PACK_INVALID,
    EVIDENCE_PACK_REVIEW_REQUIRED,
    EVIDENCE_PACK_VALID,
    INSUFFICIENT_EVIDENCE,
    Phase67Blocker,
    XamanConsentEvidencePackFixtureInput,
    XamanConsentEvidencePackSpec,
    XamanConsentEvidencePackSpecReport,
)


def _base_blockers() -> tuple[Phase67Blocker, ...]:
    return (
        Phase67Blocker("P6701", "CRITICAL", "No UI/API/runtime authorization", "UI/API/runtime implementation is out of scope in Phase 67.", True, True, True),
        Phase67Blocker("P6702", "CRITICAL", "No export/persistence authorization", "Export/file-write and persistence/DB implementations are blocked.", True, True, True),
        Phase67Blocker("P6703", "CRITICAL", "No callback runtime authorization", "Callback/webhook runtime handling remains blocked.", True, True, True),
        Phase67Blocker("P6704", "CRITICAL", "No payload/API/signing/submission authorization", "Payload creation, API usage, signing, and submission remain blocked.", False, True, True),
        Phase67Blocker("P6705", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending separate approval.", False, True, True),
    )


def build_xaman_consent_evidence_pack_spec(row: XamanConsentEvidencePackFixtureInput) -> XamanConsentEvidencePackSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    checks = (
        ("missing_candidate_identity", row.has_candidate_identity),
        ("missing_provenance", row.has_provenance),
        ("missing_firstledger_intelligence_reference", row.has_firstledger_intelligence_reference),
        ("missing_paper_simulation_reference", row.has_paper_simulation_reference),
        ("missing_paper_simulation_assumptions", row.has_paper_simulation_assumptions),
        ("missing_xaman_payload_schema_reference", row.has_xaman_payload_schema_reference),
        ("missing_callback_verification_reference", row.has_callback_verification_reference),
        ("missing_audit_idempotency_reference", row.has_audit_idempotency_reference),
        ("missing_approval_state_machine_reference", row.has_approval_state_machine_reference),
        ("missing_consent_ux_reference", row.has_consent_ux_reference),
        ("missing_risk_disclosure_bundle", row.has_risk_disclosure_bundle),
        ("missing_stale_missing_evidence_disclosure", row.has_stale_missing_evidence_disclosure),
        ("missing_no_live_execution_blocker", row.has_no_live_execution_blocker),
        ("missing_wallet_material_exclusion", row.has_wallet_material_exclusion),
        ("missing_secrets_exclusion", row.has_secrets_exclusion),
    )
    for label, present in checks:
        if not present:
            errors.append(label)

    marker_map = {
        "invalid_payload_created_marker": row.invalid_payload_created_marker,
        "invalid_xaman_called_marker": row.invalid_xaman_called_marker,
        "invalid_signing_submission_marker": row.invalid_signing_submission_marker,
        "invalid_wallet_material_marker": row.invalid_wallet_material_marker,
        "invalid_export_file_write_marker": row.invalid_export_file_write_marker,
        "invalid_ui_api_runtime_marker": row.invalid_ui_api_runtime_marker,
        "invalid_testnet_live_execution_marker": row.invalid_testnet_live_execution_marker,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = EVIDENCE_PACK_BLOCKED
        elif len(errors) >= 10:
            outcome = INSUFFICIENT_EVIDENCE
        elif len(errors) >= 5:
            outcome = EVIDENCE_PACK_INVALID
        else:
            outcome = EVIDENCE_PACK_REVIEW_REQUIRED
    else:
        outcome = EVIDENCE_PACK_VALID

    spec = XamanConsentEvidencePackSpec(
        phase="67",
        objective="Xaman testnet operator consent evidence-pack contract spec",
        evidence_pack_id=row.evidence_pack_id,
        candidate_id=row.candidate_id,
        evidence_requirements=EVIDENCE_REQUIREMENTS,
        traceability_requirements=TRACEABILITY_REQUIREMENTS,
        completeness_requirements=COMPLETENESS_REQUIREMENTS,
        blockers=_base_blockers(),
    )

    return XamanConsentEvidencePackSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
