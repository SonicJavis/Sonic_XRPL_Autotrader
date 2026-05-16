from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_evidence_attestation_spec.models import (
    XamanGovernanceEvidenceAttestationReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_evidence_attestation_spec.traceability import (
    render_traceability_map,
)


def render_xaman_governance_evidence_attestation_payload(
    report: XamanGovernanceEvidenceAttestationReport,
) -> dict[str, object]:
    f = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "readiness_classification": report.readiness_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": f.spec_only,
        "attestation_only": f.attestation_only,
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


def render_xaman_governance_evidence_attestation_json(
    report: XamanGovernanceEvidenceAttestationReport,
) -> str:
    return json.dumps(
        render_xaman_governance_evidence_attestation_payload(report),
        indent=2,
        sort_keys=True,
    )


def render_xaman_governance_evidence_attestation_markdown(
    report: XamanGovernanceEvidenceAttestationReport,
) -> str:
    payload = render_xaman_governance_evidence_attestation_payload(report)
    lines = [
        "# Phase 71 Xaman Governance Evidence Integrity + Attestation Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Readiness classification: `{payload['readiness_classification']}`",
        f"- spec_only: `{payload['spec_only']}`",
        f"- attestation_only: `{payload['attestation_only']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- xaman_payload_creation_allowed: `{payload['xaman_payload_creation_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in payload["validation_errors"] or ["none"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Final Confirmation", "- Still no live execution.", "- Still no testnet execution.", "- Still no Xaman payload creation."])
    return "\n".join(lines)


def write_xaman_governance_evidence_attestation_reports(
    report: XamanGovernanceEvidenceAttestationReport,
    output_dir: str | Path = "reports/phase71",
) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "latest_xaman_governance_evidence_attestation_spec.json"
    md_path = output_path / "latest_xaman_governance_evidence_attestation_spec.md"
    json_path.write_text(render_xaman_governance_evidence_attestation_json(report), encoding="utf-8")
    md_path.write_text(render_xaman_governance_evidence_attestation_markdown(report), encoding="utf-8")
    return json_path, md_path
