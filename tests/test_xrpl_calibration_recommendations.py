from datetime import datetime, timedelta, timezone
from math import isfinite

from app.db.models import ShadowValidationRecord
from app.validation.xrpl_calibration_recommendations import (
    RECOMMENDATION_SCHEMA_VERSION,
    XRPLCalibrationRecommendationEngine,
    compute_recommendation_id,
    stable_recommendation_json,
    validate_recommendation_payload,
)


def _record(
    idx: int,
    *,
    attribution: str = "liquidity_illusion",
    regime: str = "STABLE_SHADOW",
    token_id: int = 1,
    issuer: str | None = None,
    disagreement: float = 0.4,
    brier: float = 0.3,
    over: bool = False,
    under: bool = False,
    mismatch: bool = False,
) -> ShadowValidationRecord:
    return ShadowValidationRecord(
        decision_id=idx,
        token_id=token_id,
        issuer=issuer or f"rIssuer{token_id}",
        predicted_regime=regime,
        disagreement_score=disagreement,
        brier_score=brier,
        overconfidence_flag=over,
        underconfidence_flag=under,
        regime_mismatch=mismatch,
        liquidity_disappearance=0.3 if attribution == "liquidity_illusion" else 0.0,
        path_failure_rate=0.3 if attribution == "path_instability" else 0.0,
        competition_miss_rate=0.3 if attribution == "competition" else 0.0,
        latency_miss=0.3 if attribution == "latency" else 0.0,
        attribution=attribution,
        created_at=datetime(2026, 4, 29, tzinfo=timezone.utc) + timedelta(seconds=idx),
    )


def test_empty_validation_set_returns_no_recommendations() -> None:
    assert XRPLCalibrationRecommendationEngine().generate([], min_support=30) == []


def test_low_sample_recommendations_are_low_confidence_and_manual_review_only() -> None:
    recs = XRPLCalibrationRecommendationEngine().generate([_record(1, over=True)], min_support=30)

    assert recs
    assert all(row.confidence_level == "low" for row in recs)
    assert all(row.recommendation_strength == "weak" for row in recs)
    assert all(row.low_sample_warning for row in recs)
    assert all(row.requires_manual_approval for row in recs)
    assert all(row.is_shadow and row.is_advisory and not row.is_executable and not row.is_truth for row in recs)


def test_overconfidence_underconfidence_and_attribution_clusters_emit_multiple_recs() -> None:
    rows = [_record(i, over=i < 20, under=i >= 20, attribution="competition", token_id=3) for i in range(40)]

    body = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate(rows, min_support=30)]
    metrics = {row["source_metric"] for row in body}
    directions = {row["suggestion_direction"] for row in body}

    assert "overconfidence_rate" in metrics
    assert any("underconfidence" in row["observation"] for row in body)
    assert "attribution_cluster" in metrics
    assert {"increase", "decrease"} <= directions
    assert all(row["target_component"] in {"confidence", "penalty", "regime classifier", "weighting"} for row in body)


def test_high_brier_and_regime_asymmetry_are_interpretable() -> None:
    rows = [_record(i, attribution="regime_shift", regime="DRIFT_RISK", mismatch=True, brier=0.45) for i in range(35)]

    body = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate(rows, min_support=30)]

    assert any(row["source_metric"] == "brier_score" for row in body)
    assert any(row["target_component"] == "regime classifier" for row in body)
    assert all(_finite_json(row) for row in body)


def test_high_volatility_suppresses_strong_direction() -> None:
    rows = [
        _record(i, over=True, attribution="latency", disagreement=(0.0 if i % 2 == 0 else 1.0), brier=(0.0 if i % 2 == 0 else 1.0))
        for i in range(40)
    ]

    body = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate(rows, min_support=30)]

    assert any(row["volatility_flag"] for row in body)
    assert any(row["high_variance_flag"] for row in body)
    assert all(row["recommendation_strength"] == "weak" for row in body)
    assert all(row["confidence_level"] == "low" for row in body)
    assert all(row["suggestion_direction"] == "review" for row in body)


def test_deterministic_generation_for_identical_inputs() -> None:
    rows = [_record(i, attribution="path_instability", token_id=9, over=True) for i in range(35)]
    engine = XRPLCalibrationRecommendationEngine()

    assert [row.to_dict() for row in engine.generate(rows)] == [row.to_dict() for row in engine.generate(list(rows))]
    assert engine.serialize(rows) == stable_recommendation_json(engine.generate(list(reversed(rows))))


def test_strict_schema_rejects_unknown_fields() -> None:
    row = XRPLCalibrationRecommendationEngine().generate([_record(i, over=True) for i in range(35)])[0].to_dict()

    assert row["schema_version"] == RECOMMENDATION_SCHEMA_VERSION
    assert row["recommendation_id"] == compute_recommendation_id(row)
    validate_recommendation_payload(row)
    row["unexpected"] = "blocked"
    try:
        validate_recommendation_payload(row)
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("unknown fields must be rejected")


def test_recommendations_never_cross_token_or_issuer_scope() -> None:
    rows = [
        *[_record(i, token_id=1, issuer="rIssuerA", attribution="latency", over=True) for i in range(35)],
        *[_record(i + 100, token_id=1, issuer="rIssuerB", attribution="competition", under=True) for i in range(35)],
        *[_record(i + 200, token_id=2, issuer="rIssuerA", attribution="path_instability", over=True) for i in range(35)],
    ]

    body = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate(list(reversed(rows)), min_support=30)]

    scopes = [row["scope"] for row in body]
    assert all("token_id" in scope and "issuer" in scope for scope in scopes)
    assert {"token_id": 1, "issuer": "rIssuerA", "attribution": "competition"} not in scopes
    assert {"token_id": 1, "issuer": "rIssuerB", "attribution": "latency"} not in scopes


def test_recommendation_id_is_stable_across_replay_order() -> None:
    rows = [_record(i, token_id=8, attribution="competition", over=True) for i in range(40)]
    engine = XRPLCalibrationRecommendationEngine()

    first = [row.to_dict()["recommendation_id"] for row in engine.generate(rows, min_support=30)]
    second = [row.to_dict()["recommendation_id"] for row in engine.generate(list(reversed(rows)), min_support=30)]

    assert first == second
    assert all(str(item).startswith("rec_") for item in first)


def test_strong_strength_requires_support_and_stability() -> None:
    rows = [_record(i, token_id=4, attribution="liquidity_illusion", over=True, disagreement=0.2, brier=0.2) for i in range(70)]

    body = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate(rows, min_support=30)]

    assert any(row["recommendation_strength"] == "strong" for row in body)
    assert all(0.0 <= row["stability_score"] <= 1.0 for row in body)
    assert all(0.0 <= row["sample_decay_weight"] <= 1.0 for row in body)


def test_recommendation_language_avoids_unsafe_certainty() -> None:
    payload = [row.to_dict() for row in XRPLCalibrationRecommendationEngine().generate([_record(i, over=True) for i in range(35)])]
    text = " ".join(f"{row['observation']} {row['rationale']}" for row in payload).lower()
    for phrase in _UNSAFE_PHRASES:
        assert phrase not in text
    for phrase in ("observed disagreement", "probabilistic outcome", "uncertainty", "suggested review"):
        assert phrase in text


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True


_UNSAFE_PHRASES = (
    "accurate",
    "actual",
    "confirmed",
    "correct",
    "true fill",
    "actual fill",
    "real",
    "true",
    "guaranteed fill",
    "guaranteed execution",
    "real execution",
    "executable truth",
    "proven executable",
    "confirmed fill",
)
