import json

from sonic_xrpl.calibration_review import (
    build_threshold_recommendations,
    evaluate_readiness,
    load_evidence_snapshot,
    write_calibration_review_report,
)


FIXTURE = "tests/fixtures/calibration_review/sufficient_source_backed_evidence.json"


def test_phase53_report_writer_writes_json_and_markdown(tmp_path):
    result = evaluate_readiness(load_evidence_snapshot(FIXTURE))
    recommendations = build_threshold_recommendations(result)
    report = write_calibration_review_report(result, recommendations, tmp_path)

    json_path = tmp_path / "calibration_readiness.json"
    md_path = tmp_path / "calibration_readiness.md"
    rec_path = tmp_path / "calibration_recommendations.json"
    assert json_path.exists()
    assert md_path.exists()
    assert rec_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_id"] == report.report_id
    assert payload["paper_only"] is True
    assert payload["live_execution_allowed"] is False
    text = md_path.read_text(encoding="utf-8")
    assert "Recommendations are advisory only" in text
    assert "not executable fill claims" in text


def test_phase53_report_writer_is_deterministic(tmp_path):
    result = evaluate_readiness(load_evidence_snapshot(FIXTURE))
    recommendations = build_threshold_recommendations(result)
    first = write_calibration_review_report(result, recommendations, tmp_path)
    first_text = (tmp_path / "calibration_readiness.md").read_text(encoding="utf-8")
    second = write_calibration_review_report(result, recommendations, tmp_path)
    second_text = (tmp_path / "calibration_readiness.md").read_text(encoding="utf-8")

    assert first.report_id == second.report_id
    assert first_text == second_text
