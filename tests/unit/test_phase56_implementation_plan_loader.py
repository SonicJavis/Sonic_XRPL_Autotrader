import pytest

from sonic_xrpl.calibration_implementation_plan.errors import ImplementationInputError
from sonic_xrpl.calibration_implementation_plan.loader import load_approval_ledger, load_change_requests


def test_load_approval_ledger_works():
    data = load_approval_ledger("reports/phase55/latest_calibration_approval_ledger.json")
    assert data["ledger_id"].startswith("cal_")
    assert isinstance(data["records"], list)


def test_load_change_requests_works():
    data = load_change_requests("reports/phase55/latest_calibration_change_requests.json")
    assert len(data) >= 1
    assert "change_request_id" in data[0]


def test_loader_rejects_invalid_shape(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"not":"a-list"}', encoding="utf-8")
    with pytest.raises(ImplementationInputError):
        load_change_requests(str(bad))
