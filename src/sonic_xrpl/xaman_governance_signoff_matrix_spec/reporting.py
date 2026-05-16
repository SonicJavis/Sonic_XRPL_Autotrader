from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_signoff_matrix_spec.models import (
    XamanGovernanceSignoffReport,
    jsonable,
)
from sonic_xrpl.xaman_governance_signoff_matrix_spec.traceability import (
    render_traceability_matrix,
)


def render_xaman_governance_signoff_matrix_payload(
    report: XamanGovernanceSignoffReport,
) -> dict[str, object]:
    f = report.spec.safety_flags
    return {
        "fixture_id": report.fixture_id,
        "readiness_classification": report.readiness_classification,
        "validation_errors": list(report.validation_errors),
        "blockers": list(report.blockers),
        "spec_only": f.spec_only,
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
        "traceability_matrix": render_traceability_matrix(report),
        "spec": jsonable(report.spec),
    }


def render_xaman_governance_signoff_matrix_json(
    report: XamanGovernanceSignoffReport,
) -> str:
    return json.dumps(
        render_xaman_governance_signoff_matrix_payload(report),
        indent=2,
        sort_keys=True,
    )


def render_xaman_governance_signoff_matrix_markdown(
    report: XamanGovernanceSignoffReport,
) -> str:
    payload = render_xaman_governance_signoff_matrix_payload(report)
    lines = [
        "# Phase 70 Xaman Testnet Governance Sign-Off Matrix Spec",
        "",
        f"- Fixture: `{payload['fixture_id']}`",
        f"- Readiness classification: `{payload['readiness_classification']}`",
        f"- spec_only: `{payload['spec_only']}`",
        f"- testnet_execution_allowed: `{payload['testnet_execution_allowed']}`",
        f"- xaman_payload_creation_allowed: `{payload['xaman_payload_creation_allowed']}`",
        f"- live_execution_allowed: `{payload['live_execution_allowed']}`",
        "",
        "## Validation Errors",
    ]
    for item in payload["validation_errors"] or ["none"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Governance Roles"])
    for role in report.spec.signoff_roles:
        lines.append(f"- {role}")
    lines.extend(["", "## Sign-Off Domains"])
    for domain in report.spec.signoff_domains:
        lines.append(f"- {domain}")
    lines.extend(["", "## Final Confirmation", "- Still no live execution.", "- Still no testnet execution.", "- Still no Xaman payload creation."])
    return "\n".join(lines)


def write_xaman_governance_signoff_matrix_reports(
    report: XamanGovernanceSignoffReport,
    output_dir: str | Path = "reports/phase70",
) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "latest_xaman_governance_signoff_matrix_spec.json"
    md_path = output_path / "latest_xaman_governance_signoff_matrix_spec.md"
    json_path.write_text(render_xaman_governance_signoff_matrix_json(report), encoding="utf-8")
    md_path.write_text(render_xaman_governance_signoff_matrix_markdown(report), encoding="utf-8")
    return json_path, md_path
