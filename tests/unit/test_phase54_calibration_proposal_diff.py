from pathlib import Path

from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack, render_proposal_diff


FIXTURE = Path("tests/fixtures/calibration_proposal/ready_for_review_recommendations.json")


def test_proposal_diff_is_deterministic_and_proposed_only():
    pack = build_calibration_proposal_pack(FIXTURE)
    first = render_proposal_diff(pack)
    second = render_proposal_diff(pack)

    assert first == second
    assert "proposed only - not applied" in first
    assert "No settings were changed." in first


def test_proposal_diff_respects_allowed_ranges():
    pack = build_calibration_proposal_pack(FIXTURE)

    for proposal in pack.proposals:
        lower, upper = proposal.parameter_ref.allowed_range
        assert lower <= proposal.proposed_value <= upper
