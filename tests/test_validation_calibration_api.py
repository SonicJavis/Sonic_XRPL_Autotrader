from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient
from sqlmodel import delete, select

from app.db.models import ShadowValidationRecord
from app.main import create_app


RECOMMENDATION_FIELDS = {
    "type",
    "source_metric",
    "scope",
    "observation",
    "suggestion_direction",
    "target_component",
    "support_size",
    "consistency_score",
    "volatility_flag",
    "confidence_level",
    "rationale",
    "requires_manual_approval",
    "is_shadow",
    "is_advisory",
    "is_executable",
    "is_truth",
}


def test_calibration_recommendations_empty_state_safe() -> None:
    app = create_app()
    _clear(app)

    body = TestClient(app).get("/validation/calibration/recommendations").json()

    assert body["count"] == 0
    assert body["recommendations"] == []
    assert body["low_sample_warning"] is True
    _assert_meta(body)


def test_calibration_recommendations_populated_contract_and_repeatability() -> None:
    app = create_app()
    _clear(app)
    _seed(app, 35, attribution="liquidity_illusion", over=True, token_id=7)
    client = TestClient(app)

    first = client.get("/validation/calibration/recommendations").json()
    second = client.get("/validation/calibration/recommendations").json()

    assert first == second
    assert first["count"] > 0
    assert first["low_sample_warning"] is False
    assert set(first["recommendations"][0]) == RECOMMENDATION_FIELDS
    assert all(row["requires_manual_approval"] is True for row in first["recommendations"])
    assert all(row["is_executable"] is False and row["is_truth"] is False for row in first["recommendations"])
    assert _finite_json(first)


def test_calibration_recommendations_do_not_mutate_config_or_rows() -> None:
    app = create_app()
    _clear(app)
    _seed(app, 10, attribution="competition", over=True, token_id=2)
    before_settings = app.state.container.settings.model_dump()
    with app.state.container.session_factory() as session:
        before_count = len(session.exec(select(ShadowValidationRecord)).all())

    client = TestClient(app)
    client.get("/validation/calibration/recommendations")
    client.get("/validation/calibration/recommendations")

    assert app.state.container.settings.model_dump() == before_settings
    with app.state.container.session_factory() as session:
        after_count = len(session.exec(select(ShadowValidationRecord)).all())
    assert after_count == before_count


def test_calibration_recommendations_low_support_and_min_threshold() -> None:
    app = create_app()
    _clear(app)
    _seed(app, 5, attribution="latency", over=True, token_id=4)

    body = TestClient(app).get("/validation/calibration/recommendations?min_support=30").json()

    assert body["low_sample_warning"] is True
    assert body["recommendations"]
    assert all(row["confidence_level"] == "low" for row in body["recommendations"])


def test_calibration_recommendations_language_is_uncertainty_framed() -> None:
    app = create_app()
    _clear(app)
    _seed(app, 35, attribution="path_instability", over=True, token_id=5)

    body = TestClient(app).get("/validation/calibration/recommendations").json()
    text = str(body).lower()

    assert "manual" in text
    for phrase in _UNSAFE_PHRASES:
        assert phrase not in text


def _seed(app, count: int, *, attribution: str, token_id: int, over: bool = False, under: bool = False) -> None:
    now = datetime(2026, 4, 29, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        for idx in range(count):
            session.add(
                ShadowValidationRecord(
                    decision_id=idx + 1,
                    token_id=token_id,
                    issuer=f"rIssuer{token_id}",
                    predicted_regime="STABLE_SHADOW",
                    disagreement_score=0.35,
                    brier_score=0.30,
                    overconfidence_flag=over,
                    underconfidence_flag=under,
                    regime_mismatch=False,
                    liquidity_disappearance=0.4 if attribution == "liquidity_illusion" else 0.0,
                    path_failure_rate=0.4 if attribution == "path_instability" else 0.0,
                    competition_miss_rate=0.4 if attribution == "competition" else 0.0,
                    latency_miss=0.4 if attribution == "latency" else 0.0,
                    attribution=attribution,
                    created_at=now + timedelta(seconds=idx),
                )
            )
        session.commit()


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


_UNSAFE_PHRASES = (
    "true fill",
    "actual fill",
    "guaranteed fill",
    "guaranteed execution",
    "real execution",
    "executable truth",
    "proven executable",
    "confirmed fill",
)
