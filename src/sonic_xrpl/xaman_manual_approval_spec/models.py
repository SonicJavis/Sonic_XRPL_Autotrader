from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ManualApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


@dataclass(frozen=True)
class DesignSpecSafetyFlags:
    design_spec_only: bool = True
    manual_approval_required: bool = True
    payload_creation_allowed: bool = False
    signing_allowed: bool = False
    submission_allowed: bool = False
    autofill_allowed: bool = False
    wallet_material_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False


@dataclass(frozen=True)
class ApprovalIntentSpec:
    spec_id: str
    candidate_id: str
    issuer: str
    symbol: str
    intelligence_verdict: str
    paper_simulation_reference: str
    decision: ManualApprovalDecision = ManualApprovalDecision.PENDING


@dataclass(frozen=True)
class ConsentUxRequirement:
    risk_disclosure_required: bool
    explicit_yes_no_required: bool
    cancellation_required: bool
    non_investment_advice_notice_required: bool


@dataclass(frozen=True)
class PayloadLifecycleRequirement:
    design_spec_only: bool
    payload_creation_in_phase61: bool
    callback_webhook_design_required: bool
    callback_webhook_implemented: bool


@dataclass(frozen=True)
class ReplayProtectionRequirement:
    approval_ttl_required: bool
    nonce_required: bool
    account_txn_id_chain_required: bool
    max_reuse_attempts: int


@dataclass(frozen=True)
class AuditTrailRequirement:
    immutable_log_required: bool
    decision_actor_required: bool
    decision_timestamp_required: bool
    cancellation_reason_required: bool


@dataclass(frozen=True)
class FutureGateChecklist:
    testnet_implementation_allowed: bool
    mainnet_live_allowed: bool
    blockers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ImplementationBlocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_testnet: bool
    required_before_mainnet: bool


@dataclass(frozen=True)
class XamanManualApprovalSpec:
    phase: str
    objective: str
    intent: ApprovalIntentSpec
    consent_ux: ConsentUxRequirement
    payload_lifecycle: PayloadLifecycleRequirement
    replay_protection: ReplayProtectionRequirement
    audit_trail: AuditTrailRequirement
    implementation_blockers: tuple[ImplementationBlocker, ...]
    future_gates: FutureGateChecklist
    safety_flags: DesignSpecSafetyFlags = DesignSpecSafetyFlags()


@dataclass(frozen=True)
class XamanSpecFixtureInput:
    fixture_id: str
    candidate_id: str
    issuer: str
    symbol: str
    intelligence_verdict: str
    paper_simulation_reference: str
    risk_disclosure_present: bool
    replay_protection_present: bool
    expiry_ttl_present: bool
    audit_trail_present: bool
    attempted_payload_creation: bool = False
    attempted_signing: bool = False
    attempted_submission: bool = False
    attempted_wallet_material: bool = False
    attempted_live_execution: bool = False
    future_testnet_requested: bool = False
    future_mainnet_requested: bool = False


@dataclass(frozen=True)
class XamanSpecReport:
    fixture_id: str
    spec: XamanManualApprovalSpec
    valid_design_spec: bool
    validation_errors: tuple[str, ...]
    blocked_actions: tuple[str, ...]


def jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value
