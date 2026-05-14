from __future__ import annotations

import json

from sonic_xrpl.xaman_approval_state_machine_spec.models import XamanApprovalStateMachineSpecReport, jsonable


def render_xaman_approval_state_machine_spec_payload(report: XamanApprovalStateMachineSpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "outcome": report.outcome,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "state_machine_spec_only": report.spec.safety_flags.state_machine_spec_only,
        "runtime_state_machine_allowed": report.spec.safety_flags.runtime_state_machine_allowed,
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
        "valid_transition_table": [
            f"{t.source_state}->{t.target_state}" for t in report.spec.transition_requirements
        ],
        "invalid_transition_table": [
            f"{t.source_state}->{t.target_state}" for t in report.spec.invalid_transition_rules
        ],
        "required_evidence_checklist": sorted(
            {item for t in report.spec.transition_requirements for item in t.required_evidence}
        ),
        "audit_idempotency_replay_checklist": [
            "required_audit_entry",
            "idempotency_required",
            "replay_ttl_required",
            "human_approval_required",
        ],
    }


def render_xaman_approval_state_machine_spec_json(report: XamanApprovalStateMachineSpecReport) -> str:
    return json.dumps(render_xaman_approval_state_machine_spec_payload(report), indent=2, sort_keys=True)


def render_xaman_approval_state_machine_spec_markdown(report: XamanApprovalStateMachineSpecReport) -> str:
    payload = render_xaman_approval_state_machine_spec_payload(report)
    lines = [
        "# Phase 65 Xaman Approval State Machine Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- outcome: `{payload['outcome']}`",
        f"- state_machine_spec_only: `{payload['state_machine_spec_only']}`",
        f"- runtime_state_machine_allowed: `{payload['runtime_state_machine_allowed']}`",
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
    for e in (payload["validation_errors"] or ["none"]):
        lines.append(f"- {e}")
    lines.extend(["", "## Valid Transitions"])
    for row in payload["valid_transition_table"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Invalid Transitions"])
    for row in payload["invalid_transition_table"]:
        lines.append(f"- {row}")
    return "\n".join(lines)
