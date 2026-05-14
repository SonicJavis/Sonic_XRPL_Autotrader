from __future__ import annotations

from sonic_xrpl.xaman_audit_idempotency_spec.models import XamanAuditIdempotencySpecReport


def render_phase64_audit_checklist(report: XamanAuditIdempotencySpecReport) -> list[str]:
    return [
        "event_type_enum_required",
        "correlation_id_required",
        "callback_event_id_required",
        "payload_uuid_binding_required",
        "candidate_binding_required",
        "paper_simulation_binding_required",
        "operator_approval_binding_required",
        "append_only_required",
        "tamper_evidence_required",
        "retention_policy_required",
        "redaction_policy_required",
        "sensitive_material_exclusion_required",
        "cancellation_rejection_policy_required",
    ]
