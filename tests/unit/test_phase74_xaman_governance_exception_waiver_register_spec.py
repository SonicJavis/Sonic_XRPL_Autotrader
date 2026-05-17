from sonic_xrpl.xaman_governance_exception_waiver_register_spec import (
    build_xaman_governance_exception_waiver_register_spec,
    load_xaman_governance_exception_waiver_register_fixture,
)
from sonic_xrpl.xaman_governance_exception_waiver_register_spec.models import (
    WAIVER_BLOCKED,
    WAIVER_EXPIRED,
    WAIVER_NOT_READY,
    WAIVER_REVIEW_REQUIRED,
    WAIVER_REVOKED,
    WAIVER_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_exception_waiver_register_spec.report_writer import (
    render_xaman_governance_exception_waiver_register_json,
    render_xaman_governance_exception_waiver_register_markdown,
)

BASE = "tests/fixtures/xaman_governance_exception_waiver_register_spec"

def _run(name: str):
    return build_xaman_governance_exception_waiver_register_spec(
        load_xaman_governance_exception_waiver_register_fixture(f"{BASE}/{name}")
    )

def test_phase74_complete_bundle_is_spec_review_ready_and_deterministic():
    first = _run("complete_spec_review_ready_waiver_register.json")
    second = _run("complete_spec_review_ready_waiver_register.json")
    assert first == second
    assert first.readiness_classification == WAIVER_SPEC_REVIEW_READY
    flags = first.spec.safety_flags
    assert flags.spec_only is True
    assert flags.waiver_register_spec_only is True
    assert flags.runtime_waiver_service_allowed is False
    assert flags.safety_bypass_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False

def test_phase74_accepted_for_spec_review_never_implies_execution_readiness():
    report = _run("waiver_accepted_for_spec_review_only.json")
    assert report.readiness_classification == WAIVER_SPEC_REVIEW_READY
    assert "accepted_for_spec_review_never_implies_execution_readiness" in report.spec.limitations

def test_phase74_missing_inputs_conservatively_require_review_or_not_ready():
    for name in [
        "waiver_requested_with_missing_evidence.json",
        "missing_reviewer.json",
        "missing_expiry_policy.json",
        "missing_revocation_policy.json",
        "missing_compensating_control.json",
        "dependency_audit_waiver_review_required.json",
        "untriaged_safety_review_waiver_review_required.json",
    ]:
        assert _run(name).readiness_classification in {WAIVER_NOT_READY, WAIVER_REVIEW_REQUIRED}

def test_phase74_terminal_states_remain_non_executing():
    assert _run("waiver_revoked.json").readiness_classification == WAIVER_REVOKED
    assert _run("waiver_expired.json").readiness_classification == WAIVER_EXPIRED
    assert _run("waiver_superseded.json").readiness_classification == WAIVER_REVIEW_REQUIRED
    assert _run("waiver_rejected.json").readiness_classification == WAIVER_REVIEW_REQUIRED

def test_phase74_unsafe_waiver_targets_force_blocked_state():
    for name in [
        "blocked_due_xaman_payload_waiver_attempt.json",
        "blocked_due_wallet_material_waiver_attempt.json",
        "blocked_due_signing_submission_autofill_waiver_attempt.json",
        "blocked_due_testnet_live_execution_waiver_attempt.json",
        "blocked_due_runtime_mutation_waiver_attempt.json",
        "blocked_due_guard_weakening_waiver_attempt.json",
        "blocked_due_safety_bypass_marker.json",
    ]:
        report = _run(name)
        assert report.readiness_classification == WAIVER_BLOCKED
        assert report.blockers

def test_phase74_traceability_and_report_output_are_stable():
    report = _run("complete_spec_review_ready_waiver_register.json")
    as_json = render_xaman_governance_exception_waiver_register_json(report)
    as_md = render_xaman_governance_exception_waiver_register_markdown(report)
    assert '"phase70_signoff_domain": "SAFETY_GUARDS"' in as_json
    assert '"runtime_waiver_service_allowed": false' in as_json
    assert '"safety_bypass_allowed": false' in as_json
    assert "Still no runtime waiver service." in as_md
    assert "Still no safety bypass." in as_md
