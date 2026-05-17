from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.models import (
    BundleArtifactReference,
    XamanGovernanceFinalReadinessBundleFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _load_artifact_reference(payload: dict) -> BundleArtifactReference:
    return BundleArtifactReference(
        artifact_id=str(payload.get("artifact_id", "")),
        phase_number=str(payload.get("phase_number", "")),
        artifact_type=str(payload.get("artifact_type", "")),
        source_path=str(payload.get("source_path", "")),
        declared_hash=str(payload.get("declared_hash", "")),
        required_classification=str(payload.get("required_classification", "")),
        artifact_status=str(payload.get("artifact_status", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
        safety_flags=tuple(str(item) for item in payload.get("safety_flags", [])),
    )


def load_xaman_governance_final_readiness_bundle_fixture(
    path: str | Path,
) -> XamanGovernanceFinalReadinessBundleFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceFinalReadinessBundleFixtureInput(
        fixture_id=str(payload.get("fixture_id", "")),
        final_bundle_id=str(payload.get("final_bundle_id", "")),
        deterministic_timestamp=str(payload.get("deterministic_timestamp", "")),
        artifact_references=tuple(_load_artifact_reference(i) for i in payload.get("artifact_references", [])),
        phase70_present=_to_bool(payload.get("phase70_present", False)),
        phase71_present=_to_bool(payload.get("phase71_present", False)),
        phase72_present=_to_bool(payload.get("phase72_present", False)),
        phase73_present=_to_bool(payload.get("phase73_present", False)),
        phase74_present=_to_bool(payload.get("phase74_present", False)),
        unresolved_safety_review=_to_bool(payload.get("unresolved_safety_review", False)),
        unresolved_dependency_risk=_to_bool(payload.get("unresolved_dependency_risk", False)),
        expired_waiver=_to_bool(payload.get("expired_waiver", False)),
        revoked_waiver=_to_bool(payload.get("revoked_waiver", False)),
        overdue_critical_sla=_to_bool(payload.get("overdue_critical_sla", False)),
        unsafe_waiver_attempt=_to_bool(payload.get("unsafe_waiver_attempt", False)),
        ambiguous_signoff_linkage=_to_bool(payload.get("ambiguous_signoff_linkage", False)),
        missing_rollback_evidence=_to_bool(payload.get("missing_rollback_evidence", False)),
        missing_incident_response_evidence=_to_bool(payload.get("missing_incident_response_evidence", False)),
        invalid_xaman_payload_approval_marker=_to_bool(payload.get("invalid_xaman_payload_approval_marker", False)),
        invalid_wallet_material_approval_marker=_to_bool(payload.get("invalid_wallet_material_approval_marker", False)),
        invalid_signing_submission_autofill_approval_marker=_to_bool(payload.get("invalid_signing_submission_autofill_approval_marker", False)),
        invalid_testnet_live_execution_approval_marker=_to_bool(payload.get("invalid_testnet_live_execution_approval_marker", False)),
        invalid_runtime_readiness_service_marker=_to_bool(payload.get("invalid_runtime_readiness_service_marker", False)),
        invalid_safety_bypass_marker=_to_bool(payload.get("invalid_safety_bypass_marker", False)),
    )
