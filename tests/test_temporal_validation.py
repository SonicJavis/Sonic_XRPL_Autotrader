from app.validation.temporal_validation import TemporalValidationInput, TemporalValidationLayer


def test_collapsing_book_has_high_decay_rate() -> None:
    out = TemporalValidationLayer().validate(
        TemporalValidationInput(
            ledger_indices=[100, 101, 102, 103],
            total_depth_xrp=[1200.0, 900.0, 500.0, 250.0],
            simulator_latency_ledgers=1,
        )
    )
    assert out.depth_decay_rate > 0.25
    assert out.orderbook_collapse_detected is True


def test_stable_book_has_low_decay_rate() -> None:
    out = TemporalValidationLayer().validate(
        TemporalValidationInput(
            ledger_indices=[100, 101, 102, 103],
            total_depth_xrp=[1200.0, 1180.0, 1170.0, 1165.0],
            simulator_latency_ledgers=3,
        )
    )
    assert out.depth_decay_rate < 0.05
    assert out.orderbook_collapse_detected is False


def test_delayed_execution_mismatch_is_flagged() -> None:
    out = TemporalValidationLayer().validate(
        TemporalValidationInput(
            ledger_indices=[100, 101, 102, 103, 104, 105],
            total_depth_xrp=[900.0, 870.0, 830.0, 790.0, 740.0, 700.0],
            simulator_latency_ledgers=1,
        )
    )
    assert out.ledger_gap_error > 0.4
    assert out.latency_mismatch_flag is True
