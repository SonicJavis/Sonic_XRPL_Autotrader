from __future__ import annotations

import json

from sonic_xrpl.xaman_operator_consent_ux_spec.models import XamanOperatorConsentUxSpecReport, jsonable


def render_xaman_operator_consent_ux_payload(report: XamanOperatorConsentUxSpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "outcome": report.outcome,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "ux_contract_spec_only": report.spec.safety_flags.ux_contract_spec_only,
        "ui_implementation_allowed": report.spec.safety_flags.ui_implementation_allowed,
        "api_route_allowed": report.spec.safety_flags.api_route_allowed,
        "runtime_consent_service_allowed": report.spec.safety_flags.runtime_consent_service_allowed,
        "persistence_implementation_allowed": report.spec.safety_flags.persistence_implementation_allowed,
        "database_writes_allowed": report.spec.safety_flags.database_writes_allowed,
        "callback_handler_allowed": report.spec.safety_flags.callback_handler_allowed,
        "webhook_runtime_allowed": report.spec.safety_flags.webhook_runtime_allowed,
        "payload_creation_allowed": report.spec.safety_flags.payload_creation_allowed,
        "xaman_api_calls_allowed": report.spec.safety_flags.xaman_api_calls_allowed,
        "signing_allowed": report.spec.safety_flags.signing_allowed,
        "submission_allowed": report.spec.safety_flags.submission_allowed,
        "wallet_material_allowed": report.spec.safety_flags.wallet_material_allowed,
        "testnet_execution_allowed": report.spec.safety_flags.testnet_execution_allowed,
        "live_execution_allowed": report.spec.safety_flags.live_execution_allowed,
        "required_disclosure_checklist": [item.requirement_id for item in report.spec.disclosures if item.required],
        "acknowledgement_checklist": list(report.spec.acknowledgement_requirements),
        "rejection_cancellation_checklist": list(report.spec.rejection_cancellation_requirements),
        "operator_audit_binding_checklist": list(report.spec.operator_audit_binding_requirements),
        "spec": jsonable(report.spec),
    }


def render_xaman_operator_consent_ux_json(report: XamanOperatorConsentUxSpecReport) -> str:
    return json.dumps(render_xaman_operator_consent_ux_payload(report), indent=2, sort_keys=True)


def render_xaman_operator_consent_ux_markdown(report: XamanOperatorConsentUxSpecReport) -> str:
    payload = render_xaman_operator_consent_ux_payload(report)
    lines = [
        "# Phase 66 Xaman Operator Consent UX Contract Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Outcome: `{payload['outcome']}`",
        f"- ux_contract_spec_only: `{payload['ux_contract_spec_only']}`",
        f"- ui_implementation_allowed: `{payload['ui_implementation_allowed']}`",
        f"- api_route_allowed: `{payload['api_route_allowed']}`",
        f"- runtime_consent_service_allowed: `{payload['runtime_consent_service_allowed']}`",
        f"- persistence_implementation_allowed: `{payload['persistence_implementation_allowed']}`",
        f"- database_writes_allowed: `{payload['database_writes_allowed']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- xaman_api_calls_allowed: `{payload['xaman_api_calls_allowed']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in (payload["validation_errors"] or ["none"]):
        lines.append(f"- {item}")
    lines.extend(["", "## Required Disclosure Checklist"])
    for item in payload["required_disclosure_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Acknowledgement Checklist"])
    for item in payload["acknowledgement_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Rejection/Cancellation Checklist"])
    for item in payload["rejection_cancellation_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Operator Audit-Binding Checklist"])
    for item in payload["operator_audit_binding_checklist"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
