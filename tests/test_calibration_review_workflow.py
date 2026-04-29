from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient
from sqlmodel import delete, select

from app.db.models import CalibrationReviewRecord, ShadowValidationRecord
from app.main import create_app


def test_review_logging_is_append_only_and_non_mutating() -> None:
    app = create_app()
    _clear(app)
    _seed_validation(app, 35)
    client = TestClient(app)
    recommendation_before = client.get("/validation/calibration/recommendations").json()["recommendations"][0]
    settings_before = app.state.container.settings.model_dump()

    first = client.post(
        "/validation/calibration/review",
        json=_review_payload(recommendation_before, decision="accepted", reviewed_at="2026-04-29T12:00:00+00:00"),
    )
    second = client.post(
        "/validation/calibration/review",
        json=_review_payload(recommendation_before, decision="deferred", reviewed_at="2026-04-29T12:01:00+00:00"),
    )
    recommendation_after = client.get("/validation/calibration/recommendations").json()["recommendations"][0]
    reviews = client.get("/validation/calibration/reviews").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert recommendation_after == recommendation_before
    assert app.state.container.settings.model_dump() == settings_before
    assert reviews["count"] == 2
    assert [row["decision"] for row in reviews["reviews"]] == ["deferred", "accepted"]
    assert all(row["is_shadow"] and row["is_advisory"] and not row["is_executable"] and not row["is_truth"] for row in reviews["reviews"])
    with app.state.container.session_factory() as session:
        assert len(session.exec(select(CalibrationReviewRecord)).all()) == 2


def test_review_filters_and_strict_payload_validation() -> None:
    app = create_app()
    _clear(app)
    _seed_validation(app, 35, token_id=9, issuer="rIssuer9", attribution="latency")
    client = TestClient(app)
    recommendations = client.get("/validation/calibration/recommendations").json()["recommendations"]
    recommendation = next(row for row in recommendations if row["scope"].get("attribution") == "latency")
    response = client.post(
        "/validation/calibration/review",
        json=_review_payload(recommendation, decision="noted", reviewed_at="2026-04-29T12:00:00+00:00"),
    )
    assert response.status_code == 200

    by_decision = client.get("/validation/calibration/reviews?decision=noted").json()
    by_token = client.get("/validation/calibration/reviews?token_id=9&issuer=rIssuer9&attribution=latency").json()
    bad_extra = client.post(
        "/validation/calibration/review",
        json={**_review_payload(recommendation, decision="noted", reviewed_at="2026-04-29T12:00:00+00:00"), "unexpected": True},
    )
    bad_decision = client.post(
        "/validation/calibration/review",
        json=_review_payload(recommendation, decision="approved", reviewed_at="2026-04-29T12:00:00+00:00"),
    )

    assert by_decision["count"] == 1
    assert by_token["count"] >= 1
    assert by_token["reviews"][0]["recommendation_id"] == recommendation["recommendation_id"]
    assert bad_extra.status_code == 422
    assert bad_decision.status_code == 400


def test_no_review_update_or_delete_endpoints_exist() -> None:
    app = create_app()

    blocked_methods = set()
    for route in app.routes:
        if getattr(route, "path", "").startswith("/validation/calibration/review"):
            blocked_methods.update(method for method in getattr(route, "methods", set()) if method in {"DELETE", "PATCH", "PUT"})

    assert blocked_methods == set()


def test_deterministic_export_and_csv_contract() -> None:
    app = create_app()
    _clear(app)
    _seed_validation(app, 35)
    client = TestClient(app)
    recommendation = client.get("/validation/calibration/recommendations").json()["recommendations"][0]
    client.post(
        "/validation/calibration/review",
        json=_review_payload(recommendation, decision="rejected", reviewed_at="2026-04-29T12:00:00+00:00"),
    )

    first = client.get("/validation/calibration/export?deterministic=true").json()
    second = client.get("/validation/calibration/export?deterministic=true").json()

    assert first == second
    assert first["export_schema_version"] == "1.0"
    assert first["source_schema_version"] == "1.0"
    assert first["export_hash"].startswith("export_")
    assert first["csv_review_summary"].splitlines()[0] == (
        "review_id,recommendation_id,schema_version,decision,reviewer_id,reviewed_at,token_id,issuer,attribution,regime"
    )
    assert first["snapshot_bundle"]["review_count"] == 1
    assert first["snapshot_bundle"]["integrity"]["orphan_review_ids"] == []
    assert _finite_json(first)


def test_orphan_review_is_reported_without_mutation() -> None:
    app = create_app()
    _clear(app)
    with app.state.container.session_factory() as session:
        session.add(
            CalibrationReviewRecord(
                recommendation_id="rec_orphan",
                recommendation_snapshot_json=json.dumps({"scope": {"token_id": 99, "issuer": "rOrphan"}}),
                schema_version="1.0",
                decision="noted",
                review_notes="manual consideration only",
                reviewed_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
            )
        )
        session.commit()

    body = TestClient(app).get("/validation/calibration/export?deterministic=true").json()

    assert body["snapshot_bundle"]["integrity"]["orphan_review_ids"] == ["review_000000000001"]
    assert body["snapshot_bundle"]["integrity"]["append_only_sequence_valid"] is True


def test_duplicate_review_detection_is_reported() -> None:
    app = create_app()
    _clear(app)
    _seed_validation(app, 35)
    client = TestClient(app)
    recommendation = client.get("/validation/calibration/recommendations").json()["recommendations"][0]
    payload = _review_payload(recommendation, decision="noted", reviewed_at="2026-04-29T12:00:00+00:00")

    assert client.post("/validation/calibration/review", json=payload).status_code == 200
    assert client.post("/validation/calibration/review", json=payload).status_code == 200
    body = client.get("/validation/calibration/export?deterministic=true").json()

    assert body["snapshot_bundle"]["integrity"]["duplicate_review_ids"] == ["review_000000000002"]


def _seed_validation(
    app,
    count: int,
    *,
    token_id: int = 7,
    issuer: str = "rIssuer7",
    attribution: str = "liquidity_illusion",
) -> None:
    now = datetime(2026, 4, 29, tzinfo=timezone.utc)
    with app.state.container.session_factory() as session:
        for idx in range(count):
            session.add(
                ShadowValidationRecord(
                    decision_id=idx + 1,
                    token_id=token_id,
                    issuer=issuer,
                    predicted_regime="STABLE_SHADOW",
                    disagreement_score=0.35,
                    brier_score=0.30,
                    overconfidence_flag=True,
                    underconfidence_flag=False,
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


def _review_payload(recommendation: dict[str, object], *, decision: str, reviewed_at: str) -> dict[str, object]:
    return {
        "recommendation": recommendation,
        "decision": decision,
        "review_notes": "manual consideration only",
        "reviewer_id": "local-reviewer",
        "reviewed_at": reviewed_at,
    }


def _clear(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(CalibrationReviewRecord))
        session.exec(delete(ShadowValidationRecord))
        session.commit()


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
