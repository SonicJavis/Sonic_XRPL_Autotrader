from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_consent_evidence_pack_spec.models import XamanConsentEvidencePackFixtureInput


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_consent_evidence_pack_fixture(path: str | Path) -> XamanConsentEvidencePackFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanConsentEvidencePackFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        evidence_pack_id=str(payload.get("evidence_pack_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        has_candidate_identity=_to_bool(payload.get("has_candidate_identity", False)),
        has_provenance=_to_bool(payload.get("has_provenance", False)),
        has_firstledger_intelligence_reference=_to_bool(payload.get("has_firstledger_intelligence_reference", False)),
        has_paper_simulation_reference=_to_bool(payload.get("has_paper_simulation_reference", False)),
        has_paper_simulation_assumptions=_to_bool(payload.get("has_paper_simulation_assumptions", False)),
        has_xaman_payload_schema_reference=_to_bool(payload.get("has_xaman_payload_schema_reference", False)),
        has_callback_verification_reference=_to_bool(payload.get("has_callback_verification_reference", False)),
        has_audit_idempotency_reference=_to_bool(payload.get("has_audit_idempotency_reference", False)),
        has_approval_state_machine_reference=_to_bool(payload.get("has_approval_state_machine_reference", False)),
        has_consent_ux_reference=_to_bool(payload.get("has_consent_ux_reference", False)),
        has_risk_disclosure_bundle=_to_bool(payload.get("has_risk_disclosure_bundle", False)),
        has_stale_missing_evidence_disclosure=_to_bool(payload.get("has_stale_missing_evidence_disclosure", False)),
        has_no_live_execution_blocker=_to_bool(payload.get("has_no_live_execution_blocker", False)),
        has_wallet_material_exclusion=_to_bool(payload.get("has_wallet_material_exclusion", False)),
        has_secrets_exclusion=_to_bool(payload.get("has_secrets_exclusion", False)),
        invalid_payload_created_marker=_to_bool(payload.get("invalid_payload_created_marker", False)),
        invalid_xaman_called_marker=_to_bool(payload.get("invalid_xaman_called_marker", False)),
        invalid_signing_submission_marker=_to_bool(payload.get("invalid_signing_submission_marker", False)),
        invalid_wallet_material_marker=_to_bool(payload.get("invalid_wallet_material_marker", False)),
        invalid_export_file_write_marker=_to_bool(payload.get("invalid_export_file_write_marker", False)),
        invalid_ui_api_runtime_marker=_to_bool(payload.get("invalid_ui_api_runtime_marker", False)),
        invalid_testnet_live_execution_marker=_to_bool(payload.get("invalid_testnet_live_execution_marker", False)),
    )
