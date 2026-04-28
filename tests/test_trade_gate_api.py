from fastapi.testclient import TestClient

from app.main import create_app


def _payload(**overrides):
    payload = {
        "requested_size": 100.0,
        "expected_profit": 20.0,
        "expected_loss": 10.0,
        "calibration": {
            "fill_reliability": {"lower_bound": 0.8},
            "expected_slippage_multiplier": 1.1,
            "liquidity_haircut": 0.1,
            "phantom_penalty": 0.1,
            "route_instability": 0.1,
            "competition_penalty": 0.1,
            "ledger_delay_error": 0.1,
            "snapshot_derived_liquidity": 100.0,
            "observed_possible_fill": 100.0,
        },
    }
    for key, value in overrides.items():
        if key == "calibration":
            payload["calibration"].update(value)
        else:
            payload[key] = value
    return payload


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert body["is_shadow"] is True
    assert "xrpl_warning" in body


def test_trade_gate_api_low_fill_reliability_rejects() -> None:
    client = TestClient(create_app())
    res = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"fill_reliability": {"lower_bound": 0.05}}),
    )
    assert res.status_code == 200
    body = res.json()
    _assert_meta(body)
    assert body["allow_trade"] is False
    assert "LOW_EXECUTION_PROBABILITY" in body["risk_flags"]


def test_trade_gate_api_high_phantom_penalty_collapses_size() -> None:
    client = TestClient(create_app())
    low = client.post("/trade-gate/evaluate", json=_payload()).json()
    high = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"phantom_penalty": 0.9}),
    ).json()
    assert high["effective_size"] < low["effective_size"]


def test_trade_gate_api_high_competition_rejects() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"competition_penalty": 0.95}),
    ).json()
    _assert_meta(body)
    assert body["allow_trade"] is False
    assert "COMPETITION_RISK_HIGH" in body["risk_flags"]


def test_trade_gate_api_high_route_instability_rejects() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"route_instability": 0.95}),
    ).json()
    _assert_meta(body)
    assert body["allow_trade"] is False
    assert "ROUTE_UNSTABLE" in body["risk_flags"]


def test_trade_gate_api_ledger_delay_reduces_probability() -> None:
    client = TestClient(create_app())
    fast = client.post("/trade-gate/evaluate", json=_payload(calibration={"ledger_delay_error": 0.0})).json()
    slow = client.post("/trade-gate/evaluate", json=_payload(calibration={"ledger_delay_error": 1.0})).json()
    assert slow["latency_path_adjusted_probability"] < fast["latency_path_adjusted_probability"]


def test_trade_gate_api_is_deterministic() -> None:
    client = TestClient(create_app())
    payload = _payload(
        requested_size=75.0,
        expected_profit=12.0,
        expected_loss=8.0,
        calibration={
            "fill_reliability": {"lower_bound": 0.55},
            "expected_slippage_multiplier": 1.4,
            "liquidity_haircut": 0.2,
            "phantom_penalty": 0.15,
            "route_instability": 0.25,
            "competition_penalty": 0.1,
            "ledger_delay_error": 0.2,
        },
    )
    first = client.post("/trade-gate/evaluate", json=payload)
    second = client.post("/trade-gate/evaluate", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
