from __future__ import annotations

from sonic_xrpl.xaman_governance_signoff_matrix_spec.models import (
    READINESS_BLOCKED,
    READINESS_NOT_READY,
    READINESS_REVIEW_REQUIRED,
    READINESS_SPEC_ONLY_READY,
    GovernanceBlocker,
    GovernanceRequirement,
    XamanGovernanceFixtureInput,
    XamanGovernanceSignoffMatrixSpec,
    XamanGovernanceSignoffReport,
)

SIGNOFF_ROLES = (
    "SECURITY_REVIEWER",
    "XRPL_PROTOCOL_REVIEWER",
    "XAMAN_REVIEWER",
    "OPERATOR",
    "RISK_REVIEWER",
    "RELEASE_REVIEWER",
    "AUDIT_REVIEWER",
)

SIGNOFF_DOMAINS = (
    "SAFETY_GUARDS",
    "XAMAN_PAYLOAD_BOUNDARY",
    "TESTNET_BOUNDARY",
    "WALLET_MATERIAL_BOUNDARY",
    "DEPENDENCY_SUPPLY_CHAIN",
    "FIRSTLEDGER_DATA_BOUNDARY",
    "OPERATOR_CONSENT",
    "ROLLBACK_READINESS",
    "OBSERVABILITY",
    "INCIDENT_RESPONSE",
    "LEGAL_POLICY_REVIEW",
)

SIGNOFF_STATUSES = (
    "NOT_STARTED",
    "EVIDENCE_PENDING",
    "READY_FOR_REVIEW",
    "APPROVED_FOR_SPEC_ONLY",
    "REJECTED",
    "BLOCKED",
    "DEFERRED",
)

EVIDENCE_REQUIREMENTS: tuple[GovernanceRequirement, ...] = (
    GovernanceRequirement("safety_guards_evidence", "Safety guards evidence", "SECURITY_REVIEWER", True, "CRITICAL", True, "Must preserve fail-closed runtime boundaries."),
    GovernanceRequirement("xaman_payload_boundary_evidence", "Xaman payload boundary evidence", "XAMAN_REVIEWER", True, "CRITICAL", True, "Phase 70 does not authorize payload creation."),
    GovernanceRequirement("testnet_boundary_evidence", "Testnet boundary evidence", "XRPL_PROTOCOL_REVIEWER", True, "CRITICAL", True, "No testnet execution permitted."),
    GovernanceRequirement("wallet_material_boundary_evidence", "Wallet-material boundary evidence", "SECURITY_REVIEWER", True, "CRITICAL", True, "No wallet seed/private-key handling."),
    GovernanceRequirement("dependency_supply_chain_evidence", "Dependency supply-chain evidence", "AUDIT_REVIEWER", True, "HIGH", True, "No unaudited dependency changes."),
    GovernanceRequirement("firstledger_data_boundary_evidence", "FirstLedger data boundary evidence", "RISK_REVIEWER", True, "MEDIUM", True, "No live ingestion coupling."),
    GovernanceRequirement("operator_consent_evidence", "Operator consent evidence", "OPERATOR", True, "HIGH", True, "Must preserve manual approval contract."),
    GovernanceRequirement("rollback_readiness_evidence", "Rollback readiness evidence", "RELEASE_REVIEWER", True, "HIGH", True, "Rollback and kill-switch references required."),
    GovernanceRequirement("observability_evidence", "Observability evidence", "AUDIT_REVIEWER", False, "MEDIUM", True, "Spec-only observability traceability."),
    GovernanceRequirement("incident_response_evidence", "Incident response evidence", "SECURITY_REVIEWER", False, "MEDIUM", True, "Incident process references required."),
    GovernanceRequirement("legal_policy_review_evidence", "Legal/policy review evidence", "RISK_REVIEWER", False, "LOW", True, "Policy index alignment and constraints."),
)


