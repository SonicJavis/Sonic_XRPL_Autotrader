from __future__ import annotations

import json

from sonic_xrpl.xaman_consent_evidence_pack_spec.models import XamanConsentEvidencePackSpecReport, jsonable
from sonic_xrpl.xaman_consent_evidence_pack_spec.traceability import render_traceability_matrix


def render_xaman_consent_evidence_pack_payload(report: XamanConsentEvidencePackSpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "outcome": report.outcome,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "evidence_pack_spec_only": report.spec.safety_flags.evidence_pack_spec_only,
        "export_implementation_allowed": report.spec.safety_flags.export_implementation_allowed,
        "file_write_allowed": report.spec.safety_flags.file_write_allowed,
        "ui_implementation_allowed": report.spec.safety_flags.ui_implementation_allowed,
        "api_route_allowed": report.spec.safety_flags.api_route_allowed,
        "runtime_service_allowed": report.spec.safety_flags.runtime_service_allowed,
        "persistence_implementation_allowed": report.spec.safety_flags.persistence_implementation_allowed,
        "database_writes_allowed": report.spec.safety_flags.database_writes_allowed,
        "payload_creation_allowed": report.spec.safety_flags.payload_creation_allowed,
        "xaman_api_calls_allowed": report.spec.safety_flags.xaman_api_calls_allowed,
        "signing_allowed": report.spec.safety_flags.signing_allowed,
        "submission_allowed": report.spec.safety_flags.submission_allowed,
        "wallet_material_allowed": report.spec.safety_flags.wallet_material_allowed,
        "testnet_execution_allowed": report.spec.safety_flags.testnet_execution_allowed,
        "live_execution_allowed": report.spec.safety_flags.live_execution_allowed,
        "evidence_completeness_checklist": [item.key for item in report.spec.evidence_requirements if item.required],
        "traceability_matrix": render_traceability_matrix(report),
        "risk_disclosure_checklist": [
            "risk_disclosure_bundle",
            "stale_missing_evidence_bundle",
            "wallet_material_exclusion",
            "secrets_exclusion",
            "no_live_execution_blocker",
        ],
        "spec": jsonable(report.spec),
    }


def render_xaman_consent_evidence_pack_json(report: XamanConsentEvidencePackSpecReport) -> str:
    return json.dumps(render_xaman_consent_evidence_pack_payload(report), indent=2, sort_keys=True)


def render_xaman_consent_evidence_pack_markdown(report: XamanConsentEvidencePackSpecReport) -> str:
    payload = render_xaman_consent_evidence_pack_payload(report)
    lines = [
        "# Phase 67 Xaman Consent Evidence Pack Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Outcome: `{payload['outcome']}`",
        f"- evidence_pack_spec_only: `{payload['evidence_pack_spec_only']}`",
        f"- export_implementation_allowed: `{payload['export_implementation_allowed']}`",
        f"- file_write_allowed: `{payload['file_write_allowed']}`",
        f"- ui_implementation_allowed: `{payload['ui_implementation_allowed']}`",
        f"- api_route_allowed: `{payload['api_route_allowed']}`",
        f"- runtime_service_allowed: `{payload['runtime_service_allowed']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- xaman_api_calls_allowed: `{payload['xaman_api_calls_allowed']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in (payload["validation_errors"] or ["none"]):
        lines.append(f"- {item}")
    lines.extend(["", "## Evidence Completeness Checklist"])
    for item in payload["evidence_completeness_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Risk Disclosure Checklist"])
    for item in payload["risk_disclosure_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Traceability Matrix"])
    for row in payload["traceability_matrix"]:
        lines.append(f"- {row['evidence_key']}: {row['evidence_label']}")
    return "\n".join(lines)
