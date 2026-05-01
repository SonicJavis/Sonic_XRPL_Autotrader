from __future__ import annotations

from math import isfinite

from app.xrpl.liquidity_decay import evaluate_liquidity_decay


FEASIBILITY = {
    "schema_version": "1.0",
    "execution_feasibility_score": 0.8,
    "expected_fill_ratio": 0.75,
}
LIQUIDITY = {
    "schema_version": "1.0",
    "liquidity_source": "orderbook",
    "preferred_source": "orderbook",
    "expected_fill_ratio": 0.7,
    "amm_available": False,
}


def test_fresh_snapshot_zero_to_one_ledgers() -> None:
    result = _decay(current=101, snapshot=100)

    assert result["decision"] == "fresh"
    assert result["snapshot_age_ledgers"] == 1
    assert result["decay_factor"] > 0.85
    assert result["is_executable"] is False


def test_degraded_snapshot_uses_ledger_progression() -> None:
    result = _decay(current=104, snapshot=100)

    assert result["decision"] == "degraded"
    assert 0.0 < result["decay_factor"] < 0.85
    assert result["decayed_feasibility_score"] < FEASIBILITY["execution_feasibility_score"]


def test_stale_snapshot_after_many_ledgers() -> None:
    result = _decay(current=110, snapshot=100)

    assert result["decision"] == "stale"
    assert result["stale"] is True


def test_invalid_negative_ledger_age_fails_closed() -> None:
    result = _decay(current=99, snapshot=100)

    assert result["decision"] == "invalid"
    assert result["decay_factor"] == 0.0


def test_amm_accelerates_decay_vs_orderbook() -> None:
    orderbook = _decay(current=103, snapshot=100)
    amm = _decay(
        current=103,
        snapshot=100,
        liquidity={**LIQUIDITY, "liquidity_source": "amm", "preferred_source": "amm", "amm_available": True},
    )

    assert amm["decay_factor"] < orderbook["decay_factor"]
    assert any("AMM" in warning for warning in amm["warnings"])


def test_gap_penalty_invalidates_at_threshold() -> None:
    result = _decay(current=101, snapshot=100, recent_gap_count=3)

    assert result["decision"] == "invalid"
    assert result["decayed_fill_confidence"] == 0.0


def test_latency_penalty_only_reduces_confidence() -> None:
    normal = _decay(current=101, snapshot=100, recent_latency_ms=1000.0)
    delayed = _decay(current=101, snapshot=100, recent_latency_ms=9000.0)

    assert delayed["decay_factor"] < normal["decay_factor"]
    assert delayed["decision"] in {"degraded", "stale"}


def test_duplicates_are_diagnostic_only() -> None:
    normal = _decay(current=102, snapshot=100)
    duplicate = _decay(current=102, snapshot=100, recent_duplicate_count=10)

    assert duplicate["decay_factor"] == normal["decay_factor"]
    assert any("duplicate" in warning for warning in duplicate["warnings"])


def test_deterministic_and_bounded_outputs() -> None:
    first = _decay(current=106, snapshot=100, recent_gap_count=1, recent_latency_ms=7000.0)
    second = _decay(current=106, snapshot=100, recent_gap_count=1, recent_latency_ms=7000.0)

    assert first == second
    assert _finite_json(first)
    for key in ("staleness_score", "decay_factor", "decayed_feasibility_score", "decayed_fill_confidence"):
        assert 0.0 <= first[key] <= 1.0


def test_missing_context_invalidates() -> None:
    result = evaluate_liquidity_decay(
        snapshot_ledger_index=100,
        snapshot_ledger_time=None,
        current_ledger_index=100,
        current_ledger_time=None,
        processing_time=None,
        execution_feasibility={},
        liquidity_source_model=LIQUIDITY,
    )

    assert result["decision"] == "invalid"


def _decay(
    *,
    current: int,
    snapshot: int,
    liquidity: dict[str, object] | None = None,
    recent_gap_count: int = 0,
    recent_duplicate_count: int = 0,
    recent_latency_ms: float | None = None,
) -> dict[str, object]:
    return evaluate_liquidity_decay(
        snapshot_ledger_index=snapshot,
        snapshot_ledger_time=1_800_000_000,
        current_ledger_index=current,
        current_ledger_time=1_800_000_000 + (current - snapshot) * 4,
        processing_time=None,
        execution_feasibility=FEASIBILITY,
        liquidity_source_model=LIQUIDITY if liquidity is None else liquidity,
        recent_gap_count=recent_gap_count,
        recent_duplicate_count=recent_duplicate_count,
        recent_latency_ms=recent_latency_ms,
    )


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
