from __future__ import annotations

from sonic_xrpl.xaman_audit_idempotency_spec.models import XamanAuditIdempotencySpecReport


def render_phase64_idempotency_checklist(report: XamanAuditIdempotencySpecReport) -> list[str]:
    return [
        "idempotency_key_rule_required",
        "idempotency_conflict_policy_required",
        "duplicate_callback_policy_required",
        "replay_attempt_policy_required",
        "stale_callback_policy_required",
        "ttl_seconds_required",
        f"ttl_bounds={report.spec.idempotency.ttl_min_seconds}-{report.spec.idempotency.ttl_max_seconds}",
    ]
