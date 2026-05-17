from __future__ import annotations

from sonic_xrpl.xaman_governance_exception_waiver_register_spec.models import (
    XamanGovernanceExceptionWaiverRegisterReport,
)


def render_traceability_map(report: XamanGovernanceExceptionWaiverRegisterReport) -> dict[str, list[dict[str, str]]]:
    waiver_links = [
        {
            "waiver_id": item.waiver_id,
            "phase70_signoff_domain": item.related_phase70_signoff_domain,
            "phase71_attestation_id": item.related_phase71_attestation_id,
            "phase72_workflow_step_id": item.related_phase72_workflow_step_id,
            "phase73_sla_escalation_id": item.related_phase73_sla_escalation_id,
            "waiver_domain": item.waiver_domain,
            "status": item.current_status,
        }
        for item in report.spec.waiver_records
    ]
    blocker_links = [
        {"blocker": blocker, "unsafe_category": blocker.split(":", 1)[0].upper()}
        for blocker in report.blockers
    ]
    status_links = [
        {
            "waiver_id": item.waiver_id,
            "status": item.current_status,
            "limitation_notes": item.limitation_notes,
            "required_evidence_ids": ",".join(item.required_evidence_ids),
        }
        for item in report.spec.waiver_records
    ]
    return {
        "waiver_links": waiver_links,
        "blocker_links": blocker_links,
        "status_links": status_links,
    }
