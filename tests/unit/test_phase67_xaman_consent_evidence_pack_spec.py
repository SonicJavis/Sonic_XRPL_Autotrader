from sonic_xrpl.xaman_consent_evidence_pack_spec import (
    build_xaman_consent_evidence_pack_spec,
    load_xaman_consent_evidence_pack_fixture,
)
from sonic_xrpl.xaman_consent_evidence_pack_spec.models import (
    EVIDENCE_PACK_BLOCKED,
    EVIDENCE_PACK_INVALID,
    EVIDENCE_PACK_REVIEW_REQUIRED,
    EVIDENCE_PACK_VALID,
    INSUFFICIENT_EVIDENCE,
)
from sonic_xrpl.xaman_consent_evidence_pack_spec.reporting import (
    render_xaman_consent_evidence_pack_json,
    render_xaman_consent_evidence_pack_markdown,
)


def _run(path: str):
    return build_xaman_consent_evidence_pack_spec(load_xaman_consent_evidence_pack_fixture(path))


def test_phase67_healthy_fixture_is_valid():
    report = _run("tests/fixtures/xaman_consent_evidence_pack_spec/healthy_evidence_pack.json")
    assert report.outcome == EVIDENCE_PACK_VALID
    flags = report.spec.safety_flags
    assert flags.evidence_pack_spec_only is True
    assert flags.export_implementation_allowed is False
    assert flags.file_write_allowed is False
    assert flags.ui_implementation_allowed is False
    assert flags.api_route_allowed is False
    assert flags.runtime_service_allowed is False
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


def test_phase67_missing_required_evidence_fail_closed():
    for name, error in [
        ("missing_candidate_identity.json", "missing_candidate_identity"),
        ("missing_provenance.json", "missing_provenance"),
        ("missing_firstledger_intelligence_reference.json", "missing_firstledger_intelligence_reference"),
        ("missing_paper_simulation_reference.json", "missing_paper_simulation_reference"),
        ("missing_paper_simulation_assumptions.json", "missing_paper_simulation_assumptions"),
        ("missing_xaman_payload_schema_reference.json", "missing_xaman_payload_schema_reference"),
        ("missing_callback_verification_reference.json", "missing_callback_verification_reference"),
        ("missing_audit_idempotency_reference.json", "missing_audit_idempotency_reference"),
        ("missing_approval_state_machine_reference.json", "missing_approval_state_machine_reference"),
        ("missing_consent_ux_reference.json", "missing_consent_ux_reference"),
        ("missing_risk_disclosure_bundle.json", "missing_risk_disclosure_bundle"),
        ("missing_stale_missing_evidence_disclosure.json", "missing_stale_missing_evidence_disclosure"),
        ("missing_no_live_execution_blocker.json", "missing_no_live_execution_blocker"),
        ("missing_wallet_material_exclusion.json", "missing_wallet_material_exclusion"),
        ("missing_secrets_exclusion.json", "missing_secrets_exclusion"),
    ]:
        report = _run(f"tests/fixtures/xaman_consent_evidence_pack_spec/{name}")
        assert error in report.validation_errors


def test_phase67_unsafe_markers_are_blocked():
    for name in [
        "invalid_payload_created_marker.json",
        "invalid_xaman_called_marker.json",
        "invalid_signing_submission_marker.json",
        "invalid_wallet_material_marker.json",
        "invalid_export_file_write_marker.json",
        "invalid_ui_api_runtime_marker.json",
        "invalid_testnet_live_execution_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_consent_evidence_pack_spec/{name}")
        assert report.outcome == EVIDENCE_PACK_BLOCKED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase67_intermediate_outcomes_available():
    report = _run("tests/fixtures/xaman_consent_evidence_pack_spec/missing_candidate_identity.json")
    assert report.outcome in {EVIDENCE_PACK_REVIEW_REQUIRED, EVIDENCE_PACK_INVALID, INSUFFICIENT_EVIDENCE}


def test_phase67_reporting_includes_evidence_sections():
    report = _run("tests/fixtures/xaman_consent_evidence_pack_spec/healthy_evidence_pack.json")
    as_json = render_xaman_consent_evidence_pack_json(report)
    as_md = render_xaman_consent_evidence_pack_markdown(report)
    assert '"evidence_pack_spec_only": true' in as_json
    assert '"export_implementation_allowed": false' in as_json
    assert "Phase 67 Xaman Consent Evidence Pack Spec" in as_md
