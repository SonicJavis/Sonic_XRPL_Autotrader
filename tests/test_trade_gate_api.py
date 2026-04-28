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
    assert 0.0 <= body["memory_adjusted_probability"] <= 1.0
    assert body["effective_size"] >= 0.0
    assert body["memory_adjusted_effective_size"] >= 0.0
    for key in (
        "effective_size",
        "memory_adjusted_effective_size",
        "latency_path_adjusted_probability",
        "adjusted_execution_probability",
        "memory_adjusted_probability",
        "uncertainty_adjusted_value",
        "drift_adjusted_ev",
        "memory_probability_multiplier",
        "memory_size_multiplier",
        "memory_slippage_boost",
        "memory_ev_penalty",
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
    assert "memory_adjusted_probability" in body
    assert "memory_adjusted_effective_size" in body
    assert body["memory_risk_flags"] == []


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


def test_trade_gate_api_memory_payload_changes_output_and_preserves_alias() -> None:
    client = TestClient(create_app())
    memory = {
        "global": {
            "scope": "global",
            "key": "all",
            "liquidity_reliability": 0.2,
            "execution_reliability": 0.2,
            "regime_pressure_score": 0.8,
            "avg_phantom_penalty": 0.6,
            "avg_route_instability": 0.4,
            "avg_latency_seconds": 16.0,
            "avg_drift_adjusted_ev": -0.3,
            "advisory_risk_level": "HIGH",
        },
        "token": None,
        "issuer": None,
        "global_regime": {"regime": "LIQUIDITY_ILLUSION", "severity_score": 0.9, "risk_flags": []},
    }

    base = client.post("/trade-gate/evaluate", json=_payload()).json()
    weighted = client.post("/trade-gate/evaluate", json=_payload(memory=memory)).json()

    _assert_meta(weighted)
    _assert_output_invariants(weighted)
    assert weighted["adjusted_execution_probability"] == weighted["latency_path_adjusted_probability"]
    assert weighted["memory_adjusted_probability"] < base["memory_adjusted_probability"]
    assert weighted["memory_adjusted_effective_size"] < base["memory_adjusted_effective_size"]
    assert "PHANTOM_LIQUIDITY_MEMORY" in weighted["memory_risk_flags"]
    assert "PHANTOM_LIQUIDITY_MEMORY" in weighted["risk_flags"]


def test_trade_gate_api_execution_collapse_memory_blocks_allow_trade() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(
            expected_profit=100.0,
            expected_loss=1.0,
            memory={
                "global": {"advisory_risk_level": "CRITICAL", "regime_pressure_score": 1.0},
                "global_regime": {"regime": "EXECUTION_COLLAPSE", "severity_score": 1.0, "risk_flags": []},
            },
        ),
    ).json()

    _assert_output_invariants(body)
    assert body["allow_trade"] is False
    assert "EXECUTION_MEMORY_COLLAPSE" in body["memory_risk_flags"]


def test_trade_gate_api_path_and_issuer_memory_flags_propagate() -> None:
    client = TestClient(create_app())
    body = client.post(
        "/trade-gate/evaluate",
        json=_payload(
            memory={
                "global": {"advisory_risk_level": "MEDIUM", "regime_pressure_score": 0.4},
                "global_regime": {
                    "regime": "ROUTE_UNSTABLE",
                    "severity_score": 0.7,
                    "risk_flags": ["PATH_FAILURE_RISK", "ISSUER_RISK_PROXY"],
                },
            }
        ),
    ).json()

    _assert_output_invariants(body)
    assert "ROUTE_MEMORY_UNSTABLE" in body["memory_risk_flags"]
    assert "PATH_MEMORY_FAILURE" in body["memory_risk_flags"]
    assert "ISSUER_MEMORY_RISK" in body["memory_risk_flags"]
