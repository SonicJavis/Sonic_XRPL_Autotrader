import json

from sonic_xrpl.calibration_approval import build_approval_ledger, write_approval_reports


def test_phase55_report_writer_outputs_json_and_markdown(tmp_path):
    proposal = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"
    review = "tests/fixtures/calibration_approval/approved_change_request.json"
    ledger = build_approval_ledger(proposal, review)

    generated = write_approval_reports(ledger, proposal, review, tmp_path)

    assert (tmp_path / "latest_calibration_approval_ledger.json").exists()
    assert (tmp_path / "latest_calibration_approval_ledger.md").exists()
    assert (tmp_path / "latest_calibration_change_requests.json").exists()
    assert (tmp_path / "latest_calibration_change_requests.md").exists()
    payload = json.loads((tmp_path / "latest_calibration_approval_ledger.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "latest_calibration_approval_ledger.md").read_text(encoding="utf-8")
    request_md = (tmp_path / "latest_calibration_change_requests.md").read_text(encoding="utf-8")
    assert payload["ledger_id"] == ledger.ledger_id
    assert payload["phase"] == "55"
    assert "No calibration changes are applied." in markdown
    assert "Live execution remains blocked." in markdown
    assert "Change requests are review artifacts only." in request_md
    assert generated["approval_ledger_json"].endswith("latest_calibration_approval_ledger.json")
