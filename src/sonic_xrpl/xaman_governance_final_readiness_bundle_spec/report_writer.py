from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.models import XamanGovernanceFinalReadinessBundleReport, jsonable
from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.traceability import render_traceability_map


def render_xaman_governance_final_readiness_bundle_payload(report: XamanGovernanceFinalReadinessBundleReport) -> dict[str, object]:
    f = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "phase": report.spec.phase,
        "final_bundle_id": report.spec.final_bundle_id,
        "deterministic_timestamp": report.spec.deterministic_timestamp,
        "final_readiness_classification": report.final_readiness_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": f.spec_only,
        "final_readiness_bundle_spec_only": f.final_readiness_bundle_spec_only,
        "runtime_readiness_service_allowed": f.runtime_readiness_service_allowed,
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


def render_xaman_governance_final_readiness_bundle_json(report: XamanGovernanceFinalReadinessBundleReport) -> str:
    return json.dumps(render_xaman_governance_final_readiness_bundle_payload(report), indent=2, sort_keys=True)


def render_xaman_governance_final_readiness_bundle_markdown(report: XamanGovernanceFinalReadinessBundleReport) -> str:
    p = render_xaman_governance_final_readiness_bundle_payload(report)
    lines = [
        "# Phase 75 Xaman Governance Final Readiness Bundle Spec",
        "",
        f"- Fixture: `{p['fixture_id']}`",
        f"- Final bundle ID: `{p['final_bundle_id']}`",
        f"- Deterministic timestamp: `{p['deterministic_timestamp']}`",
        f"- Final readiness classification: `{p['final_readiness_classification']}`",
        f"- spec_only: `{p['spec_only']}`",
        f"- final_readiness_bundle_spec_only: `{p['final_readiness_bundle_spec_only']}`",
        f"- runtime_readiness_service_allowed: `{p['runtime_readiness_service_allowed']}`",
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
        "- Still no runtime readiness service.",
        "- Still no safety bypass.",
    ])
    return "\n".join(lines)


def write_xaman_governance_final_readiness_bundle_reports(report: XamanGovernanceFinalReadinessBundleReport, output_dir: str | Path = "reports/phase75") -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "latest_xaman_governance_final_readiness_bundle_spec.json"
    m = out / "latest_xaman_governance_final_readiness_bundle_spec.md"
    j.write_text(render_xaman_governance_final_readiness_bundle_json(report), encoding="utf-8")
    m.write_text(render_xaman_governance_final_readiness_bundle_markdown(report), encoding="utf-8")
    return j, m
