from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ShadowValidationRecord
from app.main import create_app


SUMMARY_FIELDS = {
    "is_shadow",
    "is_advisory",
    "is_executable",
    "is_truth",
    "xrpl_warning",
    "limit",
    "sample_count",
    "avg_disagreement_score",
    "avg_brier_score",
    "overconfidence_rate",
    "underconfidence_rate",
    "attribution_breakdown",
    "worst_regimes",
    "worst_tokens",
}

RESULT_FIELDS = {
    "id",
    "decision_id",
    "token_id",
    "issuer",
    "predicted_regime",
    "fill_probability_error",
    "effective_size_error",
    "ev_error",
    "liquidity_disappearance",
    "path_failure_rate",
    "competition_miss_rate",
    "latency_miss",
    "regime_mismatch",
    "disagreement_score",
    "brier_score",
    "overconfidence_flag",
    "underconfidence_flag",
    "confidence_error",
    "attribution",
    "created_at",
    "is_shadow",
    "is_advisory",
    "is_executable",
    "is_truth",
}


def test_shadow_validation_api_contract_empty_and_limit_bounds() -> None:
    app = create_app()
    _clear(app)
    client = TestClient(app)

    summary_zero = client.get("/validation/shadow/summary?limit=0").json()
    summary_negative = client.get("/validation/shadow/summary?limit=-10").json()
    results_cap = client.get("/validation/shadow/results?limit=999999").json()

    assert set(summary_zero) == SUMMARY_FIELDS
    assert summary_zero["limit"] == 1
    assert summary_negative["limit"] == 1
    assert results_cap["limit"] == 5000
    assert results_cap["results"] == []
    _assert_meta(summary_zero)
    _assert_meta(results_cap)


def test_shadow_validation_api_contract_populated_sorting_and_idempotence() -> None:
    app = create_app()
    _clear(app)
    now = datetime(2026, 4, 29, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        session.add(_record(1, 10, now, disagreement_score=0.2, attribution="latency"))
        session.add(_record(2, 20, now + timedelta(seconds=1), disagreement_score=0.6, attribution="competition"))
        session.commit()
    client = TestClient(app)

    first = client.get("/validation/shadow/results?limit=10").json()
    second = client.get("/validation/shadow/results?limit=10").json()
    summary = client.get("/validation/shadow/summary?limit=10").json()

    assert first == second
    assert first["count"] == 2
    assert [row["decision_id"] for row in first["results"]] == [2, 1]
    assert set(first["results"][0]) == RESULT_FIELDS
    assert summary["attribution_breakdown"] == {"competition": 1, "latency": 1}
    assert list(summary["attribution_breakdown"]) == ["competition", "latency"]
    assert _finite_json(first)
    assert _finite_json(summary)


def _record(decision_id: int, token_id: int, created_at: datetime, *, disagreement_score: float, attribution: str) -> ShadowValidationRecord:
    return ShadowValidationRecord(
        decision_id=decision_id,
        token_id=token_id,
        issuer=f"r{token_id}",
        predicted_regime="STABLE_SHADOW",
        fill_probability_error=0.1,
        effective_size_error=0.1,
        ev_error=0.1,
        liquidity_disappearance=0.1,
        path_failure_rate=0.1,
        competition_miss_rate=0.1,
        latency_miss=0.1,
        disagreement_score=disagreement_score,
        brier_score=0.1,
        confidence_error=0.1,
        attribution=attribution,
        created_at=created_at,
    )


def _clear(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowValidationRecord))
        session.commit()


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert body["is_truth"] is False
    assert "xrpl_warning" in body


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
