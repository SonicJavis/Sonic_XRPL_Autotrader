import json
from pathlib import Path

from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack, write_calibration_proposal_report


FIXTURE = Path("tests/fixtures/calibration_proposal/ready_for_review_recommendations.json")


def test_report_writer_writes_json_and_markdown(tmp_path):
    pack = build_calibration_proposal_pack(FIXTURE)
    generated = write_calibration_proposal_report(pack, tmp_path)

    json_path = tmp_path / "calibration_proposal_pack.json"
    md_path = tmp_path / "calibration_proposal_pack.md"
    assert generated["proposal_json"] == str(json_path)
    assert generated["proposal_markdown"] == str(md_path)
    assert json_path.exists()
    assert md_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    assert payload["pack_id"] == pack.pack_id
    assert payload["generated_at"] == pack.created_at
    assert payload["auto_apply_allowed"] is False
    assert payload["live_execution_allowed"] is False
    assert "No settings were changed." in markdown
    assert "Live execution remains blocked." in markdown
    assert "Human Review Checklist" in markdown
