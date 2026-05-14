from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_operator_consent_ux_spec.models import XamanOperatorConsentUxFixtureInput


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_operator_consent_ux_fixture(path: str | Path) -> XamanOperatorConsentUxFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanOperatorConsentUxFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        has_no_live_execution_disclosure=_to_bool(payload.get("has_no_live_execution_disclosure", False)),
        has_no_wallet_material_disclosure=_to_bool(payload.get("has_no_wallet_material_disclosure", False)),
        has_payload_not_created_disclosure=_to_bool(payload.get("has_payload_not_created_disclosure", False)),
        has_signing_submission_unavailable_disclosure=_to_bool(payload.get("has_signing_submission_unavailable_disclosure", False)),
        has_risk_disclosure=_to_bool(payload.get("has_risk_disclosure", False)),
        has_source_provenance_section=_to_bool(payload.get("has_source_provenance_section", False)),
        has_paper_simulation_assumption_section=_to_bool(payload.get("has_paper_simulation_assumption_section", False)),
        has_stale_missing_evidence_disclosure=_to_bool(payload.get("has_stale_missing_evidence_disclosure", False)),
        has_operator_acknowledgement=_to_bool(payload.get("has_operator_acknowledgement", False)),
        has_confirmation_phrase_requirement=_to_bool(payload.get("has_confirmation_phrase_requirement", False)),
        invalid_auto_approval_marker=_to_bool(payload.get("invalid_auto_approval_marker", False)),
        invalid_one_click_execution_marker=_to_bool(payload.get("invalid_one_click_execution_marker", False)),
        attempted_ui_implementation_marker=_to_bool(payload.get("attempted_ui_implementation_marker", False)),
        attempted_api_route_marker=_to_bool(payload.get("attempted_api_route_marker", False)),
        attempted_payload_creation_marker=_to_bool(payload.get("attempted_payload_creation_marker", False)),
        attempted_xaman_api_marker=_to_bool(payload.get("attempted_xaman_api_marker", False)),
        attempted_signing_submission_marker=_to_bool(payload.get("attempted_signing_submission_marker", False)),
        attempted_wallet_material_marker=_to_bool(payload.get("attempted_wallet_material_marker", False)),
        attempted_testnet_live_execution_marker=_to_bool(payload.get("attempted_testnet_live_execution_marker", False)),
    )
