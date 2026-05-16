from __future__ import annotations

from sonic_xrpl.xaman_governance_evidence_attestation_spec.models import (
    ATTESTATION_BLOCKED,
    ATTESTATION_NOT_READY,
    ATTESTATION_REVIEW_REQUIRED,
    ATTESTATION_SPEC_REVIEW_READY,
    IntegrityFinding,
    XamanGovernanceEvidenceAttestationFixtureInput,
    XamanGovernanceEvidenceAttestationReport,
    XamanGovernanceEvidenceAttestationSpec,
)

TERMINAL_ATTESTATION_STATES = {
    "ATTESTED_FOR_SPEC_REVIEW",
    "REVIEW_REQUIRED",
    "REJECTED",
    "BLOCKED",
    "EXPIRED",
    "SUPERSEDED",
}


def build_xaman_governance_evidence_attestation_spec(
    row: XamanGovernanceEvidenceAttestationFixtureInput,
) -> XamanGovernanceEvidenceAttestationReport:
    errors: list[str] = []
    blockers: list[str] = []
    findings: list[IntegrityFinding] = []

    if not row.evidence_artifacts:
        errors.append("missing_evidence_artifacts")
        findings.append(
            IntegrityFinding("P7101", "missing_artifact", "CRITICAL", "Evidence artifact list is empty.")
        )

    if not row.attestations:
        errors.append("missing_attestations")
        findings.append(
            IntegrityFinding("P7102", "missing_reviewer", "CRITICAL", "No attestation records supplied.")
        )

    if not row.has_dependency_report:
        errors.append("missing_dependency_report")
        findings.append(
            IntegrityFinding("P7103", "dependency_report_missing", "HIGH", "Dependency report evidence is required.")
        )
    if not row.has_safety_scan_triage:
        errors.append("missing_safety_scan_triage")
        findings.append(
            IntegrityFinding("P7104", "untriaged_safety_review", "HIGH", "Safety scan review triage evidence is missing.")
        )
    if not row.has_rollback_evidence:
        errors.append("missing_rollback_evidence")
        findings.append(
            IntegrityFinding("P7105", "rollback_evidence_missing", "HIGH", "Rollback evidence is missing.")
        )
    if not row.has_incident_response_evidence:
        errors.append("missing_incident_response_evidence")
        findings.append(
            IntegrityFinding("P7106", "incident_response_evidence_missing", "HIGH", "Incident response evidence is missing.")
        )

    for artifact in row.evidence_artifacts:
        if not artifact.deterministic_hash:
            errors.append(f"hash_missing:{artifact.evidence_id}")
            findings.append(
                IntegrityFinding("P7111", "missing_hash", "HIGH", f"Deterministic hash missing for {artifact.evidence_id}.")
            )
        if artifact.synthetic_only:
            errors.append(f"synthetic_only:{artifact.evidence_id}")
            findings.append(
                IntegrityFinding("P7112", "synthetic_only_evidence", "MEDIUM", f"Artifact {artifact.evidence_id} is synthetic-only.")
            )
        if not artifact.owner_role:
            errors.append(f"missing_owner:{artifact.evidence_id}")
            findings.append(
                IntegrityFinding("P7113", "missing_owner", "MEDIUM", f"Artifact {artifact.evidence_id} has no owner role.")
            )
        if artifact.reviewed_at.startswith("2020-") or artifact.reviewed_at.startswith("2021-"):
            errors.append(f"stale_evidence:{artifact.evidence_id}")
            findings.append(
                IntegrityFinding("P7115", "stale_evidence", "MEDIUM", f"Artifact {artifact.evidence_id} appears stale.")
            )
        if not artifact.linked_signoff_domain:
            errors.append(f"ambiguous_signoff_linkage:{artifact.evidence_id}")
            findings.append(
                IntegrityFinding("P7114", "ambiguous_signoff_linkage", "HIGH", f"Artifact {artifact.evidence_id} is not linked to a sign-off domain.")
            )

    attestation_index = {item.evidence_id for item in row.attestations}
    for artifact in row.evidence_artifacts:
        if artifact.evidence_id not in attestation_index:
            errors.append(f"missing_attestation:{artifact.evidence_id}")

    for attestation in row.attestations:
        if not attestation.reviewer_role:
            errors.append(f"missing_reviewer:{attestation.attestation_id}")
        if attestation.attestation_status not in TERMINAL_ATTESTATION_STATES and attestation.attestation_status not in {
            "NOT_ATTESTED",
            "EVIDENCE_PENDING",
        }:
            errors.append(f"unknown_attestation_status:{attestation.attestation_id}")

    if row.invalid_payload_or_execution_approval_marker:
        blockers.append("blocked_invalid_payload_or_execution_approval_marker")
        errors.append("blocked_invalid_payload_or_execution_approval_marker")
        findings.append(
            IntegrityFinding("P7121", "unsafe_runtime_path", "CRITICAL", "Fixture contains prohibited payload/testnet/live approval marker.")
        )
    if row.invalid_wallet_material_ambiguity_marker:
        blockers.append("blocked_invalid_wallet_material_ambiguity_marker")
        errors.append("blocked_invalid_wallet_material_ambiguity_marker")
        findings.append(
            IntegrityFinding("P7122", "wallet_material_ambiguity", "CRITICAL", "Fixture contains prohibited wallet-material ambiguity marker.")
        )

    if blockers:
        readiness = ATTESTATION_BLOCKED
    elif errors:
        if len(errors) >= 8:
            readiness = ATTESTATION_NOT_READY
        else:
            readiness = ATTESTATION_REVIEW_REQUIRED
    else:
        readiness = ATTESTATION_SPEC_REVIEW_READY

    spec = XamanGovernanceEvidenceAttestationSpec(
        phase="71",
        objective="Xaman governance evidence integrity and attestation contract spec",
        bundle_id=row.bundle_id,
        evidence_artifacts=row.evidence_artifacts,
        attestations=row.attestations,
        findings=tuple(findings),
    )
    return XamanGovernanceEvidenceAttestationReport(
        fixture_id=row.fixture_id,
        spec=spec,
        readiness_classification=readiness,
        validation_errors=tuple(errors),
        blockers=tuple(blockers),
    )
