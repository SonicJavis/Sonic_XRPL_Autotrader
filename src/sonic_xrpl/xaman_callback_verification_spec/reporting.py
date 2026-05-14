from __future__ import annotations

import json

from sonic_xrpl.xaman_callback_verification_spec.models import XamanCallbackVerificationSpecReport, jsonable
from sonic_xrpl.xaman_callback_verification_spec.threat_model import (
    render_phase63_blocker_register,
    render_phase63_threat_model,
)


def render_xaman_callback_verification_spec_payload(report: XamanCallbackVerificationSpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "valid_design_spec": report.valid_design_spec,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "callback_spec_only": report.spec.safety_flags.callback_spec_only,
        "verification_design_only": report.spec.safety_flags.verification_design_only,
        "runtime_callback_handler_allowed": report.spec.safety_flags.runtime_callback_handler_allowed,
        "webhook_runtime_allowed": report.spec.safety_flags.webhook_runtime_allowed,
        "payload_creation_allowed": report.spec.safety_flags.payload_creation_allowed,
        "xaman_api_calls_allowed": report.spec.safety_flags.xaman_api_calls_allowed,
        "signing_allowed": report.spec.safety_flags.signing_allowed,
        "submission_allowed": report.spec.safety_flags.submission_allowed,
        "autofill_allowed": report.spec.safety_flags.autofill_allowed,
        "wallet_material_allowed": report.spec.safety_flags.wallet_material_allowed,
        "testnet_execution_allowed": report.spec.safety_flags.testnet_execution_allowed,
        "live_execution_allowed": report.spec.safety_flags.live_execution_allowed,
        "runtime_mutation_allowed": report.spec.safety_flags.runtime_mutation_allowed,
        "spec": jsonable(report.spec),
        "callback_verification_checklist": [
            "authenticity_requirement",
            "correlation_binding",
            "nonce_ttl_replay_requirements",
            "idempotency_requirement",
            "duplicate_callback_handling",
            "cancellation_rejection_handling",
            "audit_trail_requirement",
            "operator_consent_linkage",
            "testnet_gate_checklist",
            "live_execution_blockers",
        ],
        "threat_model": render_phase63_threat_model(report),
        "blocker_register": render_phase63_blocker_register(report),
    }


def render_xaman_callback_verification_spec_json(report: XamanCallbackVerificationSpecReport) -> str:
    return json.dumps(render_xaman_callback_verification_spec_payload(report), indent=2, sort_keys=True)


def render_xaman_callback_verification_spec_markdown(report: XamanCallbackVerificationSpecReport) -> str:
    payload = render_xaman_callback_verification_spec_payload(report)
    lines = [
        "# Phase 63 Xaman Callback Verification Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- valid_design_spec: `{payload['valid_design_spec']}`",
        f"- callback_spec_only: `{payload['callback_spec_only']}`",
        f"- runtime_callback_handler_allowed: `{payload['runtime_callback_handler_allowed']}`",
        f"- webhook_runtime_allowed: `{payload['webhook_runtime_allowed']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- xaman_api_calls_allowed: `{payload['xaman_api_calls_allowed']}`",
        f"- signing_allowed: `{payload['signing_allowed']}`",
        f"- submission_allowed: `{payload['submission_allowed']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    errors = payload["validation_errors"] or ["none"]
    for item in errors:
        lines.append(f"- {item}")
    lines.extend(["", "## Callback Verification Checklist"])
    for item in payload["callback_verification_checklist"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
