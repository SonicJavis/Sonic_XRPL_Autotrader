from __future__ import annotations

from sonic_xrpl.xaman_approval_state_machine_spec.models import InvalidTransitionRule, TransitionRequirement


VALID_TRANSITIONS: tuple[TransitionRequirement, ...] = (
    TransitionRequirement(
        "DRAFT_REVIEW",
        "AWAITING_OPERATOR_REVIEW",
        ("candidate_reference", "risk_disclosure_reference"),
        True,
        True,
        True,
        True,
        "No runtime execution or callback handling is allowed in this phase.",
    ),
    TransitionRequirement(
        "AWAITING_OPERATOR_REVIEW",
        "OPERATOR_APPROVED_FOR_FUTURE_TESTNET",
        ("explicit_operator_approval",),
        True,
        True,
        True,
        True,
        "Approval is design-only and cannot trigger payload creation or execution.",
    ),
    TransitionRequirement(
        "AWAITING_OPERATOR_REVIEW",
        "OPERATOR_REJECTED",
        ("explicit_operator_rejection",),
        True,
        True,
        True,
        True,
        "Rejection is terminal for this review branch.",
    ),
    TransitionRequirement(
        "CALLBACK_RECEIVED_SPEC_ONLY",
        "CALLBACK_VERIFICATION_REQUIRED",
        ("callback_event_reference",),
        True,
        True,
        True,
        True,
        "Callback remains spec-only; no webhook runtime allowed.",
    ),
    TransitionRequirement(
        "CALLBACK_VERIFICATION_REQUIRED",
        "CALLBACK_VERIFIED_SPEC_ONLY",
        ("signature_checklist", "nonce_ttl_checklist", "idempotency_checklist"),
        True,
        True,
        True,
        True,
        "Verification is design-only and cannot move to execution states.",
    ),
    TransitionRequirement(
        "CALLBACK_VERIFIED_SPEC_ONLY",
        "AUDIT_REQUIRED",
        ("audit_envelope_reference",),
        True,
        True,
        True,
        True,
        "Audit is required before any final design acceptance.",
    ),
    TransitionRequirement(
        "AUDIT_REQUIRED",
        "FINAL_SPEC_ACCEPTED",
        ("audit_checklist_complete",),
        True,
        True,
        True,
        True,
        "Final accepted is spec-valid only, not executable.",
    ),
    TransitionRequirement(
        "AUDIT_REQUIRED",
        "FINAL_SPEC_REJECTED",
        ("audit_findings_present",),
        True,
        True,
        True,
        True,
        "Final rejected blocks the design until remediation.",
    ),
)


INVALID_TRANSITIONS: tuple[InvalidTransitionRule, ...] = (
    InvalidTransitionRule("*", "SIGNING", "Signing is out of scope and blocked."),
    InvalidTransitionRule("*", "SUBMISSION", "Submission is out of scope and blocked."),
    InvalidTransitionRule("*", "PAYLOAD_CREATION", "Payload creation is out of scope and blocked."),
    InvalidTransitionRule("*", "XAMAN_API_CALL", "Xaman API calls are out of scope and blocked."),
    InvalidTransitionRule("*", "WALLET_USE", "Wallet material handling is out of scope and blocked."),
    InvalidTransitionRule("*", "TESTNET_EXECUTION", "Testnet execution is blocked."),
    InvalidTransitionRule("*", "LIVE_EXECUTION", "Live execution is blocked."),
    InvalidTransitionRule(
        "CALLBACK_RECEIVED_SPEC_ONLY",
        "FINAL_SPEC_ACCEPTED",
        "Verification and audit cannot be skipped.",
    ),
    InvalidTransitionRule(
        "DUPLICATE_CALLBACK_REJECTED",
        "FINAL_SPEC_ACCEPTED",
        "Duplicate callback must remain rejected.",
    ),
    InvalidTransitionRule(
        "REPLAY_REJECTED",
        "FINAL_SPEC_ACCEPTED",
        "Replay callback must remain rejected.",
    ),
    InvalidTransitionRule(
        "EXPIRED",
        "OPERATOR_APPROVED_FOR_FUTURE_TESTNET",
        "Expired state cannot be approved.",
    ),
)
