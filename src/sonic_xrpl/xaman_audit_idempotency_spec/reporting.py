from __future__ import annotations

import json

from sonic_xrpl.xaman_audit_idempotency_spec.audit_trail import render_phase64_audit_checklist
from sonic_xrpl.xaman_audit_idempotency_spec.idempotency import render_phase64_idempotency_checklist
from sonic_xrpl.xaman_audit_idempotency_spec.models import XamanAuditIdempotencySpecReport, jsonable


def render_xaman_audit_idempotency_spec_payload(report: XamanAuditIdempotencySpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "outcome": report.outcome,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "audit_spec_only": report.spec.safety_flags.audit_spec_only,
        "idempotency_spec_only": report.spec.safety_flags.idempotency_spec_only,
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
        "spec": jsonable(report.spec),
        "idempotency_checklist": render_phase64_idempotency_checklist(report),
        "audit_trail_checklist": render_phase64_audit_checklist(report),
    }


def render_xaman_audit_idempotency_spec_json(report: XamanAuditIdempotencySpecReport) -> str:
    return json.dumps(render_xaman_audit_idempotency_spec_payload(report), indent=2, sort_keys=True)


def render_xaman_audit_idempotency_spec_markdown(report: XamanAuditIdempotencySpecReport) -> str:
    payload = render_xaman_audit_idempotency_spec_payload(report)
    lines = [
        "# Phase 64 Xaman Audit Idempotency Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- outcome: `{payload['outcome']}`",
        f"- audit_spec_only: `{payload['audit_spec_only']}`",
        f"- idempotency_spec_only: `{payload['idempotency_spec_only']}`",
        f"- persistence_implementation_allowed: `{payload['persistence_implementation_allowed']}`",
        f"- database_writes_allowed: `{payload['database_writes_allowed']}`",
        f"- callback_handler_allowed: `{payload['callback_handler_allowed']}`",
        f"- webhook_runtime_allowed: `{payload['webhook_runtime_allowed']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- xaman_api_calls_allowed: `{payload['xaman_api_calls_allowed']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    errors = payload["validation_errors"] or ["none"]
    for item in errors:
        lines.append(f"- {item}")
    lines.extend(["", "## Idempotency Checklist"])
    for item in payload["idempotency_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Audit Trail Checklist"])
    for item in payload["audit_trail_checklist"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
