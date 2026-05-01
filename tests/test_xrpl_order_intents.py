from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite

from app.validation.xrpl_order_intents import (
    XRPLIntentSnapshot,
    build_order_intent,
    build_order_intents,
    summarize_order_intents,
)


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)


def test_intent_generation_is_deterministic_and_uses_stable_id() -> None:
    rec = _recommendation()
    snapshot = _snapshot()

    first = build_order_intent(recommendation=rec, snapshot=snapshot).to_dict()
    second = build_order_intent(recommendation=rec, snapshot=snapshot).to_dict()

    assert first == second
    assert first["intent_id"].startswith("intent_")
    assert first["xrpl_context"]["ledger_index"] == 500
    assert first["xrpl_context"]["validated"] is True
    assert first["is_executable"] is False


def test_unvalidated_or_gap_context_forces_avoid() -> None:
    unvalidated = build_order_intent(recommendation=_recommendation(), snapshot=_snapshot(validated=False)).to_dict()
    gap = build_order_intent(recommendation=_recommendation(), snapshot=_snapshot(recent_ledger_gap=True)).to_dict()

    assert unvalidated["action"] == "avoid"
    assert unvalidated["proposed_size"] == 0.0
    assert gap["action"] == "avoid"
    assert gap["proposed_size"] == 0.0


def test_low_liquidity_and_low_path_viability_avoid_behaviour() -> None:
    low_liquidity = build_order_intent(recommendation=_recommendation(), snapshot=_snapshot(bid_depth=2.0, ask_depth=1.0)).to_dict()
    low_path = build_order_intent(
        recommendation=_recommendation(attribution="path_instability"),
        snapshot=_snapshot(spread_pct=18.0),
    ).to_dict()

    assert low_liquidity["action"] == "avoid"
    assert low_liquidity["execution_estimates"]["liquidity_score"] < 0.20
    assert low_path["action"] == "avoid"
    assert low_path["pathfinding"]["path_required"] is True
    assert low_path["pathfinding"]["path_viability_score"] < 0.35
    assert low_liquidity["execution_feasibility"]["decision"] == "avoid"
    assert low_liquidity["liquidity_source_model"]["decision"] == "avoid"


def test_high_signal_with_low_feasibility_downgrades_to_avoid() -> None:
    body = build_order_intent(
        recommendation=_recommendation(),
        snapshot=_snapshot(bid_depth=5.0, ask_depth=4.0, spread_pct=12.0),
        requested_size=100.0,
    ).to_dict()

    assert body["action"] == "avoid"
    assert body["execution_feasibility"]["decision"] == "avoid"
    assert body["execution_feasibility"]["execution_feasibility_score"] < 0.40
    assert body["liquidity_source_model"]["liquidity_source"] in {"orderbook", "unknown"}


def test_partial_fill_model_is_bounded_and_never_assumes_full_fill() -> None:
    body = build_order_intent(recommendation=_recommendation(), snapshot=_snapshot()).to_dict()
    fill_model = body["fill_model"]

    assert 0.0 <= fill_model["min_fill_ratio"] <= fill_model["max_fill_ratio"] <= 0.95
    assert 0.0 <= fill_model["confidence_adjusted_fill"] <= 1.0
    assert 0.0 <= body["execution_estimates"]["expected_fill_ratio"] <= 0.95
    assert 0.0 <= body["execution_feasibility"]["expected_fill_ratio"] <= 1.0
    assert 0.0 <= body["liquidity_source_model"]["expected_fill_ratio"] <= 1.0
    assert _finite_json(body)


def test_duplicate_recommendation_does_not_create_duplicate_intents() -> None:
    rec = _recommendation()
    intents = build_order_intents(
        recommendations=[rec, rec],
        snapshots_by_token={7: _snapshot(token_id=7)},
    )

    assert len(intents) == 1
    summary = summarize_order_intents(intents)
    assert summary["count"] == 1
    assert summary["is_shadow"] is True
    assert summary["is_executable"] is False


def test_replay_parity_for_identical_inputs() -> None:
    recs = [_recommendation(token_id=7), _recommendation(token_id=8, recommendation_id="rec_b")]
    snapshots = {7: _snapshot(token_id=7), 8: _snapshot(token_id=8, issuer="rIssuer2")}

    first = [intent.to_dict() for intent in build_order_intents(recommendations=recs, snapshots_by_token=snapshots)]
    second = [intent.to_dict() for intent in build_order_intents(recommendations=recs, snapshots_by_token=snapshots)]

    assert first == second
    assert all(_finite_json(row) for row in first)


def _recommendation(
    *,
    token_id: int = 7,
    issuer: str = "rIssuer",
    attribution: str = "liquidity_illusion",
    recommendation_id: str = "rec_a",
) -> dict[str, object]:
    return {
        "recommendation_id": recommendation_id,
        "source_metric": "attribution_cluster",
        "scope": {"token_id": token_id, "issuer": issuer, "attribution": attribution, "regime": "STABLE_SHADOW"},
        "stability_score": 0.8,
        "consistency_score": 0.75,
        "support_size": 40,
    }


def _snapshot(
    *,
    token_id: int = 7,
    issuer: str = "rIssuer",
    bid_depth: float = 150.0,
    ask_depth: float = 90.0,
    spread_pct: float = 2.0,
    validated: bool = True,
    recent_ledger_gap: bool = False,
) -> XRPLIntentSnapshot:
    return XRPLIntentSnapshot(
        token_id=token_id,
        issuer=issuer,
        currency="USD",
        ledger_index=500,
        ledger_time=BASE,
        best_bid=0.99,
        best_ask=1.01,
        bid_depth_xrp=bid_depth,
        ask_depth_xrp=ask_depth,
        spread_pct=spread_pct,
        validated=validated,
        recent_ledger_gap=recent_ledger_gap,
        snapshot_complete=True,
    )


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
