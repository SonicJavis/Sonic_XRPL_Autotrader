from __future__ import annotations
import json
from pathlib import Path
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.models import ExportArtifactRecord, XamanGovernanceFinalReadinessReviewExportFixtureInput

def _to_bool(v):
    return v if isinstance(v, bool) else str(v).strip().lower() in {"1","true","yes"}

def _artifact(p):
    return ExportArtifactRecord(
        export_artifact_id=str(p.get("export_artifact_id", "")), source_phase_number=str(p.get("source_phase_number", "")),
        source_artifact_type=str(p.get("source_artifact_type", "")), source_reference=str(p.get("source_reference", "")),
        declared_hash=str(p.get("declared_hash", "")), inclusion_status=str(p.get("inclusion_status", "")),
        redaction_status=str(p.get("redaction_status", "")), reviewer_visibility=str(p.get("reviewer_visibility", "")),
        required_classification=str(p.get("required_classification", "")), limitation_notes=str(p.get("limitation_notes", "")),
        safety_flags=tuple(str(i) for i in p.get("safety_flags", [])),
    )

def load_xaman_governance_final_readiness_review_export_fixture(path: str | Path):
    p=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceFinalReadinessReviewExportFixtureInput(
        fixture_id=str(p.get("fixture_id", "")), export_package_id=str(p.get("export_package_id", "")), manifest_id=str(p.get("manifest_id", "")),
        deterministic_timestamp=str(p.get("deterministic_timestamp", "")), export_artifacts=tuple(_artifact(i) for i in p.get("export_artifacts", [])),
        phase75_present=_to_bool(p.get("phase75_present", False)), phase70_present=_to_bool(p.get("phase70_present", False)),
        phase71_present=_to_bool(p.get("phase71_present", False)), phase72_present=_to_bool(p.get("phase72_present", False)),
        phase73_present=_to_bool(p.get("phase73_present", False)), phase74_present=_to_bool(p.get("phase74_present", False)),
        unresolved_blocker_summary=_to_bool(p.get("unresolved_blocker_summary", False)), unresolved_limitation_summary=_to_bool(p.get("unresolved_limitation_summary", False)),
        expired_waiver_included=_to_bool(p.get("expired_waiver_included", False)), revoked_waiver_included=_to_bool(p.get("revoked_waiver_included", False)),
        overdue_critical_sla_included=_to_bool(p.get("overdue_critical_sla_included", False)), unsafe_waiver_attempt_included=_to_bool(p.get("unsafe_waiver_attempt_included", False)),
        invalid_xaman_payload_approval_marker=_to_bool(p.get("invalid_xaman_payload_approval_marker", False)), invalid_wallet_material_approval_marker=_to_bool(p.get("invalid_wallet_material_approval_marker", False)),
        invalid_signing_submission_autofill_approval_marker=_to_bool(p.get("invalid_signing_submission_autofill_approval_marker", False)), invalid_testnet_live_execution_approval_marker=_to_bool(p.get("invalid_testnet_live_execution_approval_marker", False)),
        invalid_runtime_export_service_marker=_to_bool(p.get("invalid_runtime_export_service_marker", False)), invalid_download_service_marker=_to_bool(p.get("invalid_download_service_marker", False)),
        invalid_api_ui_export_route_marker=_to_bool(p.get("invalid_api_ui_export_route_marker", False)), invalid_safety_bypass_marker=_to_bool(p.get("invalid_safety_bypass_marker", False)),
    )
