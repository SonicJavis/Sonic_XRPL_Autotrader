from __future__ import annotations

from math import inf, isfinite, nan

from app.xrpl.execution_feasibility import evaluate_execution_feasibility
from app.xrpl.orderbook_normalizer import normalize_book_offers
from app.xrpl.pathfinding_model import evaluate_pathfinding_uncertainty


USD = {"currency": "USD", "issuer": "rUsd"}
EUR = {"currency": "EUR", "issuer": "rEur"}
ABC = {"currency": "ABC", "issuer": "rAbc"}
XRP = {"currency": "XRP", "issuer": None}


def test_feasible_direct_path() -> None:
    book = _book(USD, EUR, [(140.0, 140.0)])
    path = evaluate_pathfinding_uncertainty([book], USD, EUR, 50.0)

    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
        signal_strength=0.9,
    )

    assert result["decision"] == "feasible"
    assert result["route_type"] == "direct"
    assert result["execution_feasibility_score"] >= 0.70
    assert result["expected_fill_ratio"] >= 0.80
    assert result["confidence_adjusted_signal"] is not None
    assert result["is_executable"] is False


def test_marginal_xrp_bridge_path() -> None:
    first = _book(USD, "XRP", [(100.0, 100.0)])
    second = _book("XRP", EUR, [(100.0, 92.0)])
    path = evaluate_pathfinding_uncertainty([first, second], USD, EUR, 50.0)

    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[first, second],
        pathfinding_result=path,
    )

    assert result["route_type"] == "xrp_bridge"
    assert result["decision"] in {"marginal", "avoid"}
    assert result["path_reliability_score"] <= path["path_viability_score"]


def test_avoid_no_path() -> None:
    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[],
        pathfinding_result=evaluate_pathfinding_uncertainty([], USD, EUR, 50.0),
    )

    assert result["decision"] == "avoid"
    assert result["execution_feasibility_score"] == 0.0
    assert result["route_type"] == "none"
    assert "NO_PATH_AVAILABLE" in result["failure_modes"]


def test_avoid_insufficient_weakest_hop_capacity() -> None:
    first = _book(USD, "XRP", [(100.0, 100.0)])
    second = _book("XRP", EUR, [(10.0, 9.0)])
    path = evaluate_pathfinding_uncertainty([first, second], USD, EUR, 50.0)
    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[first, second],
        pathfinding_result=path,
    )

    assert result["decision"] == "avoid"
    assert result["weakest_hop_capacity"] == 10.0
    assert "INSUFFICIENT_CAPACITY_FOR_SIZE" in result["failure_modes"]


def test_avoid_high_slippage() -> None:
    book = _book(USD, EUR, [(5.0, 5.0), (50.0, 80.0)])
    path = evaluate_pathfinding_uncertainty([book], USD, EUR, 50.0)
    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
    )

    assert result["decision"] == "avoid"
    assert result["slippage_risk_score"] > 0.0
    assert "EXTREME_SLIPPAGE" in result["failure_modes"]


def test_malformed_and_non_finite_input_fails_closed() -> None:
    result = evaluate_execution_feasibility(
        source_asset={"currency": "", "issuer": None},
        destination_asset=EUR,
        requested_size=nan,
        normalized_orderbooks=[],
        pathfinding_result={"path_capacity": inf},
    )

    assert result["decision"] == "avoid"
    assert result["avoid_reason"] == "malformed_input"
    assert _finite_json(result)


def test_deep_book_with_no_route_still_avoids() -> None:
    book = _book(USD, EUR, [(500.0, 500.0)])
    result = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[book],
        pathfinding_result=evaluate_pathfinding_uncertainty([], USD, EUR, 50.0),
    )

    assert result["decision"] == "avoid"
    assert result["execution_feasibility_score"] == 0.0


def test_multi_hop_penalized_against_direct() -> None:
    direct = _book(USD, EUR, [(150.0, 150.0)])
    first = _book(USD, ABC, [(150.0, 150.0)])
    second = _book(ABC, EUR, [(150.0, 150.0)])
    direct_path = evaluate_pathfinding_uncertainty([direct], USD, EUR, 50.0)
    multi_path = evaluate_pathfinding_uncertainty([first, second], USD, EUR, 50.0, intermediate_assets=[ABC])

    direct_result = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=50.0, normalized_orderbooks=[direct], pathfinding_result=direct_path)
    multi_result = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=50.0, normalized_orderbooks=[first, second], pathfinding_result=multi_path)

    assert multi_result["execution_feasibility_score"] < direct_result["execution_feasibility_score"]
    assert multi_result["route_type"] == "multi_hop"


def test_fragility_and_fragmentation_reduce_feasibility() -> None:
    smooth = _book(USD, EUR, [(200.0, 200.0)])
    fragmented = _book(USD, EUR, [(5.0, 5.0), (5.0, 4.8), (5.0, 4.4), (90.0, 60.0)])
    smooth_path = evaluate_pathfinding_uncertainty([smooth], USD, EUR, 50.0)
    fragmented_path = evaluate_pathfinding_uncertainty([fragmented], USD, EUR, 50.0)

    smooth_result = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=50.0, normalized_orderbooks=[smooth], pathfinding_result=smooth_path)
    fragmented_result = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=50.0, normalized_orderbooks=[fragmented], pathfinding_result=fragmented_path)

    assert fragmented_result["fragmentation_risk_score"] > smooth_result["fragmentation_risk_score"]
    assert fragmented_result["execution_feasibility_score"] < smooth_result["execution_feasibility_score"]


def test_deterministic_and_bounded_output() -> None:
    book = _book(USD, EUR, [(100.0, 100.0), (25.0, 24.0)])
    path = evaluate_pathfinding_uncertainty([book], USD, EUR, 75.0)
    first = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=75.0, normalized_orderbooks=[book], pathfinding_result=path)
    second = evaluate_execution_feasibility(source_asset=USD, destination_asset=EUR, requested_size=75.0, normalized_orderbooks=[book], pathfinding_result=path)

    assert first == second
    assert _finite_json(first)
    for key in (
        "liquidity_score",
        "path_reliability_score",
        "fill_confidence_score",
        "slippage_risk_score",
        "fragility_risk_score",
        "fragmentation_risk_score",
        "execution_feasibility_score",
        "expected_fill_ratio",
    ):
        assert 0.0 <= first[key] <= 1.0


def _book(source: dict[str, str] | str, destination: dict[str, str] | str, levels: list[tuple[float, float]]) -> dict[str, object]:
    return normalize_book_offers(
        [
            {
                "TakerGets": _amount(source, source_amount),
                "TakerPays": _amount(destination, destination_amount),
                "owner": f"rOwner{idx}",
            }
            for idx, (source_amount, destination_amount) in enumerate(levels)
        ]
    )


def _amount(asset: dict[str, str] | str, value: float) -> object:
    if asset == "XRP":
        return str(int(value * 1_000_000))
    return {"currency": asset["currency"], "issuer": asset["issuer"], "value": str(value)}


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
