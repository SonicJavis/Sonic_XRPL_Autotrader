from sonic_xrpl.xaman_operator_consent_ux_spec import (
    build_xaman_operator_consent_ux_spec,
    load_xaman_operator_consent_ux_fixture,
)
from sonic_xrpl.xaman_operator_consent_ux_spec.models import (
    CONSENT_BLOCKED,
    CONSENT_SPEC_INVALID,
    CONSENT_SPEC_REVIEW_REQUIRED,
    CONSENT_SPEC_VALID,
    INSUFFICIENT_EVIDENCE,
)
from sonic_xrpl.xaman_operator_consent_ux_spec.reporting import (
    render_xaman_operator_consent_ux_json,
    render_xaman_operator_consent_ux_markdown,
)


def _run(path: str):
    return build_xaman_operator_consent_ux_spec(load_xaman_operator_consent_ux_fixture(path))


def test_phase66_healthy_fixture_is_valid():
    report = _run("tests/fixtures/xaman_operator_consent_ux_spec/healthy_consent_ux_contract.json")
    assert report.outcome == CONSENT_SPEC_VALID
    flags = report.spec.safety_flags
    assert flags.ux_contract_spec_only is True
    assert flags.ui_implementation_allowed is False
    assert flags.api_route_allowed is False
    assert flags.runtime_consent_service_allowed is False
    assert flags.persistence_implementation_allowed is False
    assert flags.database_writes_allowed is False
    assert flags.callback_handler_allowed is False
    assert flags.webhook_runtime_allowed is False
    assert flags.payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False


def test_phase66_missing_disclosures_fail_closed():
    for name, error in [
        ("missing_no_live_execution_disclosure.json", "missing_no_live_execution_disclosure"),
        ("missing_no_wallet_material_disclosure.json", "missing_no_wallet_material_disclosure"),
        ("missing_payload_not_created_disclosure.json", "missing_payload_not_created_disclosure"),
        ("missing_signing_submission_unavailable_disclosure.json", "missing_signing_submission_unavailable_disclosure"),
        ("missing_risk_disclosure.json", "missing_risk_disclosure"),
        ("missing_source_provenance_section.json", "missing_source_provenance_section"),
        ("missing_paper_simulation_assumption_section.json", "missing_paper_simulation_assumption_section"),
        ("missing_stale_missing_evidence_disclosure.json", "missing_stale_missing_evidence_disclosure"),
        ("missing_operator_acknowledgement.json", "missing_operator_acknowledgement"),
        ("missing_confirmation_phrase_requirement.json", "missing_confirmation_phrase_requirement"),
    ]:
        report = _run(f"tests/fixtures/xaman_operator_consent_ux_spec/{name}")
        assert error in report.validation_errors


def test_phase66_unsafe_markers_blocked():
    for name in [
        "invalid_auto_approval_marker.json",
        "invalid_one_click_execution_marker.json",
        "attempted_ui_implementation_marker.json",
        "attempted_api_route_marker.json",
        "attempted_payload_creation_marker.json",
        "attempted_xaman_api_marker.json",
        "attempted_signing_submission_marker.json",
        "attempted_wallet_material_marker.json",
        "attempted_testnet_live_execution_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_operator_consent_ux_spec/{name}")
        assert report.outcome == CONSENT_BLOCKED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase66_intermediate_outcomes_available():
    report = _run("tests/fixtures/xaman_operator_consent_ux_spec/missing_no_live_execution_disclosure.json")
    assert report.outcome in {CONSENT_SPEC_REVIEW_REQUIRED, CONSENT_SPEC_INVALID, INSUFFICIENT_EVIDENCE}


def test_phase66_reporting_includes_required_sections():
    report = _run("tests/fixtures/xaman_operator_consent_ux_spec/healthy_consent_ux_contract.json")
    as_json = render_xaman_operator_consent_ux_json(report)
    as_md = render_xaman_operator_consent_ux_markdown(report)
    assert '"ux_contract_spec_only": true' in as_json
    assert '"ui_implementation_allowed": false' in as_json
    assert "Phase 66 Xaman Operator Consent UX Contract Spec" in as_md
