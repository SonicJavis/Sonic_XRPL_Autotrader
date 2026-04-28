from app.calibration.xrpl_time_execution_model import XRPLTimeExecutionInput, XRPLTimeExecutionModel


def _payload(**overrides) -> XRPLTimeExecutionInput:
    values = {
        "snapshot_price": 1.0,
        "execution_price": 1.0,
        "requested_size": 100.0,
        "snapshot_derived_liquidity": 100.0,
        "observed_possible_fill": 100.0,
        "ledger_index_snapshot": 100,
        "ledger_index_execution": 100,
        "competition_penalty": 0.0,
        "base_fill_probability": 0.8,
        "path_complexity": 0,
        "slippage_estimate": 0.0,
    }
    values.update(overrides)
    return XRPLTimeExecutionInput(**values)


def test_higher_latency_reduces_fill_probability() -> None:
    model = XRPLTimeExecutionModel()
    fast = model.evaluate(_payload(ledger_index_execution=100))
    slow = model.evaluate(_payload(ledger_index_execution=103))

    assert slow.effective_fill_probability < fast.effective_fill_probability


def test_higher_path_complexity_reduces_fill_probability() -> None:
    model = XRPLTimeExecutionModel()
    direct = model.evaluate(_payload(path_complexity=0))
    multi_hop = model.evaluate(_payload(path_complexity=2))

    assert multi_hop.effective_fill_probability < direct.effective_fill_probability


def test_zero_latency_has_no_penalty() -> None:
    result = XRPLTimeExecutionModel().evaluate(_payload())

    assert result.ledger_delay == 0
    assert result.latency_seconds == 0.0
    assert result.inclusion_probability == 1.0
    assert result.effective_fill_probability == 0.8


def test_zero_drift_has_no_ev_reduction() -> None:
    result = XRPLTimeExecutionModel().evaluate(_payload(base_fill_probability=1.0))

    assert result.price_drift == 0.0
    assert result.drift_amplified == 0.0
    assert result.drift_adjusted_ev == 1.0


def test_high_decay_drives_near_zero_fill_probability() -> None:
    result = XRPLTimeExecutionModel().evaluate(
        _payload(
            snapshot_derived_liquidity=1000.0,
            observed_possible_fill=0.001,
        )
    )

    assert result.liquidity_decay <= 0.000001
    assert result.effective_fill_probability <= 0.000001
