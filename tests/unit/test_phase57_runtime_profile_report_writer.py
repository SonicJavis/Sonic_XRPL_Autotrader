import json

from sonic_xrpl.runtime_profile.report_writer import write_runtime_profile_reports


def test_phase57_report_writer_outputs_expected_files(tmp_path):
    generated = write_runtime_profile_reports(tmp_path)
    assert (tmp_path / "latest_runtime_profile.json").exists()
    assert (tmp_path / "latest_runtime_profile.md").exists()
    assert (tmp_path / "latest_runtime_profile_conformance.json").exists()
    assert (tmp_path / "latest_runtime_profile_conformance.md").exists()
    assert "runtime_profile_json" in generated


def test_phase57_json_report_has_safety_fields(tmp_path):
    write_runtime_profile_reports(tmp_path)
    payload = json.loads((tmp_path / "latest_runtime_profile.json").read_text(encoding="utf-8"))
    assert payload["paper_only"] is True
    assert payload["live_execution_allowed"] is False
    assert payload["signing_allowed"] is False
    assert payload["submission_allowed"] is False
