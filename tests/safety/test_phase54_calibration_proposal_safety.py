from pathlib import Path

from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack


FIXTURE = Path("tests/fixtures/calibration_proposal/ready_for_review_recommendations.json")


def test_phase54_live_flags_remain_false():
    pack = build_calibration_proposal_pack(FIXTURE)

    assert pack.live_execution_allowed is False
    assert pack.auto_apply_allowed is False
    assert all(item.live_execution_allowed is False for item in pack.proposals)
    assert all(item.auto_apply_allowed is False for item in pack.proposals)
    assert all(item.human_review_required is True for item in pack.proposals)


def test_phase54_has_no_forbidden_runtime_terms():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/calibration_proposal").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "Xaman",
        "fromSeed",
        "familySeed",
        "auto-buy",
        "place_order",
        "while True",
        "websocket",
        "requests.",
    ]
    for term in forbidden:
        assert term not in combined


def test_phase54_no_forbidden_command_names_exist():
    cli_source = Path("src/sonic_xrpl/cli/main.py").read_text(encoding="utf-8")
    forbidden = [
        "apply-calibration",
        "calibration-apply",
        "approve-and-apply",
        "live-calibrate",
        "auto-calibrate",
    ]
    for command in forbidden:
        assert command not in cli_source


def test_phase54_proposals_do_not_mutate_config_files():
    config_paths = [
        Path("pyproject.toml"),
        Path(".env.example"),
    ]
    before = {path: path.read_text(encoding="utf-8") for path in config_paths if path.exists()}

    build_calibration_proposal_pack(FIXTURE)

    after = {path: path.read_text(encoding="utf-8") for path in config_paths if path.exists()}
    assert before == after
