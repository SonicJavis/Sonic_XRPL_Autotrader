from __future__ import annotations

from sonic_xrpl.xaman_callback_verification_spec.models import XamanCallbackVerificationSpecReport


def render_phase63_threat_model(report: XamanCallbackVerificationSpecReport) -> dict[str, object]:
    return {
        "phase": "63",
        "scope": "callback-authenticity-and-replay-verification-design-only",
        "assets": [
            "callback_integrity",
            "operator_consent_binding",
            "audit_trail_completeness",
            "idempotency_state",
        ],
        "threats": [
            "forged_callback_body",
            "signature_header_spoof",
            "nonce_replay",
            "stale_callback_replay",
            "duplicate_callback_processing",
            "out_of_order_callback_processing",
            "consent_linkage_bypass",
            "audit_gap_or_tampering",
        ],
        "required_controls": [
            "signature/authenticity verification",
            "nonce + ttl verification",
            "replay window enforcement",
            "idempotency key check",
            "duplicate callback suppression",
            "ordered callback state transitions",
            "candidate/paper-simulation/correlation binding",
            "immutable audit trail",
            "manual approval linkage",
        ],
        "blockers": [b.blocker_id for b in report.spec.blockers],
        "design_only": True,
        "runtime_callback_handler_allowed": False,
        "webhook_runtime_allowed": False,
        "testnet_execution_allowed": False,
        "live_execution_allowed": False,
    }


def render_phase63_blocker_register(report: XamanCallbackVerificationSpecReport) -> list[dict[str, object]]:
    rows = []
    for blocker in report.spec.blockers:
        rows.append(
            {
                "blocker_id": blocker.blocker_id,
                "severity": blocker.severity,
                "title": blocker.title,
                "detail": blocker.detail,
                "required_before_callback_runtime": blocker.required_before_callback_runtime,
                "required_before_testnet_impl": blocker.required_before_testnet_impl,
                "required_before_mainnet_impl": blocker.required_before_mainnet_impl,
            }
        )
    return rows
