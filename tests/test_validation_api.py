from fastapi.testclient import TestClient

from app.main import create_app


def test_validation_uncertainty_report_has_required_meta() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/validation/uncertainty-report")
    assert res.status_code == 200
    body = res.json()
    assert body["is_truth"] is False
    assert body["is_validation_only"] is True
    assert "Observed data may not reflect executable liquidity" in body["xrpl_warning"]
    assert "report" in body


def test_validation_runs_endpoint_has_required_meta() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/validation/runs")
    assert res.status_code == 200
    body = res.json()
    assert body["is_truth"] is False
    assert body["is_validation_only"] is True
    assert "runs" in body


def test_validation_from_calibration_creates_run_with_required_meta() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.post("/validation/from-calibration")
    assert res.status_code == 200
    body = res.json()
    assert body["is_truth"] is False
    assert body["is_validation_only"] is True
    assert "run" in body
    assert "report" in body
