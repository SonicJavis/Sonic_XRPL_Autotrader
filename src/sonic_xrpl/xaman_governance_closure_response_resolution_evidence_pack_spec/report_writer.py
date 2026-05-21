from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.models import (
    XamanGovernanceClosureResponseResolutionEvidencePackReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.traceability import render_traceability_map


def render_xaman_governance_closure_response_resolution_evidence_pack_payload(
    report: XamanGovernanceClosureResponseResolutionEvidencePackReport,
) -> dict:
    flags = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "phase": report.spec.phase,
        "evidence_pack_bundle_id": report.spec.evidence_pack_bundle_id,
        "source_closure_response_resolution_register_id": report.spec.source_closure_response_resolution_register_id,
        "source_closure_digest_response_bundle_id": report.spec.source_closure_digest_response_bundle_id,
        "deterministic_timestamp": report.spec.deterministic_timestamp,
        "final_evidence_pack_classification": report.final_evidence_pack_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": flags.spec_only,
        "closure_response_resolution_evidence_pack_spec_only": flags.closure_response_resolution_evidence_pack_spec_only,
        "runtime_closure_response_resolution_evidence_pack_service_allowed": flags.runtime_closure_response_resolution_evidence_pack_service_allowed,
        "download_service_allowed": flags.download_service_allowed,
        "api_route_allowed": flags.api_route_allowed,
        "dashboard_ui_allowed": flags.dashboard_ui_allowed,
        "safety_bypass_allowed": flags.safety_bypass_allowed,
        "testnet_execution_allowed": flags.testnet_execution_allowed,
        "xaman_payload_creation_allowed": flags.xaman_payload_creation_allowed,
        "xaman_api_calls_allowed": flags.xaman_api_calls_allowed,
        "xaman_sdk_dependency_allowed": flags.xaman_sdk_dependency_allowed,
        "signing_allowed": flags.signing_allowed,
        "submission_allowed": flags.submission_allowed,
        "autofill_allowed": flags.autofill_allowed,
        "wallet_material_allowed": flags.wallet_material_allowed,
        "live_execution_allowed": flags.live_execution_allowed,
        "runtime_mutation_allowed": flags.runtime_mutation_allowed,
        "traceability_map": render_traceability_map(report),
        "spec": jsonable(report.spec),
    }


def render_xaman_governance_closure_response_resolution_evidence_pack_json(report: XamanGovernanceClosureResponseResolutionEvidencePackReport) -> str:
    return json.dumps(render_xaman_governance_closure_response_resolution_evidence_pack_payload(report), indent=2, sort_keys=True)


def render_xaman_governance_closure_response_resolution_evidence_pack_markdown(report: XamanGovernanceClosureResponseResolutionEvidencePackReport) -> str:
    payload = render_xaman_governance_closure_response_resolution_evidence_pack_payload(report)
    lines = [
        "# Phase 88 Xaman Governance Closure Response Resolution Evidence Pack Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Evidence pack bundle ID: `{payload['evidence_pack_bundle_id']}`",
        f"- Source closure response resolution register ID: `{payload['source_closure_response_resolution_register_id']}`",
        f"- Final evidence-pack classification: `{payload['final_evidence_pack_classification']}`",
        f"- spec_only: `{payload['spec_only']}`",
        f"- closure_response_resolution_evidence_pack_spec_only: `{payload['closure_response_resolution_evidence_pack_spec_only']}`",
        f"- runtime_closure_response_resolution_evidence_pack_service_allowed: `{payload['runtime_closure_response_resolution_evidence_pack_service_allowed']}`",
        "",
        "## Validation Errors",
    ]
    lines += [f"- {item}" for item in (payload["validation_errors"] or ["none"])]
    lines += ["", "## Evidence Pack Domains"]
    lines += [f"- {domain}" for domain in payload["spec"]["evidence_pack_domains"]]
    lines += ["", "## Evidence Pack Records"]
    lines += [
        f"- `{record['evidence_pack_id']}` / `{record['evidence_pack_domain']}` / `{record['evidence_completeness_status']}` / `{record['evidence_sufficiency_status']}`"
        for record in payload["spec"]["evidence_pack_records"]
    ]
    lines += ["", "## Evidence Pack Findings"]
    lines += [
        f"- `{finding['finding_id']}` / `{finding['category']}` / `{finding['severity']}`"
        for finding in (payload["spec"]["evidence_pack_findings"] or [])
    ] or ["- none"]
    lines += ["", "## Evidence Pack Limitation Register"]
    lines += [
        f"- `{limitation['limitation_id']}` / `{limitation['category']}` / `{limitation['severity']}`"
        for limitation in (payload["spec"]["evidence_pack_limitation_register"] or [])
    ] or ["- none"]
    lines += ["", "## Cross-Phase Evidence-Pack Traceability Map"]
    for key, value in payload["traceability_map"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Non-Authorization Confirmations"]
    lines += [f"- {notice}" for notice in payload["spec"]["non_authorization_notices"]]
    lines += [
        "",
        "## Final Confirmation",
        "- Still no live execution.",
        "- Still no testnet execution.",
        "- Still no Xaman payload creation.",
        "- Still no runtime closure response resolution evidence pack service.",
        "- Still no download service.",
        "- Still no API/UI evidence-pack route.",
        "- Still no safety bypass.",
    ]
    return "\n".join(lines)


def write_xaman_governance_closure_response_resolution_evidence_pack_reports(
    report: XamanGovernanceClosureResponseResolutionEvidencePackReport,
    output_dir: str | Path = "reports/phase88",
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "latest_xaman_governance_closure_response_resolution_evidence_pack_spec.json"
    markdown_path = out / "latest_xaman_governance_closure_response_resolution_evidence_pack_spec.md"
    json_path.write_text(render_xaman_governance_closure_response_resolution_evidence_pack_json(report), encoding="utf-8")
    markdown_path.write_text(render_xaman_governance_closure_response_resolution_evidence_pack_markdown(report), encoding="utf-8")
    return json_path, markdown_path
