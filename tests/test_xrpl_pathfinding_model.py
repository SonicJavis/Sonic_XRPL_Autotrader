from app.xrpl.orderbook_normalizer import normalize_book_offers
from app.xrpl.pathfinding_model import evaluate_pathfinding_uncertainty


USD = {"currency": "USD", "issuer": "rUsd"}
EUR = {"currency": "EUR", "issuer": "rEur"}
ABC = {"currency": "ABC", "issuer": "rAbc"}


def _book(source: dict[str, str] | str, destination: dict[str, str] | str, levels: list[tuple[float, float]]) -> dict[str, object]:
    offers = []
    for idx, (source_amount, destination_amount) in enumerate(levels):
        offers.append(
            {
                "TakerGets": _amount(source, source_amount),
                "TakerPays": _amount(destination, destination_amount),
                "owner": f"rOwner{idx}",
            }
        )
    return normalize_book_offers(offers)


def _amount(asset: dict[str, str] | str, value: float) -> object:
    if asset == "XRP":
        return str(int(value * 1_000_000))
    return {"currency": asset["currency"], "issuer": asset["issuer"], "value": str(value)}


def test_direct_path_full_liquidity_scores_highest_without_path_required() -> None:
    direct = _book(USD, EUR, [(50.0, 50.0), (50.0, 49.0)])

    result = evaluate_pathfinding_uncertainty([direct], USD, EUR, 40.0)

    assert result["direct_liquidity_available"] is True
    assert result["bridge_available"] is False
    assert result["path_required"] is False
    assert result["estimated_hops"] == 1
    assert result["path_capacity"] == 100.0
    assert result["path_viability_score"] > 0.75
    assert result["is_shadow"] is True
    assert result["is_advisory"] is True
    assert result["is_executable"] is False


def test_xrp_bridge_path_is_selected_when_direct_missing() -> None:
    usd_to_xrp = _book(USD, "XRP", [(100.0, 100.0)])
    xrp_to_eur = _book("XRP", EUR, [(100.0, 95.0)])

    result = evaluate_pathfinding_uncertainty([usd_to_xrp, xrp_to_eur], USD, EUR, 50.0)

    assert result["direct_liquidity_available"] is False
    assert result["bridge_available"] is True
    assert result["path_required"] is True
    assert result["estimated_hops"] == 2
    assert result["selected_path"] == "xrp_bridge"
    assert result["path_viability_score"] > 0.4


def test_no_path_scenario_fails_closed() -> None:
    result = evaluate_pathfinding_uncertainty([], USD, EUR, 50.0)

    assert result["selected_path"] == "none"
    assert result["estimated_hops"] == 0
    assert result["path_capacity"] == 0.0
    assert result["path_viability_score"] == 0.0
    assert result["uncertainty_score"] == 1.0
    assert "NO_PATH_AVAILABLE" in result["failure_modes"]


def test_weakest_hop_limits_bridge_capacity() -> None:
    usd_to_xrp = _book(USD, "XRP", [(100.0, 100.0)])
    xrp_to_eur = _book("XRP", EUR, [(10.0, 9.0)])

    result = evaluate_pathfinding_uncertainty([usd_to_xrp, xrp_to_eur], USD, EUR, 50.0)

    assert result["path_capacity"] == 10.0
    assert "INSUFFICIENT_CAPACITY_FOR_SIZE" in result["failure_modes"]
    assert "WEAKEST_HOP_BOTTLENECK" in result["failure_modes"]


def test_fragmentation_penalty_increases_for_many_uneven_levels() -> None:
    smooth = _book(USD, EUR, [(100.0, 100.0)])
    fragmented = _book(USD, EUR, [(5.0, 5.0), (5.0, 4.8), (5.0, 4.4), (85.0, 55.0)])

    smooth_result = evaluate_pathfinding_uncertainty([smooth], USD, EUR, 10.0)
    fragmented_result = evaluate_pathfinding_uncertainty([fragmented], USD, EUR, 10.0)

    assert fragmented_result["liquidity_fragmentation_score"] > smooth_result["liquidity_fragmentation_score"]
    assert fragmented_result["path_viability_score"] < smooth_result["path_viability_score"]


def test_fragility_sensitivity_penalizes_near_capacity_size() -> None:
    robust = _book(USD, EUR, [(200.0, 200.0)])
    fragile = _book(USD, EUR, [(100.0, 100.0)])

    robust_result = evaluate_pathfinding_uncertainty([robust], USD, EUR, 98.0)
    fragile_result = evaluate_pathfinding_uncertainty([fragile], USD, EUR, 98.0)

    assert fragile_result["liquidity_fragility_score"] > robust_result["liquidity_fragility_score"]
    assert fragile_result["uncertainty_score"] > robust_result["uncertainty_score"]


def test_limited_multi_hop_requires_explicit_intermediate_asset() -> None:
    usd_to_abc = _book(USD, ABC, [(100.0, 100.0)])
    abc_to_eur = _book(ABC, EUR, [(100.0, 90.0)])

    result = evaluate_pathfinding_uncertainty([usd_to_abc, abc_to_eur], USD, EUR, 25.0, intermediate_assets=[ABC])

    assert result["multi_hop_possible"] is True
    assert result["selected_path"] == "multi_hop:ABC"
    assert result["estimated_hops"] == 2


def test_deterministic_outputs_for_identical_inputs() -> None:
    books = [
        _book(USD, "XRP", [(100.0, 100.0), (25.0, 20.0)]),
        _book("XRP", EUR, [(100.0, 95.0), (25.0, 20.0)]),
    ]

    first = evaluate_pathfinding_uncertainty(books, USD, EUR, 75.0)
    second = evaluate_pathfinding_uncertainty(books, USD, EUR, 75.0)

    assert first == second
