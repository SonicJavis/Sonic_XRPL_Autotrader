from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.runtime_profile.conformance import evaluate_runtime_profile_conformance
from sonic_xrpl.runtime_profile.models import RuntimeProfile, RuntimeProfileConformance, jsonable
from sonic_xrpl.runtime_profile.profiles import build_runtime_profile_snapshot


def _profile_markdown(profile: RuntimeProfile) -> str:
    warning_lines = [f"- {item}" for item in profile.warnings] if profile.warnings else ["- none"]
    limitation_lines = [f"- {item}" for item in profile.limitations] if profile.limitations else ["- none"]
    lines = [
        "# Phase 57 Runtime Profile",
        "",
        f"Profile ID: `{profile.profile_id}`",
        f"Profile: `{profile.profile_name}`",
        f"Created at: `{profile.created_at}`",
        "",
        "## Safety Statement",
        profile.safety_statement,
        "",
        "## Capabilities",
        f"- paper_only: `{profile.paper_only}`",
        f"- dry_run: `{profile.dry_run}`",
        f"- live_execution_allowed: `{profile.live_execution_allowed}`",
        f"- execution_enabled: `{profile.execution_enabled}`",
        f"- signing_allowed: `{profile.signing_allowed}`",
        f"- submission_allowed: `{profile.submission_allowed}`",
        f"- wallet_material_allowed: `{profile.wallet_material_allowed}`",
        f"- dashboard_mutation_allowed: `{profile.dashboard_mutation_allowed}`",
        f"- calibration_mutation_allowed: `{profile.calibration_mutation_allowed}`",
        "",
        "## Policies",
        f"- network_read_policy: `{profile.network_read_policy}`",
        f"- runtime_write_policy: `{profile.runtime_write_policy}`",
        "",
        "## Warnings",
        *warning_lines,
        "",
        "## Limitations",
        *limitation_lines,
        "",
    ]
    return "\n".join(lines) + "\n"


def _conformance_markdown(conformance: RuntimeProfileConformance) -> str:
    drift_lines = [f"- {item}" for item in conformance.drift_findings] if conformance.drift_findings else ["- none"]
    blocker_lines = [f"- {item}" for item in conformance.blockers] if conformance.blockers else ["- none"]
    warning_lines = [f"- {item}" for item in conformance.warnings] if conformance.warnings else ["- none"]
    lines = [
        "# Phase 57 Runtime Profile Conformance",
        "",
        f"Conformance ID: `{conformance.conformance_id}`",
        f"Profile: `{conformance.profile_name}`",
        f"Status: `{conformance.status}`",
        f"Created at: `{conformance.created_at}`",
        "",
        "## Checks",
        "| Check | Status | Message |",
        "|---|---|---|",
        *(
            f"| `{check.check_id}` | `{check.status}` | {check.message} |"
            for check in conformance.checks
        ),
        "",
        "## Drift Findings",
        *drift_lines,
        "",
        "## Blockers",
        *blocker_lines,
        "",
        "## Warnings",
        *warning_lines,
        "",
    ]
    return "\n".join(lines) + "\n"


def write_runtime_profile_reports(output_dir: str | Path = "reports/phase57") -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    profile = build_runtime_profile_snapshot()
    conformance = evaluate_runtime_profile_conformance()

    profile_json = target / "latest_runtime_profile.json"
    profile_md = target / "latest_runtime_profile.md"
    conformance_json = target / "latest_runtime_profile_conformance.json"
    conformance_md = target / "latest_runtime_profile_conformance.md"

    profile_json.write_text(json.dumps(jsonable(profile), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    profile_md.write_text(_profile_markdown(profile), encoding="utf-8")
    conformance_json.write_text(json.dumps(jsonable(conformance), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    conformance_md.write_text(_conformance_markdown(conformance), encoding="utf-8")

    return {
        "runtime_profile_json": str(profile_json),
        "runtime_profile_markdown": str(profile_md),
        "runtime_profile_conformance_json": str(conformance_json),
        "runtime_profile_conformance_markdown": str(conformance_md),
    }
