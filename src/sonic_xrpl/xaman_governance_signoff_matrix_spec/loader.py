from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_signoff_matrix_spec.models import (
    XamanGovernanceFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_governance_signoff_matrix_fixture(
    path: str | Path,
) -> XamanGovernanceFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        matrix_id=str(payload.get("matrix_id") or ""),
        has_safety_guards_evidence=_to_bool(payload.get("has_safety_guards_evidence", False)),
        has_xaman_payload_boundary_evidence=_to_bool(payload.get("has_xaman_payload_boundary_evidence", False)),
        has_testnet_boundary_evidence=_to_bool(payload.get("has_testnet_boundary_evidence", False)),
        has_wallet_material_boundary_evidence=_to_bool(payload.get("has_wallet_material_boundary_evidence", False)),
        has_dependency_supply_chain_evidence=_to_bool(payload.get("has_dependency_supply_chain_evidence", False)),
        has_firstledger_data_boundary_evidence=_to_bool(payload.get("has_firstledger_data_boundary_evidence", False)),
        has_operator_consent_evidence=_to_bool(payload.get("has_operator_consent_evidence", False)),
        has_rollback_readiness_evidence=_to_bool(payload.get("has_rollback_readiness_evidence", False)),
        has_observability_evidence=_to_bool(payload.get("has_observability_evidence", False)),
        has_incident_response_evidence=_to_bool(payload.get("has_incident_response_evidence", False)),
        has_legal_policy_review_evidence=_to_bool(payload.get("has_legal_policy_review_evidence", False)),
        has_safety_scan_review_triage=_to_bool(payload.get("has_safety_scan_review_triage", False)),
        has_guard_critical_approval=_to_bool(payload.get("has_guard_critical_approval", False)),
        invalid_xaman_payload_ambiguity_marker=_to_bool(payload.get("invalid_xaman_payload_ambiguity_marker", False)),
        invalid_wallet_material_ambiguity_marker=_to_bool(payload.get("invalid_wallet_material_ambiguity_marker", False)),
        invalid_dependency_risk_marker=_to_bool(payload.get("invalid_dependency_risk_marker", False)),
        invalid_testnet_approved_marker=_to_bool(payload.get("invalid_testnet_approved_marker", False)),
        invalid_live_approved_marker=_to_bool(payload.get("invalid_live_approved_marker", False)),
        invalid_runtime_execution_marker=_to_bool(payload.get("invalid_runtime_execution_marker", False)),
    )
