from sonic_xrpl.xaman_governance_evidence_attestation_spec import (
    build_xaman_governance_evidence_attestation_spec,
    load_xaman_governance_evidence_attestation_fixture,
)
from sonic_xrpl.xaman_governance_evidence_attestation_spec.models import (
    ATTESTATION_BLOCKED,
    ATTESTATION_NOT_READY,
    ATTESTATION_REVIEW_REQUIRED,
    ATTESTATION_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_evidence_attestation_spec.report_writer import (
    render_xaman_governance_evidence_attestation_json,
    render_xaman_governance_evidence_attestation_markdown,
)


def _run(path: str):
    return build_xaman_governance_evidence_attestation_spec(
        load_xaman_governance_evidence_attestation_fixture(path)
    )


def test_phase71_complete_bundle_is_spec_review_ready():
    report = _run(
        "tests/fixtures/xaman_governance_evidence_attestation_spec/complete_spec_review_ready_bundle.json"
    )
    assert report.readiness_classification == ATTESTATION_SPEC_REVIEW_READY
    f = report.spec.safety_flags
    assert f.spec_only is True
    assert f.attestation_only is True
    assert f.testnet_execution_allowed is False
    assert f.xaman_payload_creation_allowed is False
    assert f.live_execution_allowed is False


def test_phase71_missing_or_integrity_issues_are_conservative():
    for name in [
        "missing_evidence_artifact.json",
        "hash_mismatch.json",
        "stale_evidence.json",
        "synthetic_only_requires_review.json",
        "missing_reviewer.json",
        "ambiguous_signoff_linkage.json",
        "dependency_report_missing.json",
        "safety_scan_untriaged.json",
        "rollback_evidence_missing.json",
        "incident_response_evidence_missing.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_evidence_attestation_spec/{name}")
        assert report.readiness_classification in {
            ATTESTATION_REVIEW_REQUIRED,
            ATTESTATION_NOT_READY,
        }


def test_phase71_unsafe_markers_block():
    for name in [
        "blocked_payload_testnet_live_wording.json",
        "blocked_wallet_material_ambiguity.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_evidence_attestation_spec/{name}")
        assert report.readiness_classification == ATTESTATION_BLOCKED
        assert report.blockers


def test_phase71_report_formats_include_safety_statement():
    report = _run(
        "tests/fixtures/xaman_governance_evidence_attestation_spec/complete_spec_review_ready_bundle.json"
    )
    as_json = render_xaman_governance_evidence_attestation_json(report)
    as_md = render_xaman_governance_evidence_attestation_markdown(report)
    assert '"attestation_only": true' in as_json
    assert "Still no Xaman payload creation." in as_md
