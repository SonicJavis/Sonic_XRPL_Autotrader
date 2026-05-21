from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.models import (
    XamanGovernanceClosureResponseEvidencePackReviewDigestReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.traceability import render_traceability_map


def render_xaman_governance_closure_response_evidence_pack_review_digest_payload(
    report: XamanGovernanceClosureResponseEvidencePackReviewDigestReport,
) -> dict:
    flags = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "phase": report.spec.phase,
        "review_digest_bundle_id": report.spec.review_digest_bundle_id,
        "source_phase88_evidence_pack_bundle_id": report.spec.source_phase88_evidence_pack_bundle_id,
        "source_closure_response_resolution_register_id": report.spec.source_closure_response_resolution_register_id,
        "deterministic_timestamp": report.spec.deterministic_timestamp,
        "final_review_digest_classification": report.final_review_digest_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": flags.spec_only,
        "closure_response_evidence_pack_review_digest_spec_only": flags.closure_response_evidence_pack_review_digest_spec_only,
        "runtime_evidence_pack_review_digest_service_allowed": flags.runtime_evidence_pack_review_digest_service_allowed,
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


def render_xaman_governance_closure_response_evidence_pack_review_digest_json(report: XamanGovernanceClosureResponseEvidencePackReviewDigestReport) -> str:
    return json.dumps(render_xaman_governance_closure_response_evidence_pack_review_digest_payload(report), indent=2, sort_keys=True)


def render_xaman_governance_closure_response_evidence_pack_review_digest_markdown(report: XamanGovernanceClosureResponseEvidencePackReviewDigestReport) -> str:
    payload = render_xaman_governance_closure_response_evidence_pack_review_digest_payload(report)
    lines = [
        "# Phase 89 Xaman Governance Closure Response Evidence Pack Review Digest Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Review digest bundle ID: `{payload['review_digest_bundle_id']}`",
        f"- Source Phase 88 evidence-pack bundle ID: `{payload['source_phase88_evidence_pack_bundle_id']}`",
        f"- Final review digest classification: `{payload['final_review_digest_classification']}`",
        f"- spec_only: `{payload['spec_only']}`",
        f"- closure_response_evidence_pack_review_digest_spec_only: `{payload['closure_response_evidence_pack_review_digest_spec_only']}`",
        f"- runtime_evidence_pack_review_digest_service_allowed: `{payload['runtime_evidence_pack_review_digest_service_allowed']}`",
        "",
        "## Validation Errors",
    ]
    lines += [f"- {item}" for item in (payload["validation_errors"] or ["none"])]
    lines += ["", "## Review Digest Domains"]
    lines += [f"- {domain}" for domain in payload["spec"]["review_digest_domains"]]
    lines += ["", "## Review Digest Sections"]
    lines += [
        f"- `{section['digest_section_id']}` / `{section['digest_domain']}` / `{section['digest_status']}` / evidence `{section['evidence_count']}`"
        for section in payload["spec"]["review_digest_sections"]
    ]
    lines += ["", "## Review Digest Findings"]
    lines += [
        f"- `{finding['finding_id']}` / `{finding['category']}` / `{finding['severity']}`"
        for finding in (payload["spec"]["review_digest_findings"] or [])
    ] or ["- none"]
    lines += ["", "## Review Digest Limitation Register"]
    lines += [
        f"- `{limitation['limitation_id']}` / `{limitation['category']}` / `{limitation['severity']}`"
        for limitation in (payload["spec"]["review_digest_limitation_register"] or [])
    ] or ["- none"]
    lines += ["", "## Cross-Phase Review Digest Traceability Map"]
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
        "- Still no runtime evidence-pack review digest service.",
        "- Still no download service.",
        "- Still no API/UI evidence-pack digest route.",
        "- Still no safety bypass.",
    ]
    return "\n".join(lines)


def write_xaman_governance_closure_response_evidence_pack_review_digest_reports(
    report: XamanGovernanceClosureResponseEvidencePackReviewDigestReport,
    output_dir: str | Path = "reports/phase89",
) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "latest_xaman_governance_closure_response_evidence_pack_review_digest_spec.json"
    markdown_path = out / "latest_xaman_governance_closure_response_evidence_pack_review_digest_spec.md"
    json_path.write_text(render_xaman_governance_closure_response_evidence_pack_review_digest_json(report), encoding="utf-8")
    markdown_path.write_text(render_xaman_governance_closure_response_evidence_pack_review_digest_markdown(report), encoding="utf-8")
    return json_path, markdown_path
