from math import isfinite

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


def _assert_output_invariants(body: dict[str, object]) -> None:
    assert isinstance(body["allow_trade"], bool)
    assert 0.0 <= body["latency_path_adjusted_probability"] <= 1.0
    assert 0.0 <= body["adjusted_execution_probability"] <= 1.0
    assert body["latency_path_adjusted_probability"] == body["adjusted_execution_probability"]
    assert body["effective_size"] >= 0.0
    for key in (
        "effective_size",
        "latency_path_adjusted_probability",
        "adjusted_execution_probability",
        "uncertainty_adjusted_value",
        "drift_adjusted_ev",
    ):
        assert isfinite(float(body[key]))


def test_trade_gate_api_phase_12_payload_stays_backward_compatible() -> None:
    client = TestClient(create_app())

    res = client.post("/trade-gate/evaluate", json=_payload())

    assert res.status_code == 200
    body = res.json()
    _assert_meta(body)
    _assert_output_invariants(body)
    assert "latency_path_adjusted_probability" in body
    assert "drift_adjusted_ev" in body
    assert "adjusted_execution_probability" in body


def test_trade_gate_api_low_fill_reliability_rejects() -> None:
    client = TestClient(create_app())
    res = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"fill_reliability": {"lower_bound": 0.05}}),
    )
    assert res.status_code == 200
    body = res.json()
    _assert_meta(body)
    _assert_output_invariants(body)
    assert body["allow_trade"] is False
    assert "LOW_EXECUTION_PROBABILITY" in body["risk_flags"]


def test_trade_gate_api_high_phantom_penalty_collapses_size() -> None:
    client = TestClient(create_app())
    low = client.post("/trade-gate/evaluate", json=_payload()).json()
    high = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"phantom_penalty": 0.9}),
    ).json()
    _assert_output_invariants(low)
    _assert_output_invariants(high)
    assert high["effective_size"] < low["effective_size"]


def test_trade_gate_api_high_competition_rejects() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"competition_penalty": 0.95}),
    ).json()
    _assert_meta(body)
    _assert_output_invariants(body)
    assert body["allow_trade"] is False
    assert "COMPETITION_RISK_HIGH" in body["risk_flags"]


def test_trade_gate_api_high_route_instability_rejects() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"route_instability": 0.95}),
    ).json()
    _assert_meta(body)
    _assert_output_invariants(body)
    assert body["allow_trade"] is False
    assert "ROUTE_UNSTABLE" in body["risk_flags"]


def test_trade_gate_api_ledger_delay_reduces_probability() -> None:
    client = TestClient(create_app())
    fast = client.post("/trade-gate/evaluate", json=_payload(calibration={"ledger_delay_error": 0.0})).json()
    slow = client.post("/trade-gate/evaluate", json=_payload(calibration={"ledger_delay_error": 1.0})).json()
    assert slow["latency_path_adjusted_probability"] < fast["latency_path_adjusted_probability"]


def test_trade_gate_api_high_path_complexity_reduces_probability() -> None:
    client = TestClient(create_app())
    direct = client.post("/trade-gate/evaluate", json=_payload(calibration={"path_complexity": 0, "route_instability": 0.0})).json()
    complex_path = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"path_complexity": 3, "route_instability": 0.0}),
    ).json()

    assert complex_path["latency_path_adjusted_probability"] < direct["latency_path_adjusted_probability"]


def test_trade_gate_api_high_drift_reduces_ev() -> None:
    client = TestClient(create_app())
    no_drift = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"snapshot_price": 1.0, "execution_price": 1.0}),
    ).json()
    high_drift = client.post(
        "/trade-gate/evaluate",
        json=_payload(calibration={"snapshot_price": 1.0, "execution_price": 2.0}),
    ).json()

    assert high_drift["drift_adjusted_ev"] < no_drift["drift_adjusted_ev"]


def test_trade_gate_api_safety_flags_trigger() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(
            calibration={
                "fill_reliability": {"lower_bound": 0.01},
                "expected_slippage_multiplier": 2.0,
                "snapshot_price": 1.0,
                "execution_price": 5.0,
                "slippage_estimate": 1.0,
            }
        ),
    ).json()

    _assert_output_invariants(body)
    assert "LOW_EXECUTION_PROBABILITY" in body["risk_flags"]
    assert "DRIFT_ADJUSTED_EV_LOW" in body["risk_flags"]
    assert "HIGH_SLIPPAGE_ENVIRONMENT" in body["risk_flags"]


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
    _assert_output_invariants(first.json())
    assert first.json() == second.json()
