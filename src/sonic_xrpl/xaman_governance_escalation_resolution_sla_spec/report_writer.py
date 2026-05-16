from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.models import (
    XamanGovernanceEscalationResolutionSLAReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.traceability import (
    render_traceability_map,
)


def render_xaman_governance_escalation_resolution_sla_payload(
    report: XamanGovernanceEscalationResolutionSLAReport,
) -> dict[str, object]:
    f = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "readiness_classification": report.readiness_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": f.spec_only,
        "sla_spec_only": f.sla_spec_only,
        "runtime_sla_engine_allowed": f.runtime_sla_engine_allowed,
        "scheduler_allowed": f.scheduler_allowed,
        "notification_allowed": f.notification_allowed,
        "testnet_execution_allowed": f.testnet_execution_allowed,
        "xaman_payload_creation_allowed": f.xaman_payload_creation_allowed,
        "xaman_api_calls_allowed": f.xaman_api_calls_allowed,
        "xaman_sdk_dependency_allowed": f.xaman_sdk_dependency_allowed,
        "signing_allowed": f.signing_allowed,
        "submission_allowed": f.submission_allowed,
        "autofill_allowed": f.autofill_allowed,
        "wallet_material_allowed": f.wallet_material_allowed,
        "live_execution_allowed": f.live_execution_allowed,
        "runtime_mutation_allowed": f.runtime_mutation_allowed,
        "traceability_map": render_traceability_map(report),
        "spec": jsonable(report.spec),
    }


def render_xaman_governance_escalation_resolution_sla_json(
    report: XamanGovernanceEscalationResolutionSLAReport,
) -> str:
    return json.dumps(
        render_xaman_governance_escalation_resolution_sla_payload(report),
        indent=2,
        sort_keys=True,
    )


def render_xaman_governance_escalation_resolution_sla_markdown(
    report: XamanGovernanceEscalationResolutionSLAReport,
) -> str:
    p = render_xaman_governance_escalation_resolution_sla_payload(report)
    lines = [
        "# Phase 73 Xaman Governance Escalation Resolution SLA Spec",
        "",
        f"- Fixture: `{p['fixture_id']}`",
        f"- Readiness classification: `{p['readiness_classification']}`",
        f"- spec_only: `{p['spec_only']}`",
        f"- sla_spec_only: `{p['sla_spec_only']}`",
        f"- runtime_sla_engine_allowed: `{p['runtime_sla_engine_allowed']}`",
        f"- scheduler_allowed: `{p['scheduler_allowed']}`",
        f"- notification_allowed: `{p['notification_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in p["validation_errors"] or ["none"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Final Confirmation",
            "- Still no live execution.",
            "- Still no testnet execution.",
            "- Still no Xaman payload creation.",
            "- Still no runtime SLA engine.",
            "- Still no scheduler.",
            "- Still no notifications.",
        ]
    )
    return "\n".join(lines)


def write_xaman_governance_escalation_resolution_sla_reports(
    report: XamanGovernanceEscalationResolutionSLAReport,
    output_dir: str | Path = "reports/phase73",
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "latest_xaman_governance_escalation_resolution_sla_spec.json"
    m = out / "latest_xaman_governance_escalation_resolution_sla_spec.md"
    j.write_text(render_xaman_governance_escalation_resolution_sla_json(report), encoding="utf-8")
    m.write_text(render_xaman_governance_escalation_resolution_sla_markdown(report), encoding="utf-8")
    return j, m
