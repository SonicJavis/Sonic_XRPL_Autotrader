from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec import (
    build_xaman_governance_closure_response_evidence_pack_review_digest_spec,
    load_xaman_governance_closure_response_evidence_pack_review_digest_fixture,
    render_xaman_governance_closure_response_evidence_pack_review_digest_json,
    render_xaman_governance_closure_response_evidence_pack_review_digest_markdown,
)
from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.models import (
    EVIDENCE_PACK_DIGEST_BLOCKED,
    EVIDENCE_PACK_DIGEST_INCOMPLETE,
    EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED,
    EVIDENCE_PACK_DIGEST_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.traceability import render_traceability_map

FIXTURES = Path("tests/fixtures/xaman_governance_closure_response_evidence_pack_review_digest_spec")


def _build(name: str):
    fixture = load_xaman_governance_closure_response_evidence_pack_review_digest_fixture(FIXTURES / f"{name}.json")
    return build_xaman_governance_closure_response_evidence_pack_review_digest_spec(fixture)


def test_complete_review_digest_is_deterministic_and_spec_review_only():
    first = _build("complete_spec_review_ready_evidence_pack_review_digest")
    second = _build("complete_spec_review_ready_evidence_pack_review_digest")
    assert render_xaman_governance_closure_response_evidence_pack_review_digest_json(first) == render_xaman_governance_closure_response_evidence_pack_review_digest_json(second)
    assert first.final_review_digest_classification == EVIDENCE_PACK_DIGEST_SPEC_REVIEW_READY
    payload = render_xaman_governance_closure_response_evidence_pack_review_digest_json(first)
    assert "ready for payload creation" not in payload.lower()
    assert "ready for testnet execution" not in payload.lower()
    assert "ready for live execution" not in payload.lower()
    flags = first.spec.safety_flags
    assert flags.spec_only is True
    assert flags.closure_response_evidence_pack_review_digest_spec_only is True
    assert flags.runtime_evidence_pack_review_digest_service_allowed is False
    assert flags.download_service_allowed is False
    assert flags.api_route_allowed is False
    assert flags.dashboard_ui_allowed is False
    assert flags.safety_bypass_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.xaman_payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.live_execution_allowed is False
    assert flags.runtime_mutation_allowed is False


def test_fail_closed_fixture_cases_classify_as_review_or_blocked():
    review_cases = [
        "incomplete_evidence_pack",
        "missing_evidence_completeness_summary",
        "missing_evidence_sufficiency_summary",
        "missing_owner_reviewer_summary",
        "missing_non_authorization_summary",
        "hidden_unresolved_blocker",
        "hidden_unresolved_limitation",
        "stale_evidence_summary_gap",
        "redacted_evidence_summary_gap",
        "reference_only_evidence_summary_gap",
        "synthetic_only_evidence_summary_gap",
        "unverified_evidence_summary_gap",
        "dependency_audit_evidence_summary_gap",
        "safety_review_evidence_summary_gap",
        "rejected_evidence_unresolved",
        "superseded_evidence_missing_replacement",
        "traceability_gap",
    ]
    for name in review_cases:
        report = _build(name)
        assert report.final_review_digest_classification in {EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED, EVIDENCE_PACK_DIGEST_INCOMPLETE}
        assert report.validation_errors
    assert _build("missing_evidence_pack").final_review_digest_classification == EVIDENCE_PACK_DIGEST_INCOMPLETE
    assert _build("blocked_evidence_pack").final_review_digest_classification == EVIDENCE_PACK_DIGEST_BLOCKED


def test_blocked_marker_fixtures_force_blocked_state():
    blocked_cases = [
        "blocked_due_xaman_payload_approval_wording",
        "blocked_due_wallet_material_approval_wording",
        "blocked_due_signing_submission_autofill_approval_wording",
        "blocked_due_testnet_live_execution_approval_wording",
        "blocked_due_runtime_evidence_pack_review_digest_service_marker",
        "blocked_due_download_service_marker",
        "blocked_due_api_ui_evidence_pack_digest_route_marker",
        "blocked_due_safety_bypass_marker",
    ]
    for name in blocked_cases:
        report = _build(name)
        assert report.final_review_digest_classification == EVIDENCE_PACK_DIGEST_BLOCKED
        assert report.blockers


def test_reports_and_traceability_include_required_phase_links():
    report = _build("complete_spec_review_ready_evidence_pack_review_digest")
    markdown = render_xaman_governance_closure_response_evidence_pack_review_digest_markdown(report)
    assert "Still no runtime evidence-pack review digest service." in markdown
    assert "Still no API/UI evidence-pack digest route." in markdown
    traceability = render_traceability_map(report)
    assert traceability["review_digest_to_phase88_evidence_pack"] == "P88-EVIDENCE-PACK-BUNDLE-001"
    assert traceability["review_digest_to_phase87_closure_response_resolution_register"] == "P87-CLOSURE-RESPONSE-RESOLUTION-REGISTER-001"
    assert traceability["review_digest_to_phase70_77_support_artifacts"]
    assert report.spec.review_digest_limitation_register == ()