def _base_blockers() -> tuple[GovernanceBlocker, ...]:
    return (
        GovernanceBlocker("P7001", "missing_evidence", "CRITICAL", "Missing mandatory governance evidence", "Mandatory sign-off evidence is missing."),
        GovernanceBlocker("P7002", "unsafe_runtime_path", "CRITICAL", "Runtime authorization blocked", "Runtime/testnet/live execution authorization is out of scope."),
        GovernanceBlocker("P7003", "xaman_payload_ambiguity", "CRITICAL", "Xaman payload boundary ambiguity", "Payload creation must remain explicitly blocked."),
        GovernanceBlocker("P7004", "wallet_material_ambiguity", "CRITICAL", "Wallet material boundary ambiguity", "Wallet material must remain explicitly blocked."),
        GovernanceBlocker("P7005", "dependency_risk", "HIGH", "Dependency/supply-chain risk", "Dependency risk must be resolved before future implementation."),
    )


def build_xaman_governance_signoff_matrix_spec(
    row: XamanGovernanceFixtureInput,
) -> XamanGovernanceSignoffReport:
    errors: list[str] = []
    blockers: list[str] = []

    required_checks = (
        ("missing_safety_guards_evidence", row.has_safety_guards_evidence),
        ("missing_xaman_payload_boundary_evidence", row.has_xaman_payload_boundary_evidence),
        ("missing_testnet_boundary_evidence", row.has_testnet_boundary_evidence),
        ("missing_wallet_material_boundary_evidence", row.has_wallet_material_boundary_evidence),
        ("missing_dependency_supply_chain_evidence", row.has_dependency_supply_chain_evidence),
        ("missing_firstledger_data_boundary_evidence", row.has_firstledger_data_boundary_evidence),
        ("missing_operator_consent_evidence", row.has_operator_consent_evidence),
        ("missing_rollback_readiness_evidence", row.has_rollback_readiness_evidence),
        ("missing_observability_evidence", row.has_observability_evidence),
        ("missing_incident_response_evidence", row.has_incident_response_evidence),
        ("missing_legal_policy_review_evidence", row.has_legal_policy_review_evidence),
        ("missing_safety_scan_review_triage", row.has_safety_scan_review_triage),
        ("missing_guard_critical_approval", row.has_guard_critical_approval),
    )
    for key, present in required_checks:
        if not present:
            errors.append(key)

    marker_map = {
        "blocked_xaman_payload_ambiguity": row.invalid_xaman_payload_ambiguity_marker,
        "blocked_wallet_material_ambiguity": row.invalid_wallet_material_ambiguity_marker,
        "blocked_dependency_risk": row.invalid_dependency_risk_marker,
        "blocked_testnet_approved_marker": row.invalid_testnet_approved_marker,
        "blocked_live_approved_marker": row.invalid_live_approved_marker,
        "blocked_runtime_execution_marker": row.invalid_runtime_execution_marker,
    }
    for key, enabled in marker_map.items():
        if enabled:
            errors.append(key)
            blockers.append(key)

    if blockers:
        outcome = READINESS_BLOCKED
    elif errors:
        if len(errors) >= 7:
            outcome = READINESS_NOT_READY
        else:
            outcome = READINESS_REVIEW_REQUIRED
    else:
        outcome = READINESS_SPEC_ONLY_READY

    spec = XamanGovernanceSignoffMatrixSpec(
        phase="70",
        objective="Xaman testnet governance sign-off matrix contract spec",
        matrix_id=row.matrix_id,
        signoff_roles=SIGNOFF_ROLES,
        signoff_domains=SIGNOFF_DOMAINS,
        signoff_statuses=SIGNOFF_STATUSES,
        evidence_requirements=EVIDENCE_REQUIREMENTS,
        blockers=_base_blockers(),
    )
    return XamanGovernanceSignoffReport(
        fixture_id=row.fixture_id,
        spec=spec,
        readiness_classification=outcome,
        validation_errors=tuple(errors),
        blockers=tuple(blockers),
    )
