from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_evidence_attestation_spec.models import (
    AttestationRecord,
    EvidenceArtifact,
    XamanGovernanceEvidenceAttestationFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _load_artifact(payload: dict) -> EvidenceArtifact:
    return EvidenceArtifact(
        evidence_id=str(payload.get("evidence_id", "")),
        source_path=str(payload.get("source_path", "")),
        evidence_type=str(payload.get("evidence_type", "")),
        governance_domain=str(payload.get("governance_domain", "")),
        linked_signoff_domain=str(payload.get("linked_signoff_domain", "")),
        deterministic_hash=str(payload.get("deterministic_hash", "")),
        provenance_label=str(payload.get("provenance_label", "")),
        synthetic_only=_to_bool(payload.get("synthetic_only", False)),
        owner_role=str(payload.get("owner_role", "")),
        reviewed_at=str(payload.get("reviewed_at", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
    )


def _load_attestation(payload: dict) -> AttestationRecord:
    return AttestationRecord(
        attestation_id=str(payload.get("attestation_id", "")),
        evidence_id=str(payload.get("evidence_id", "")),
        reviewer_role=str(payload.get("reviewer_role", "")),
        attestation_status=str(payload.get("attestation_status", "")),
        notes=str(payload.get("notes", "")),
    )


def load_xaman_governance_evidence_attestation_fixture(
    path: str | Path,
) -> XamanGovernanceEvidenceAttestationFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    artifacts = tuple(_load_artifact(item) for item in payload.get("evidence_artifacts", []))
    attestations = tuple(_load_attestation(item) for item in payload.get("attestations", []))
    return XamanGovernanceEvidenceAttestationFixtureInput(
        fixture_id=str(payload.get("fixture_id", "")),
        bundle_id=str(payload.get("bundle_id", "")),
        evidence_artifacts=artifacts,
        attestations=attestations,
        has_dependency_report=_to_bool(payload.get("has_dependency_report", False)),
        has_safety_scan_triage=_to_bool(payload.get("has_safety_scan_triage", False)),
        has_rollback_evidence=_to_bool(payload.get("has_rollback_evidence", False)),
        has_incident_response_evidence=_to_bool(payload.get("has_incident_response_evidence", False)),
        invalid_payload_or_execution_approval_marker=_to_bool(payload.get("invalid_payload_or_execution_approval_marker", False)),
        invalid_wallet_material_ambiguity_marker=_to_bool(payload.get("invalid_wallet_material_ambiguity_marker", False)),
    )
