from __future__ import annotations

import json

from sonic_xrpl.xaman_manual_approval_spec.models import XamanSpecReport, jsonable
from sonic_xrpl.xaman_manual_approval_spec.threat_model import build_threat_model


def render_manual_approval_spec_payload(report: XamanSpecReport) -> dict[str, object]:
    threat = build_threat_model(report)
    return {
        "fixture_id": report.fixture_id,
        "design_spec_only": report.spec.safety_flags.design_spec_only,
        "manual_approval_required": report.spec.safety_flags.manual_approval_required,
        "payload_creation_allowed": report.spec.safety_flags.payload_creation_allowed,
        "signing_allowed": report.spec.safety_flags.signing_allowed,
        "submission_allowed": report.spec.safety_flags.submission_allowed,
        "autofill_allowed": report.spec.safety_flags.autofill_allowed,
        "wallet_material_allowed": report.spec.safety_flags.wallet_material_allowed,
        "live_execution_allowed": report.spec.safety_flags.live_execution_allowed,
        "runtime_mutation_allowed": report.spec.safety_flags.runtime_mutation_allowed,
        "valid_design_spec": report.valid_design_spec,
        "validation_errors": list(report.validation_errors),
        "blocked_actions": list(report.blocked_actions),
        "spec": jsonable(report.spec),
        "threat_model": jsonable(threat),
    }


def render_manual_approval_spec_markdown(report: XamanSpecReport) -> str:
    payload = render_manual_approval_spec_payload(report)
    lines = [
        "# Phase 61 Xaman Manual Approval Design Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Valid design spec: `{payload['valid_design_spec']}`",
        f"- design_spec_only: `{payload['design_spec_only']}`",
        f"- payload_creation_allowed: `{payload['payload_creation_allowed']}`",
        f"- signing_allowed: `{payload['signing_allowed']}`",
        f"- submission_allowed: `{payload['submission_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    errors = payload["validation_errors"] or ["none"]
    for item in errors:
        lines.append(f"- {item}")

    lines.extend(["", "## Future Gates", "- testnet_implementation_allowed: `False`", "- mainnet_live_allowed: `False`"])
    return "\n".join(lines)


def render_manual_approval_spec_json(report: XamanSpecReport) -> str:
    return json.dumps(render_manual_approval_spec_payload(report), indent=2, sort_keys=True)
