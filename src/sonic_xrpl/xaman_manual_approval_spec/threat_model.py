from __future__ import annotations

from dataclasses import dataclass

from sonic_xrpl.xaman_manual_approval_spec.models import XamanSpecReport


@dataclass(frozen=True)
class ThreatModelView:
    assets: tuple[str, ...]
    trust_boundaries: tuple[str, ...]
    abuse_paths: tuple[str, ...]
    controls_required: tuple[str, ...]


def build_threat_model(report: XamanSpecReport) -> ThreatModelView:
    abuse = [
        "payload_spoofing_without_user_consent",
        "callback_replay_without_nonce_ttl",
        "approval_state_tampering_without_immutable_audit",
        "attempted_auto_submission_without_explicit_phase_approval",
        "mainnet_execution_without_testnet_gate",
    ]
    if report.blocked_actions:
        abuse.extend(f"attempted_{item}" for item in report.blocked_actions)

    return ThreatModelView(
        assets=(
            "operator_consent_decision",
            "approval_intent_integrity",
            "audit_trail_integrity",
            "future_execution_boundary",
        ),
        trust_boundaries=(
            "paper_intelligence_to_human_review",
            "human_review_to_future_payload_layer",
            "future_payload_layer_to_future_submission_layer",
        ),
        abuse_paths=tuple(dict.fromkeys(abuse)),
        controls_required=(
            "explicit_yes_no_consent",
            "ttl_and_nonce_replay_protection",
            "immutable_audit_persistence",
            "manual_cancellation_path",
            "testnet_only_gate_before_mainnet",
        ),
    )
