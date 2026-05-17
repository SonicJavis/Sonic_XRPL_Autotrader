from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_exception_waiver_register_spec.models import (
    XamanGovernanceExceptionWaiverRegisterReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_exception_waiver_register_spec.traceability import render_traceability_map


def render_xaman_governance_exception_waiver_register_payload(
    report: XamanGovernanceExceptionWaiverRegisterReport,
) -> dict[str, object]:
    f = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "phase": report.spec.phase,
        "waiver_register_id": report.spec.waiver_register_id,
        "deterministic_timestamp": report.spec.deterministic_timestamp,
        "readiness_classification": report.readiness_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "limitations": list(report.spec.limitations),
        "spec_only": f.spec_only,
        "waiver_register_spec_only": f.waiver_register_spec_only,
        "runtime_waiver_service_allowed": f.runtime_waiver_service_allowed,
        "safety_bypass_allowed": f.safety_bypass_allowed,
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


def render_xaman_governance_exception_waiver_register_json(
    report: XamanGovernanceExceptionWaiverRegisterReport,
) -> str:
    return json.dumps(render_xaman_governance_exception_waiver_register_payload(report), indent=2, sort_keys=True)


def render_xaman_governance_exception_waiver_register_markdown(
    report: XamanGovernanceExceptionWaiverRegisterReport,
) -> str:
    p = render_xaman_governance_exception_waiver_register_payload(report)
    lines = [
        "# Phase 74 Xaman Governance Exception Waiver Register Spec",
        "",
        f"- Fixture: `{p['fixture_id']}`",
        f"- Waiver register ID: `{p['waiver_register_id']}`",
        f"- Deterministic timestamp: `{p['deterministic_timestamp']}`",
        f"- Readiness classification: `{p['readiness_classification']}`",
        f"- spec_only: `{p['spec_only']}`",
        f"- waiver_register_spec_only: `{p['waiver_register_spec_only']}`",
        f"- runtime_waiver_service_allowed: `{p['runtime_waiver_service_allowed']}`",
        f"- safety_bypass_allowed: `{p['safety_bypass_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in p["validation_errors"] or ["none"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Final Confirmation",
        "- Still no live execution.",
        "- Still no testnet execution.",
        "- Still no Xaman payload creation.",
        "- Still no runtime waiver service.",
        "- Still no safety bypass.",
    ])
    return "\n".join(lines)


def write_xaman_governance_exception_waiver_register_reports(
    report: XamanGovernanceExceptionWaiverRegisterReport,
    output_dir: str | Path = "reports/phase74",
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "latest_xaman_governance_exception_waiver_register_spec.json"
    m = out / "latest_xaman_governance_exception_waiver_register_spec.md"
    j.write_text(render_xaman_governance_exception_waiver_register_json(report), encoding="utf-8")
    m.write_text(render_xaman_governance_exception_waiver_register_markdown(report), encoding="utf-8")
    return j, m
