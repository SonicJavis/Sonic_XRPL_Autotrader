from app.validation.execution_bounds import ExecutionBoundsInput, ExecutionBoundsModel


def test_thin_books_produce_wide_bounds() -> None:
    out = ExecutionBoundsModel().compute(
        data=ExecutionBoundsInput(
            total_visible_depth_xrp=120.0,
            requested_size_xrp=1000.0,
            depth_uncertainty=0.7,
            fundedness_uncertainty=0.7,
            decay_rate=0.6,
            regime="THIN",
        ),
        simulator_fill_size_xrp=90.0,
    )
    assert out.max_possible_fill - out.min_executable_size > 40.0


def test_stable_books_produce_tighter_bounds() -> None:
    out = ExecutionBoundsModel().compute(
        data=ExecutionBoundsInput(
            total_visible_depth_xrp=1300.0,
            requested_size_xrp=1000.0,
            depth_uncertainty=0.15,
            fundedness_uncertainty=0.2,
            decay_rate=0.1,
            regime="STABLE",
        ),
        simulator_fill_size_xrp=850.0,
    )
    assert out.max_possible_fill - out.min_executable_size < 280.0


def test_spoofy_books_produce_very_wide_bounds() -> None:
    out = ExecutionBoundsModel().compute(
        data=ExecutionBoundsInput(
            total_visible_depth_xrp=1400.0,
            requested_size_xrp=1000.0,
            depth_uncertainty=0.5,
            fundedness_uncertainty=0.8,
            decay_rate=0.6,
            regime="SPOOFY",
        ),
        simulator_fill_size_xrp=950.0,
    )
    assert out.max_possible_fill - out.min_executable_size > 350.0
    assert out.simulator_within_bounds is False
