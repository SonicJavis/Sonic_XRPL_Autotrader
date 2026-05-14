from __future__ import annotations

import json

from sonic_xrpl.xaman_testnet_payload_spec.models import XamanTestnetSpecReport, jsonable


def render_xaman_testnet_payload_spec_payload(report: XamanTestnetSpecReport) -> dict[str, object]:
    return {
        "fixture_id": report.fixture_id,
        "valid_design_spec": report.valid_design_spec,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "design_spec_only": report.spec.safety_flags.design_spec_only,
        "manual_approval_required": report.spec.safety_flags.manual_approval_required,
        "payload_creation_allowed": report.spec.safety_flags.payload_creation_allowed,
        "xaman_api_calls_allowed": report.spec.safety_flags.xaman_api_calls_allowed,
        "signing_allowed": report.spec.safety_flags.signing_allowed,
        "submission_allowed": report.spec.safety_flags.submission_allowed,
        "autofill_allowed": report.spec.safety_flags.autofill_allowed,
        "wallet_material_allowed": report.spec.safety_flags.wallet_material_allowed,
        "live_execution_allowed": report.spec.safety_flags.live_execution_allowed,
        "runtime_mutation_allowed": report.spec.safety_flags.runtime_mutation_allowed,
        "spec": jsonable(report.spec),
        "verification_checklist": [
            "callback_signature_required",
            "callback_replay_cache_required",
            "account_txn_id_required",
            "pre_submit_verification_required",
            "post_submit_verification_required",
            "testnet_only_gate_required",
            "mainnet_blocked",
        ],
    }


def render_xaman_testnet_payload_spec_json(report: XamanTestnetSpecReport) -> str:
    return json.dumps(render_xaman_testnet_payload_spec_payload(report), indent=2, sort_keys=True)


def render_xaman_testnet_payload_spec_markdown(report: XamanTestnetSpecReport) -> str:
    payload = render_xaman_testnet_payload_spec_payload(report)
    lines = [
        "# Phase 62 Xaman Testnet Payload Schema Review",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- valid_design_spec: `{payload['valid_design_spec']}`",
        f"- design_spec_only: `{payload['design_spec_only']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- xaman_api_calls_allowed: `{payload['xaman_api_calls_allowed']}`",
        f"- signing_allowed: `{payload['signing_allowed']}`",
        f"- submission_allowed: `{payload['submission_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    errors = payload["validation_errors"] or ["none"]
    for item in errors:
        lines.append(f"- {item}")
    lines.extend(["", "## Gate Checklist"])
    for item in payload["verification_checklist"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
