from __future__ import annotations

from sonic_xrpl.xaman_dry_run_readiness_review_spec.models import (
    XamanDryRunReadinessSpecReport,
)


def render_traceability_matrix(
    report: XamanDryRunReadinessSpecReport,
) -> list[dict[str, str]]:
    return [
        {"requirement_key": item.key, "requirement_label": item.label}
        for item in report.spec.readiness_requirements
        if item.required
    ]
