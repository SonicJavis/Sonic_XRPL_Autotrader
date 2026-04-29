from __future__ import annotations

from math import isfinite

from app.execution.xrpl_paper_execution import XRPLPaperExecutionEngine, XRPLQualityLevel, summarize_simulations


def test_quality_level_order_consumption_uses_best_quality_first() -> None:
    result = XRPLPaperExecutionEngine().simulate(
        intent=_intent(size=80.0),
        quality_levels=[
            XRPLQualityLevel(quality=1.20, price=1.20, available_size=50.0),
            XRPLQualityLevel(quality=1.00, price=1.00, available_size=30.0),
            XRPLQualityLevel(quality=1.10, price=1.10, available_size=50.0),
        ],
    ).to_dict()

    assert result["execution_status"] == "full"
    assert result["filled_size"] == 80.0
    assert result["xrpl_execution_context"]["quality_levels_consumed"] == 2
    assert result["avg_execution_price"] == 1.0625


def test_unfunded_levels_are_skipped_and_partial_fill_is_common() -> None:
    result = XRPLPaperExecutionEngine().simulate(
        intent=_intent(size=100.0),
        quality_levels=[
            XRPLQualityLevel(quality=1.00, price=1.00, available_size=90.0, funded=False),
            XRPLQualityLevel(quality=1.10, price=1.10, available_size=40.0, funded=True),
        ],
    ).to_dict()

    assert result["execution_status"] == "partial"
    assert result["filled_size"] == 40.0
    assert result["fill_ratio"] == 0.4
    assert result["xrpl_execution_context"]["funded_liquidity_only"] is True


def test_zero_liquidity_fails_with_explicit_reason() -> None:
    result = XRPLPaperExecutionEngine().simulate(intent=_intent(size=100.0), quality_levels=[]).to_dict()

    assert result["execution_status"] == "failed"
    assert result["failure_reason"] == "liquidity"
    assert result["fill_ratio"] == 0.0


def test_pathfinding_failure_and_incomplete_snapshot_fail_closed() -> None:
    path_failed = XRPLPaperExecutionEngine().simulate(
        intent=_intent(path_required=True, path_viability=0.2),
        quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)],
    ).to_dict()
    incomplete = XRPLPaperExecutionEngine().simulate(
        intent=_intent(),
        quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)],
        snapshot_complete=False,
    ).to_dict()

    assert path_failed["execution_status"] == "failed"
    assert path_failed["failure_reason"] == "path"
    assert path_failed["pathfinding"]["path_used"] == "none"
    assert incomplete["failure_reason"] == "incomplete_snapshot"


def test_transfer_fee_reduces_fill_and_increases_slippage() -> None:
    no_fee = XRPLPaperExecutionEngine().simulate(
        intent=_intent(size=100.0),
        quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)],
        transfer_fee_bps=0,
    ).to_dict()
    fee = XRPLPaperExecutionEngine().simulate(
        intent=_intent(size=100.0),
        quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)],
        transfer_fee_bps=200,
    ).to_dict()

    assert fee["filled_size"] < no_fee["filled_size"]
    assert fee["slippage_realized"] > no_fee["slippage_realized"]
    assert fee["issuer_friction"]["transfer_fee_bps"] == 200


def test_slippage_increases_as_size_traverses_more_quality_levels() -> None:
    levels = [
        XRPLQualityLevel(quality=1.0, price=1.0, available_size=25.0),
        XRPLQualityLevel(quality=1.5, price=1.5, available_size=100.0),
    ]
    small = XRPLPaperExecutionEngine().simulate(intent=_intent(size=20.0), quality_levels=levels).to_dict()
    large = XRPLPaperExecutionEngine().simulate(intent=_intent(size=80.0), quality_levels=levels).to_dict()

    assert large["slippage_realized"] > small["slippage_realized"]
    assert large["xrpl_execution_context"]["quality_levels_consumed"] > small["xrpl_execution_context"]["quality_levels_consumed"]


def test_deterministic_replay_and_summary_are_bounded() -> None:
    engine = XRPLPaperExecutionEngine()
    first = engine.simulate(intent=_intent(), quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)]).to_dict()
    second = engine.simulate(intent=_intent(), quality_levels=[XRPLQualityLevel(quality=1.0, price=1.0, available_size=100.0)]).to_dict()
    summary = summarize_simulations([first, second])

    assert first == second
    assert first["simulation_id"].startswith("sim_")
    assert 0.0 <= summary["avg_fill_ratio"] <= 1.0
    assert 0.0 <= summary["failure_rate"] <= 1.0
    assert _finite_json(first)
    assert _finite_json(summary)


def _intent(*, size: float = 50.0, path_required: bool = False, path_viability: float = 1.0) -> dict[str, object]:
    return {
        "intent_id": "intent_test",
        "action": "buy",
        "proposed_size": size,
        "xrpl_context": {"ledger_index": 100, "validated": True},
        "execution_estimates": {"expected_price": 1.0},
        "pathfinding": {"path_required": path_required, "path_viability_score": path_viability},
    }


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
