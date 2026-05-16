from sonic_xrpl.xaman_governance_signoff_matrix_spec import (
    build_xaman_governance_signoff_matrix_spec,
    load_xaman_governance_signoff_matrix_fixture,
)
from sonic_xrpl.xaman_governance_signoff_matrix_spec.models import (
    READINESS_BLOCKED,
    READINESS_NOT_READY,
    READINESS_REVIEW_REQUIRED,
    READINESS_SPEC_ONLY_READY,
)
from sonic_xrpl.xaman_governance_signoff_matrix_spec.reporting import (
    render_xaman_governance_signoff_matrix_json,
    render_xaman_governance_signoff_matrix_markdown,
)


def _run(path: str):
    return build_xaman_governance_signoff_matrix_spec(
        load_xaman_governance_signoff_matrix_fixture(path)
    )


def test_phase70_healthy_fixture_is_spec_only_ready():
    report = _run(
        "tests/fixtures/xaman_governance_signoff_matrix_spec/healthy_governance_signoff_matrix.json"
    )
    assert report.readiness_classification == READINESS_SPEC_ONLY_READY
    f = report.spec.safety_flags
    assert f.spec_only is True
    assert f.testnet_execution_allowed is False
    assert f.xaman_payload_creation_allowed is False
    assert f.live_execution_allowed is False
    assert f.runtime_mutation_allowed is False


def test_phase70_missing_required_evidence_is_conservative():
    report = _run(
        "tests/fixtures/xaman_governance_signoff_matrix_spec/missing_security_reviewer_evidence.json"
    )
    assert report.readiness_classification in {
        READINESS_REVIEW_REQUIRED,
        READINESS_NOT_READY,
    }
    assert "missing_safety_guards_evidence" in report.validation_errors


def test_phase70_blocked_markers_fail_closed():
    for name in [
        "blocked_xaman_payload_ambiguity.json",
        "blocked_wallet_material_ambiguity.json",
        "blocked_dependency_risk.json",
        "invalid_testnet_approved_marker.json",
        "invalid_live_approved_marker.json",
        "invalid_runtime_execution_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_signoff_matrix_spec/{name}")
        assert report.readiness_classification == READINESS_BLOCKED


def test_phase70_report_formats_include_safety_statement():
    report = _run(
        "tests/fixtures/xaman_governance_signoff_matrix_spec/healthy_governance_signoff_matrix.json"
    )
    as_json = render_xaman_governance_signoff_matrix_json(report)
    as_md = render_xaman_governance_signoff_matrix_markdown(report)
    assert '"spec_only": true' in as_json
    assert '"testnet_execution_allowed": false' in as_json
    assert "Still no live execution." in as_md
