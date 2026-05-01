from __future__ import annotations

from math import inf, isfinite

from app.xrpl.execution_feasibility import evaluate_execution_feasibility
from app.xrpl.liquidity_source_model import evaluate_liquidity_sources
from app.xrpl.orderbook_normalizer import normalize_book_offers
from app.xrpl.pathfinding_model import evaluate_pathfinding_uncertainty


USD = {"currency": "USD", "issuer": "rUsd"}
EUR = {"currency": "EUR", "issuer": "rEur"}


def test_orderbook_only_source() -> None:
    book, path, feasibility = _orderbook_context(100.0)

    result = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
        execution_feasibility=feasibility,
    )

    assert result["liquidity_source"] == "orderbook"
    assert result["preferred_source"] == "orderbook"
    assert result["orderbook_available"] is True
    assert result["amm_available"] is False
    assert result["hybrid_possible"] is False
    assert result["decision"] in {"usable", "marginal"}
    assert result["is_executable"] is False


def test_amm_only_source() -> None:
    result = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=10.0,
        normalized_orderbooks=[],
        pathfinding_result={},
        execution_feasibility={"execution_feasibility_score": 0.0, "decision": "avoid", "route_type": "none"},
        amm_snapshot=_amm(1000.0, 1000.0),
    )

    assert result["liquidity_source"] == "amm"
    assert result["preferred_source"] == "amm"
    assert result["amm_available"] is True
    assert result["amm_score"] > 0.0


def test_hybrid_detection_and_score() -> None:
    book, path, feasibility = _orderbook_context(100.0)
    result = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=25.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
        execution_feasibility=feasibility,
        amm_snapshot=_amm(2000.0, 2000.0),
    )

    assert result["liquidity_source"] == "hybrid"
    assert result["hybrid_possible"] is True
    assert result["hybrid_score"] == max(result["orderbook_score"], result["amm_score"])
    assert "HYBRID_POSSIBLE_NOT_OPTIMIZED" in result["liquidity_warnings"]


def test_high_amm_price_impact_avoids_when_only_source() -> None:
    result = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=90.0,
        normalized_orderbooks=[],
        pathfinding_result={},
        execution_feasibility={"execution_feasibility_score": 0.0, "decision": "avoid", "route_type": "none"},
        amm_snapshot=_amm(100.0, 100.0),
    )

    assert result["liquidity_source"] == "unknown"
    assert result["decision"] == "avoid"
    assert "AMM_PRICE_IMPACT_TOO_HIGH" in result["liquidity_warnings"]


def test_shallow_amm_pool_is_penalized() -> None:
    deep = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=10.0,
        normalized_orderbooks=[],
        pathfinding_result={},
        execution_feasibility={"execution_feasibility_score": 0.0, "decision": "avoid", "route_type": "none"},
        amm_snapshot=_amm(2000.0, 2000.0),
    )
    shallow = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=10.0,
        normalized_orderbooks=[],
        pathfinding_result={},
        execution_feasibility={"execution_feasibility_score": 0.0, "decision": "avoid", "route_type": "none"},
        amm_snapshot=_amm(50.0, 50.0),
    )

    assert shallow["amm_score"] < deep["amm_score"]
    assert shallow["expected_price_impact"] > deep["expected_price_impact"]


def test_malformed_amm_fails_closed() -> None:
    result = evaluate_liquidity_sources(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=10.0,
        normalized_orderbooks=[],
        pathfinding_result={},
        execution_feasibility={},
        amm_snapshot={"asset1": USD, "asset2": EUR, "reserve1": inf, "reserve2": 0.0, "trading_fee": 0.003},
    )

    assert result["decision"] == "avoid"
    assert result["amm_available"] is False
    assert _finite_json(result)


def test_deterministic_and_bounded_output() -> None:
    book, path, feasibility = _orderbook_context(120.0)
    args = dict(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=40.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
        execution_feasibility=feasibility,
        amm_snapshot=_amm(1000.0, 900.0),
    )

    first = evaluate_liquidity_sources(**args)
    second = evaluate_liquidity_sources(**args)

    assert first == second
    assert _finite_json(first)
    for key in ("orderbook_score", "amm_score", "hybrid_score", "expected_price_impact", "expected_fill_ratio", "amm_price_impact", "amm_fill_ratio"):
        assert 0.0 <= first[key] <= 1.0


def _orderbook_context(depth: float) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    book = normalize_book_offers(
        [{"TakerGets": _amount(USD, depth), "TakerPays": _amount(EUR, depth), "owner": "rOwner"}]
    )
    path = evaluate_pathfinding_uncertainty([book], USD, EUR, 50.0)
    feasibility = evaluate_execution_feasibility(
        source_asset=USD,
        destination_asset=EUR,
        requested_size=50.0,
        normalized_orderbooks=[book],
        pathfinding_result=path,
    )
    return book, path, feasibility


def _amm(reserve1: float, reserve2: float) -> dict[str, object]:
    return {"asset1": USD, "asset2": EUR, "reserve1": reserve1, "reserve2": reserve2, "trading_fee": 0.003}


def _amount(asset: dict[str, str], value: float) -> object:
    return {"currency": asset["currency"], "issuer": asset["issuer"], "value": str(value)}


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
