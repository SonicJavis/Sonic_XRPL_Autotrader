from __future__ import annotations

from sonic_xrpl.xaman_manual_approval_spec.models import (
    ApprovalIntentSpec,
    AuditTrailRequirement,
    ConsentUxRequirement,
    FutureGateChecklist,
    ImplementationBlocker,
    PayloadLifecycleRequirement,
    ReplayProtectionRequirement,
    XamanManualApprovalSpec,
    XamanSpecFixtureInput,
    XamanSpecReport,
)


def _base_blockers() -> tuple[ImplementationBlocker, ...]:
    return (
        ImplementationBlocker("B001", "CRITICAL", "No Xaman SDK approved", "No dependency approval for Xaman SDK integration.", True, True),
        ImplementationBlocker("B002", "CRITICAL", "No payload schema approved", "Payload template and policy contract are not finalized.", True, True),
        ImplementationBlocker("B003", "HIGH", "No callback/webhook threat model implementation", "Callback verification and replay defense are design-only.", True, True),
        ImplementationBlocker("B004", "HIGH", "No replay-protection implementation", "Nonce, TTL and idempotency checks are not implemented.", True, True),
        ImplementationBlocker("B005", "HIGH", "No consent UX implementation", "Operator confirmation UX and cancellation path are not implemented.", True, True),
        ImplementationBlocker("B006", "HIGH", "No audit persistence design implementation", "Immutable approval logging storage is not implemented.", True, True),
        ImplementationBlocker("B007", "HIGH", "No rollback design implementation", "Signed/submitted rollback handling is not implemented.", True, True),
        ImplementationBlocker("B008", "HIGH", "No testnet kill-switch implementation", "Testnet-only abort mechanism not implemented.", True, True),
        ImplementationBlocker("B009", "CRITICAL", "No secrets management design implementation", "Credential handling policy not implemented for any live flow.", True, True),
        ImplementationBlocker("B010", "CRITICAL", "No signing/submission approval", "No approved phase authorizes signing/submission.", True, True),
    )


def build_manual_approval_spec(row: XamanSpecFixtureInput) -> XamanSpecReport:
    errors: list[str] = []
    blocked_actions: list[str] = []

    if not row.risk_disclosure_present:
        errors.append("missing_risk_disclosure")
    if not row.replay_protection_present:
        errors.append("missing_replay_protection")
    if not row.expiry_ttl_present:
        errors.append("missing_approval_expiry_ttl")
    if not row.audit_trail_present:
        errors.append("missing_audit_trail")

    marker_map = {
        "attempted_payload_creation": row.attempted_payload_creation,
        "attempted_signing": row.attempted_signing,
        "attempted_submission": row.attempted_submission,
        "attempted_wallet_material": row.attempted_wallet_material,
        "attempted_live_execution": row.attempted_live_execution,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked_actions.append(marker)

    if row.future_testnet_requested:
        errors.append("future_testnet_gate_blocked")
    if row.future_mainnet_requested:
        errors.append("future_mainnet_gate_blocked")

    spec = XamanManualApprovalSpec(
        phase="61",
        objective="Xaman manual approval design-spec only",
        intent=ApprovalIntentSpec(
            spec_id=f"phase61_{row.fixture_id}",
            candidate_id=row.candidate_id,
            issuer=row.issuer,
            symbol=row.symbol,
            intelligence_verdict=row.intelligence_verdict,
            paper_simulation_reference=row.paper_simulation_reference,
        ),
        consent_ux=ConsentUxRequirement(
            risk_disclosure_required=True,
            explicit_yes_no_required=True,
            cancellation_required=True,
            non_investment_advice_notice_required=True,
        ),
        payload_lifecycle=PayloadLifecycleRequirement(
            design_spec_only=True,
            payload_creation_in_phase61=False,
            callback_webhook_design_required=True,
            callback_webhook_implemented=False,
        ),
        replay_protection=ReplayProtectionRequirement(
            approval_ttl_required=True,
            nonce_required=True,
            account_txn_id_chain_required=True,
            max_reuse_attempts=0,
        ),
        audit_trail=AuditTrailRequirement(
            immutable_log_required=True,
            decision_actor_required=True,
            decision_timestamp_required=True,
            cancellation_reason_required=True,
        ),
        implementation_blockers=_base_blockers(),
        future_gates=FutureGateChecklist(
            testnet_implementation_allowed=False,
            mainnet_live_allowed=False,
            blockers=(
                "separate_phase_required_for_payload_creation",
                "separate_phase_required_for_testnet_execution",
                "separate_phase_required_for_mainnet_live_execution",
            ),
        ),
    )

    return XamanSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        valid_design_spec=len(errors) == 0,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked_actions),
    )
